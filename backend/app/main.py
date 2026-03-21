"""Entrypoint principal de la aplicación FastAPI."""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, events, reports, stats
from app.api import ml as ml_api
from app.config import settings
from app.core.alert_engine import AlertEngine
from app.core.detector import AnomalyDetector
from app.core.enricher import enrich_event
from app.core.ingester import LogIngester
from app.core.normalizer import normalize_event
from app.core.parser import LogParser
from app.core.sequence_analyzer import SequenceAnalyzer
from app.database import AsyncSessionLocal, engine
from app.ml.predictor import initialize_predictor
from app.models.alert import Alert as AlertModel
from app.models.event import LogEvent
from app.utils.logger import setup_logging
from app.websocket.manager import ws_manager

logger = logging.getLogger(__name__)

# Componentes del pipeline
parser = LogParser()
alert_engine = AlertEngine()
detector = AnomalyDetector()
sequence_analyzer = SequenceAnalyzer()

# Cola async para procesar líneas de log
log_queue: asyncio.Queue = asyncio.Queue()


def on_new_log_line(line: str, filepath: str) -> None:
    """Callback del ingester: encola la línea para procesamiento async."""
    try:
        log_queue.put_nowait((line, filepath))
    except asyncio.QueueFull:
        logger.warning("Cola de logs llena, descartando línea")


async def process_pipeline() -> None:
    """Worker que procesa líneas de log del queue a través del pipeline."""
    while True:
        try:
            line, filepath = await log_queue.get()

            # 1. Parse
            parsed = parser.parse(line, filepath)
            if parsed is None:
                continue

            # 2. Normalize
            normalized = normalize_event(parsed)

            # 3. Enrich (GeoIP, AbuseIPDB)
            enriched = await enrich_event(normalized)

            # 4. Detect anomalías (Isolation Forest)
            is_anomaly, score = detector.predict(enriched)
            enriched["is_anomaly"] = is_anomaly
            enriched["severity_score"] = score

            # 4b. Clasificar tipo de ataque (Random Forest)
            classification = detector.classify_attack(enriched)
            if classification["confidence"] > 0.5:
                enriched.setdefault("message_parsed", {})
                if enriched["message_parsed"] is None:
                    enriched["message_parsed"] = {}
                enriched["message_parsed"]["ml_classification"] = classification

            # 5. Persistir en DB
            async with AsyncSessionLocal() as session:
                event = LogEvent(id=uuid.uuid4(), **enriched)
                session.add(event)
                await session.flush()

                # 6. Evaluar alertas (reglas)
                alert_data = await alert_engine.evaluate(enriched)
                if alert_data:
                    alert = AlertModel(
                        id=uuid.uuid4(),
                        event_id=event.id,
                        **alert_data,
                    )
                    session.add(alert)
                    # Broadcast alerta por WebSocket
                    await ws_manager.broadcast_alert({
                        "id": str(alert.id),
                        "severity": alert.severity,
                        "alert_type": alert.alert_type,
                        "description": alert.description,
                        "source_ip": alert.source_ip,
                    })

                # 6b. Analizar secuencias temporales por IP
                seq_alert = await sequence_analyzer.record_and_analyze(enriched)
                if seq_alert:
                    seq_alert_model = AlertModel(
                        id=uuid.uuid4(),
                        event_id=event.id,
                        severity=seq_alert["severity"],
                        alert_type=seq_alert["alert_type"],
                        description=seq_alert["description"],
                        source_ip=seq_alert.get("source_ip"),
                    )
                    session.add(seq_alert_model)
                    await ws_manager.broadcast_alert({
                        "id": str(seq_alert_model.id),
                        "severity": seq_alert_model.severity,
                        "alert_type": seq_alert_model.alert_type,
                        "description": seq_alert_model.description,
                        "source_ip": seq_alert_model.source_ip,
                    })

                await session.commit()

                # 7. Broadcast evento por WebSocket
                await ws_manager.broadcast_event({
                    "type": "event",
                    "data": {
                        "id": str(event.id),
                        "event_type": event.event_type,
                        "source_ip": event.source_ip,
                        "log_level": event.log_level,
                        "severity_score": event.severity_score,
                        "is_anomaly": event.is_anomaly,
                        "timestamp_utc": event.timestamp_utc.isoformat(),
                    },
                })

        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Error procesando línea de log")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Conectar servicios al iniciar, limpiar al apagar."""
    setup_logging("DEBUG" if settings.DEBUG else "INFO")
    logger.info("Iniciando Log Analyzer AI...")

    # Cargar modelo ML
    initialize_predictor()

    # Conectar Redis (alert engine + sequence analyzer)
    await alert_engine.connect()
    await sequence_analyzer.connect()

    # Iniciar worker del pipeline
    pipeline_task = asyncio.create_task(process_pipeline())

    # Iniciar ingester de logs
    ingester = LogIngester(on_new_log_line)
    try:
        ingester.start()
    except Exception:
        logger.warning("No se pudo iniciar el ingester (logs no accesibles)")

    logger.info("Sistema listo")

    yield

    # Cleanup
    logger.info("Deteniendo servicios...")
    pipeline_task.cancel()
    try:
        await pipeline_task
    except asyncio.CancelledError:
        pass
    try:
        ingester.stop()
    except Exception:
        pass
    await alert_engine.close()
    await sequence_analyzer.close()
    await engine.dispose()


app = FastAPI(
    title="Log Analyzer AI",
    description="Sistema de análisis de logs con IA para detección de anomalías",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(ml_api.router, prefix="/api/ml", tags=["ml"])


@app.get("/")
async def root():
    return {"status": "ok", "project": "Log Analyzer AI"}


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint para streaming de eventos en tiempo real."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Mantener conexión abierta, recibir pings del cliente
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
