"""Tests para el detector de anomalías."""

from app.core.detector import AnomalyDetector


class TestAnomalyDetector:
    """Tests del detector basado en reglas (sin modelo ML)."""

    def setup_method(self):
        self.detector = AnomalyDetector()

    def test_detect_ssh_failed_anomaly(self):
        event = {
            "event_type": "ssh_login_failed",
            "severity_score": 0.5,
            "source_ip": "45.33.32.156",
            "message_parsed": {},
        }
        is_anomaly, score = self.detector.predict(event)
        assert is_anomaly is True
        assert score >= 0.4

    def test_normal_event_not_anomaly(self):
        event = {
            "event_type": "ssh_login_accepted",
            "severity_score": 0.1,
            "source_ip": "192.168.1.10",
            "message_parsed": {},
        }
        is_anomaly, score = self.detector.predict(event)
        assert is_anomaly is False

    def test_apache_500_is_anomaly(self):
        event = {
            "event_type": "apache_access",
            "severity_score": 0.5,
            "source_ip": "10.0.0.1",
            "message_parsed": {"status": 500},
        }
        is_anomaly, score = self.detector.predict(event)
        assert is_anomaly is True
        assert score >= 0.5

    def test_apache_200_not_anomaly(self):
        event = {
            "event_type": "apache_access",
            "severity_score": 0.0,
            "source_ip": "192.168.1.10",
            "message_parsed": {"status": 200},
        }
        is_anomaly, score = self.detector.predict(event)
        assert is_anomaly is False
