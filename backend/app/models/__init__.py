"""Modelos SQLAlchemy del proyecto."""

from app.models.alert import Alert
from app.models.event import LogEvent

__all__ = ["LogEvent", "Alert"]
