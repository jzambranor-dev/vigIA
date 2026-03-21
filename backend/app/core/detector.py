"""Detector de anomalías con Isolation Forest, clasificador de ataques y reglas."""

import logging
from pathlib import Path

import joblib
import numpy as np

from app.ml.feature_extractor import extract_features

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "ml" / "models"


class AnomalyDetector:
    """Combina Isolation Forest + clasificador de ataques + reglas heurísticas."""

    def __init__(self):
        self.anomaly_model = None    # Isolation Forest
        self.classifier_model = None  # Random Forest classifier
        self.label_encoder = None     # Label encoder para tipos de ataque

    def load_model(self, model_name: str = "isolation_forest.pkl") -> bool:
        """Carga el modelo de anomalías desde disco."""
        model_path = MODELS_DIR / model_name
        if model_path.exists():
            self.anomaly_model = joblib.load(model_path)
            logger.info(f"Modelo anomalías cargado: {model_path}")
        else:
            logger.warning(f"Modelo anomalías no encontrado: {model_path}")

        # Intentar cargar clasificador
        classifier_path = MODELS_DIR / "attack_classifier.pkl"
        encoder_path = MODELS_DIR / "label_encoder.pkl"
        if classifier_path.exists() and encoder_path.exists():
            self.classifier_model = joblib.load(classifier_path)
            self.label_encoder = joblib.load(encoder_path)
            logger.info(f"Clasificador de ataques cargado: {classifier_path}")

        return self.anomaly_model is not None

    def predict(self, event: dict) -> tuple[bool, float]:
        """Predice si un evento es anomalía. Retorna (is_anomaly, score)."""
        features = extract_features(event)

        # Si hay modelo ML, usarlo
        if self.anomaly_model is not None:
            try:
                features_array = np.array([features])
                prediction = self.anomaly_model.predict(features_array)
                score = self.anomaly_model.decision_function(features_array)
                is_anomaly = prediction[0] == -1
                # Normalizar score a 0-1
                normalized_score = max(0.0, min(1.0, 0.5 - score[0] / 2))
                return is_anomaly, normalized_score
            except Exception:
                logger.exception("Error en predicción ML anomalías")

        # Fallback: reglas heurísticas
        return self._rule_based_detection(event)

    def classify_attack(self, event: dict) -> dict:
        """Clasifica el tipo de ataque usando el modelo supervisado.

        Retorna:
            {"attack_type": str, "confidence": float, "probabilities": dict}
        """
        if self.classifier_model is None or self.label_encoder is None:
            return {"attack_type": "unknown", "confidence": 0.0, "probabilities": {}}

        try:
            features = extract_features(event)
            features_array = np.array([features])
            prediction = self.classifier_model.predict(features_array)
            probabilities = self.classifier_model.predict_proba(features_array)[0]

            attack_type = self.label_encoder.inverse_transform(prediction)[0]
            confidence = float(max(probabilities))

            prob_dict = {
                self.label_encoder.inverse_transform([i])[0]: float(p)
                for i, p in enumerate(probabilities)
                if p > 0.01
            }

            return {
                "attack_type": attack_type,
                "confidence": confidence,
                "probabilities": prob_dict,
            }
        except Exception:
            logger.exception("Error en clasificación de ataque")
            return {"attack_type": "unknown", "confidence": 0.0, "probabilities": {}}

    def _rule_based_detection(self, event: dict) -> tuple[bool, float]:
        """Detección basada en reglas cuando no hay modelo ML."""
        score = event.get("severity_score", 0.0)
        event_type = event.get("event_type", "")

        if event_type in ("ssh_login_failed", "ssh_invalid_user") and score >= 0.4:
            return True, score

        if event_type == "apache_access":
            parsed = event.get("message_parsed") or {}
            status = parsed.get("status", 200)
            if status >= 500:
                return True, max(score, 0.6)

        return False, score
