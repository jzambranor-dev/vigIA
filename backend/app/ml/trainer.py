"""Entrenamiento del modelo Isolation Forest."""

import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent / "models"


def train_isolation_forest(
    features: np.ndarray,
    contamination: float = 0.1,
    n_estimators: int = 100,
    model_name: str = "isolation_forest.pkl",
) -> IsolationForest:
    """Entrena un modelo Isolation Forest y lo serializa."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(features)

    model_path = MODELS_DIR / model_name
    joblib.dump(model, model_path)
    logger.info(f"Modelo guardado en {model_path}")

    return model
