"""Schemas Pydantic para eventos de log."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LogEventBase(BaseModel):
    """Campos comunes de un evento de log."""

    timestamp_utc: datetime
    source_file: str
    log_level: str = "INFO"
    event_type: str
    source_ip: str | None = None
    username: str | None = None
    message_raw: str
    message_parsed: dict | None = None
    severity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_anomaly: bool = False


class LogEventCreate(LogEventBase):
    """Schema para crear un evento."""

    pass


class LogEventResponse(LogEventBase):
    """Schema de respuesta con campos generados."""

    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class LogEventList(BaseModel):
    """Lista paginada de eventos."""

    total: int
    items: list[LogEventResponse]
