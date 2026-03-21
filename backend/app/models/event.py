"""Modelo SQLAlchemy para eventos de log."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class LogEvent(Base):
    """Tabla log_events: almacena cada línea de log parseada."""

    __tablename__ = "log_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    timestamp_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    log_level: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    source_ip: Mapped[str | None] = mapped_column(String(45), index=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message_raw: Mapped[str] = mapped_column(Text, nullable=False)
    message_parsed: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    severity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_log_events_timestamp_type", "timestamp_utc", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<LogEvent {self.event_type} from {self.source_ip} at {self.timestamp_utc}>"
