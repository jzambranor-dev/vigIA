"""Inferencia en tiempo real usando modelos entrenados."""

import logging

from app.core.detector import AnomalyDetector

logger = logging.getLogger(__name__)

# Instancia global del detector
detector = AnomalyDetector()


def initialize_predictor() -> bool:
    """Carga los modelos al iniciar la aplicación."""
    loaded = detector.load_model()
    if not loaded:
        logger.warning("Sin modelo ML de anomalías, usando detección por reglas")
    if detector.classifier_model is not None:
        logger.info("Clasificador de ataques disponible")
    else:
        logger.warning("Sin clasificador de ataques")
    return loaded


async def predict_anomaly(event: dict) -> dict:
    """Predice si un evento es anomalía y actualiza el dict."""
    is_anomaly, score = detector.predict(event)
    event["is_anomaly"] = is_anomaly
    event["severity_score"] = score
    return event
