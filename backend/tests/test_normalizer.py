"""Tests para el normalizador de eventos."""

from datetime import datetime, timezone

from app.core.normalizer import normalize_event


class TestNormalizer:

    def test_normalize_complete_event(self):
        parsed = {
            "timestamp_utc": datetime(2026, 3, 20, 10, 30, 0),
            "source_file": "/var/log/auth.log",
            "log_level": "WARNING",
            "event_type": "ssh_login_failed",
            "source_ip": "45.33.32.156",
            "username": "root",
            "message_raw": "Failed password for root",
            "message_parsed": {"host": "server"},
            "severity_score": 0.5,
            "is_anomaly": False,
        }
        result = normalize_event(parsed)
        assert result["timestamp_utc"].tzinfo == timezone.utc
        assert result["source_file"] == "/var/log/auth.log"
        assert result["log_level"] == "WARNING"
        assert result["event_type"] == "ssh_login_failed"
        assert result["source_ip"] == "45.33.32.156"
        assert result["severity_score"] == 0.5
        assert result["is_anomaly"] is False

    def test_normalize_missing_fields_defaults(self):
        parsed = {"timestamp_utc": datetime(2026, 1, 1, tzinfo=timezone.utc)}
        result = normalize_event(parsed)
        assert result["source_file"] == "unknown"
        assert result["log_level"] == "INFO"
        assert result["event_type"] == "unknown"
        assert result["source_ip"] is None
        assert result["username"] is None
        assert result["message_raw"] == ""
        assert result["severity_score"] == 0.0
        assert result["is_anomaly"] is False

    def test_normalize_adds_utc_to_naive_datetime(self):
        parsed = {"timestamp_utc": datetime(2026, 6, 15, 12, 0, 0)}
        result = normalize_event(parsed)
        assert result["timestamp_utc"].tzinfo == timezone.utc

    def test_normalize_preserves_aware_datetime(self):
        ts = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        parsed = {"timestamp_utc": ts}
        result = normalize_event(parsed)
        assert result["timestamp_utc"] is ts
