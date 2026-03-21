"""Tests para el módulo predictor."""

import pytest
from unittest.mock import patch

from app.ml.predictor import predict_anomaly, initialize_predictor


class TestPredictor:

    def test_initialize_no_model(self):
        with patch("app.ml.predictor.detector") as mock_det:
            mock_det.load_model.return_value = False
            result = initialize_predictor()
            assert result is False

    def test_initialize_with_model(self):
        with patch("app.ml.predictor.detector") as mock_det:
            mock_det.load_model.return_value = True
            result = initialize_predictor()
            assert result is True

    @pytest.mark.asyncio
    async def test_predict_anomaly_updates_event(self):
        event = {
            "event_type": "ssh_login_failed",
            "severity_score": 0.5,
            "source_ip": "1.2.3.4",
            "message_parsed": {},
        }
        with patch("app.ml.predictor.detector") as mock_det:
            mock_det.predict.return_value = (True, 0.8)
            result = await predict_anomaly(event)
            assert result["is_anomaly"] is True
            assert result["severity_score"] == 0.8
