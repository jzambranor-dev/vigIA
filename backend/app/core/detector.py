"""Detector de anomalías con Isolation Forest y motor de reglas."""

import logging
from pathlib import Path

import joblib
import numpy as np

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "ml" / "models"


class AnomalyDetector:
    """Combina Isolation Forest con reglas heurísticas para detección."""

    def __init__(self):
        self.model = None

    def load_model(self, model_name: str = "isolation_forest.pkl") -> bool:
        """Carga un modelo entrenado desde disco."""
        model_path = MODELS_DIR / model_name
        if model_path.exists():
            self.model = joblib.load(model_path)
            logger.info(f"Modelo cargado: {model_path}")
            return True
        logger.warning(f"Modelo no encontrado: {model_path}")
        return False

    def predict(self, event: dict) -> tuple[bool, float]:
        """Predice si un evento es anomalía. Retorna (is_anomaly, score)."""
        features = self._extract_features(event)

        # Si hay modelo ML, usarlo
        if self.model is not None:
            try:
                features_array = np.array([features])
                prediction = self.model.predict(features_array)
                score = self.model.decision_function(features_array)
                is_anomaly = prediction[0] == -1
                # Normalizar score a 0-1
                normalized_score = max(0.0, min(1.0, 0.5 - score[0] / 2))
                return is_anomaly, normalized_score
            except Exception:
                logger.exception("Error en predicción ML")

        # Fallback: reglas heurísticas
        return self._rule_based_detection(event)

    def _extract_features(self, event: dict) -> list[float]:
        """Extrae features numéricas de un evento para el modelo ML."""
        parsed = event.get("message_parsed") or {}
        return [
            event.get("severity_score", 0.0),
            1.0 if event.get("event_type") in ("ssh_login_failed", "ssh_invalid_user") else 0.0,
            1.0 if event.get("log_level") in ("ERROR", "CRITICAL") else 0.0,
            float(parsed.get("status", 200)) / 600.0 if "status" in parsed else 0.0,
            1.0 if event.get("source_ip") else 0.0,
        ]

    def _rule_based_detection(self, event: dict) -> tuple[bool, float]:
        """Detección basada en reglas cuando no hay modelo ML."""
        score = event.get("severity_score", 0.0)
        event_type = event.get("event_type", "")

        # Eventos de alta severidad
        if event_type in ("ssh_login_failed", "ssh_invalid_user") and score >= 0.4:
            return True, score

        if event_type == "apache_access":
            parsed = event.get("message_parsed") or {}
            status = parsed.get("status", 200)
            if status >= 500:
                return True, max(score, 0.6)

        return False, score
