"""Normaliza eventos parseados a un schema JSON unificado."""

from datetime import datetime, timezone


def normalize_event(parsed: dict) -> dict:
    """Normaliza un dict parseado al schema LogEvent unificado."""
    timestamp = parsed.get("timestamp_utc")
    if isinstance(timestamp, datetime) and timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return {
        "timestamp_utc": timestamp,
        "source_file": parsed.get("source_file", "unknown"),
        "log_level": parsed.get("log_level", "INFO"),
        "event_type": parsed.get("event_type", "unknown"),
        "source_ip": parsed.get("source_ip"),
        "username": parsed.get("username"),
        "message_raw": parsed.get("message_raw", ""),
        "message_parsed": parsed.get("message_parsed"),
        "severity_score": float(parsed.get("severity_score", 0.0)),
        "is_anomaly": bool(parsed.get("is_anomaly", False)),
    }
