"""Tests para el entrenador de modelos ML."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np

from app.ml.trainer import train_isolation_forest


class TestTrainer:

    def test_train_isolation_forest(self):
        """Entrena un modelo y verifica que se guarda."""
        features = np.random.rand(100, 5)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.ml.trainer.MODELS_DIR", Path(tmpdir)):
                model = train_isolation_forest(
                    features, contamination=0.1, n_estimators=10, model_name="test.pkl"
                )
                assert (Path(tmpdir) / "test.pkl").exists()
                predictions = model.predict(features)
                assert len(predictions) == 100
                assert set(predictions).issubset({-1, 1})

    def test_train_creates_directory(self):
        """Verifica que crea el directorio si no existe."""
        features = np.random.rand(50, 3)
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "sub" / "models"
            with patch("app.ml.trainer.MODELS_DIR", subdir):
                model = train_isolation_forest(features, n_estimators=5)
                assert subdir.exists()
