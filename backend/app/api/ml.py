"""API router para operaciones de Machine Learning."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import LogEvent
from app.ml.feature_extractor import FEATURE_NAMES, N_FEATURES, extract_features
from app.ml.trainer import train_from_events, _infer_label

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/retrain")
async def retrain_models(
    max_events: int = 5000,
    db: AsyncSession = Depends(get_db),
):
    """Re-entrena los modelos ML con eventos recientes de la base de datos."""
    # Obtener eventos
    result = await db.execute(
        select(LogEvent)
        .order_by(LogEvent.created_at.desc())
        .limit(max_events)
    )
    db_events = result.scalars().all()

    if len(db_events) < 10:
        return {
            "status": "error",
            "message": f"Muy pocos eventos para entrenar: {len(db_events)}. Mínimo 10.",
        }

    # Convertir a dicts para el trainer
    events = []
    for ev in db_events:
        events.append({
            "timestamp_utc": ev.timestamp_utc,
            "source_file": ev.source_file,
            "log_level": ev.log_level,
            "event_type": ev.event_type,
            "source_ip": ev.source_ip,
            "username": ev.username,
            "message_raw": ev.message_raw,
            "message_parsed": ev.message_parsed,
            "severity_score": ev.severity_score,
            "is_anomaly": ev.is_anomaly,
        })

    try:
        results = train_from_events(events)

        # Recargar modelos en el detector activo
        from app.ml.predictor import detector
        detector.load_model()

        return {
            "status": "ok",
            "message": "Modelos re-entrenados exitosamente",
            "events_used": len(events),
            "isolation_forest": results["isolation_forest"],
            "classifier": results["classifier"],
        }
    except Exception as e:
        logger.exception("Error re-entrenando modelos")
        return {"status": "error", "message": str(e)}


@router.get("/status")
async def ml_status():
    """Estado actual de los modelos ML."""
    from app.ml.predictor import detector
    from pathlib import Path

    models_dir = Path(__file__).parent.parent / "ml" / "models"

    iso_path = models_dir / "isolation_forest.pkl"
    clf_path = models_dir / "attack_classifier.pkl"

    return {
        "anomaly_model": {
            "loaded": detector.anomaly_model is not None,
            "file_exists": iso_path.exists(),
            "file_size_kb": round(iso_path.stat().st_size / 1024, 1) if iso_path.exists() else 0,
        },
        "classifier_model": {
            "loaded": detector.classifier_model is not None,
            "file_exists": clf_path.exists(),
            "file_size_kb": round(clf_path.stat().st_size / 1024, 1) if clf_path.exists() else 0,
        },
        "feature_count": N_FEATURES,
        "feature_names": FEATURE_NAMES,
    }


@router.post("/predict")
async def predict_event(event: dict):
    """Predice anomalía y clasifica un evento manualmente (para testing)."""
    from app.ml.predictor import detector

    features = extract_features(event)
    is_anomaly, score = detector.predict(event)
    classification = detector.classify_attack(event)
    inferred_label = _infer_label(event)

    return {
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": float(score),
        "classification": classification,
        "inferred_label": inferred_label,
        "features": {k: float(v) for k, v in zip(FEATURE_NAMES, features)},
    }
