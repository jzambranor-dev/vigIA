"""Tests para schemas Pydantic."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.alert import AlertBase, AlertCreate, AlertList, AlertResponse
from app.schemas.event import LogEventBase, LogEventCreate, LogEventList, LogEventResponse


class TestLogEventSchemas:

    def test_event_base_valid(self):
        event = LogEventBase(
            timestamp_utc=datetime.now(timezone.utc),
            source_file="/var/log/auth.log",
            event_type="ssh_login_failed",
            message_raw="Failed password for root",
        )
        assert event.log_level == "INFO"
        assert event.severity_score == 0.0
        assert event.is_anomaly is False

    def test_event_base_severity_bounds(self):
        with pytest.raises(ValidationError):
            LogEventBase(
                timestamp_utc=datetime.now(timezone.utc),
                source_file="test",
                event_type="test",
                message_raw="test",
                severity_score=1.5,
            )

    def test_event_create_inherits(self):
        event = LogEventCreate(
            timestamp_utc=datetime.now(timezone.utc),
            source_file="test",
            event_type="test",
            message_raw="msg",
        )
        assert isinstance(event, LogEventBase)

    def test_event_response(self):
        resp = LogEventResponse(
            id=uuid4(),
            timestamp_utc=datetime.now(timezone.utc),
            source_file="test",
            event_type="test",
            message_raw="msg",
            created_at=datetime.now(timezone.utc),
        )
        assert resp.id is not None

    def test_event_list(self):
        lst = LogEventList(total=0, items=[])
        assert lst.total == 0
        assert lst.items == []


class TestAlertSchemas:

    def test_alert_base_valid(self):
        alert = AlertBase(
            event_id=uuid4(),
            severity="HIGH",
            alert_type="brute_force_ssh",
            description="Test alert",
        )
        assert alert.source_ip is None

    def test_alert_create_inherits(self):
        alert = AlertCreate(
            event_id=uuid4(),
            severity="CRITICAL",
            alert_type="sql_injection",
            description="SQL injection detected",
            source_ip="10.0.0.1",
        )
        assert isinstance(alert, AlertBase)
        assert alert.source_ip == "10.0.0.1"

    def test_alert_response(self):
        resp = AlertResponse(
            id=uuid4(),
            event_id=uuid4(),
            severity="MEDIUM",
            alert_type="sudo_root",
            description="Sudo to root",
            created_at=datetime.now(timezone.utc),
        )
        assert resp.acknowledged is False
        assert resp.acknowledged_at is None

    def test_alert_list(self):
        lst = AlertList(total=0, items=[])
        assert lst.total == 0
