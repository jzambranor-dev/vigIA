"""Schemas Pydantic para alertas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AlertBase(BaseModel):
    """Campos comunes de una alerta."""

    event_id: UUID
    severity: str
    alert_type: str
    description: str
    source_ip: str | None = None


class AlertCreate(AlertBase):
    """Schema para crear una alerta."""

    pass


class AlertResponse(AlertBase):
    """Schema de respuesta con campos generados."""

    id: UUID
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertList(BaseModel):
    """Lista paginada de alertas."""

    total: int
    items: list[AlertResponse]


class AlertAcknowledge(BaseModel):
    """Schema para marcar alerta como reconocida."""

    acknowledged: bool = True
