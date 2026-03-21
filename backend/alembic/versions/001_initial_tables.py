"""Crear tablas log_events y alerts.

Revision ID: 001_initial
Revises: None
Create Date: 2026-03-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "log_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("timestamp_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_file", sa.String(255), nullable=False),
        sa.Column("log_level", sa.String(20), nullable=False, server_default="INFO"),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("source_ip", sa.String(45), nullable=True),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("message_raw", sa.Text, nullable=False),
        sa.Column("message_parsed", JSON, nullable=True),
        sa.Column("severity_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("is_anomaly", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_log_events_timestamp_utc", "log_events", ["timestamp_utc"])
    op.create_index("ix_log_events_event_type", "log_events", ["event_type"])
    op.create_index("ix_log_events_source_ip", "log_events", ["source_ip"])
    op.create_index("ix_log_events_timestamp_type", "log_events", ["timestamp_utc", "event_type"])

    op.create_table(
        "alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", UUID(as_uuid=True), sa.ForeignKey("log_events.id"), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("source_ip", sa.String(45), nullable=True),
        sa.Column("acknowledged", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_alerts_event_id", "alerts", ["event_id"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("log_events")
