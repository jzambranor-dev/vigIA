"""Tests para el detector con features y reglas adicionales."""

from app.core.detector import AnomalyDetector


class TestFeatureExtraction:

    def setup_method(self):
        self.detector = AnomalyDetector()

    def test_extract_features_ssh_failed(self):
        event = {
            "severity_score": 0.5,
            "event_type": "ssh_login_failed",
            "log_level": "WARNING",
            "source_ip": "10.0.0.1",
            "message_parsed": {},
        }
        features = self.detector._extract_features(event)
        assert len(features) == 5
        assert features[0] == 0.5   # severity
        assert features[1] == 1.0   # is ssh_failed
        assert features[4] == 1.0   # has IP

    def test_extract_features_normal(self):
        event = {
            "severity_score": 0.1,
            "event_type": "ssh_login_accepted",
            "log_level": "INFO",
            "source_ip": None,
            "message_parsed": {"status": 200},
        }
        features = self.detector._extract_features(event)
        assert features[0] == 0.1
        assert features[1] == 0.0   # not ssh_failed
        assert features[2] == 0.0   # not error
        assert features[4] == 0.0   # no IP

    def test_extract_features_apache_500(self):
        event = {
            "severity_score": 0.6,
            "event_type": "apache_access",
            "log_level": "ERROR",
            "source_ip": "1.2.3.4",
            "message_parsed": {"status": 500},
        }
        features = self.detector._extract_features(event)
        assert features[2] == 1.0   # is error level
        assert abs(features[3] - 500 / 600) < 0.01  # status normalized

    def test_rule_based_syslog_not_anomaly(self):
        event = {
            "event_type": "syslog",
            "severity_score": 0.0,
            "message_parsed": {},
        }
        is_anomaly, score = self.detector._rule_based_detection(event)
        assert is_anomaly is False

    def test_rule_based_apache_200_not_anomaly(self):
        event = {
            "event_type": "apache_access",
            "severity_score": 0.0,
            "message_parsed": {"status": 200},
        }
        is_anomaly, score = self.detector._rule_based_detection(event)
        assert is_anomaly is False

    def test_load_model_nonexistent(self):
        detector = AnomalyDetector()
        loaded = detector.load_model("nonexistent.pkl")
        assert loaded is False
        assert detector.model is None
