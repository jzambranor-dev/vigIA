#!/usr/bin/env python3
"""Inserta datos iniciales en la base de datos para demo."""

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import AsyncSessionLocal, engine, Base
from app.models.event import LogEvent
from app.models.alert import Alert


async def seed():
    """Crea tablas e inserta datos de ejemplo."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Eventos de ejemplo
        events = [
            LogEvent(
                id=uuid.uuid4(),
                timestamp_utc=datetime(2026, 3, 20, 10, 30, 0, tzinfo=timezone.utc),
                source_file="/var/log/auth.log",
                log_level="WARNING",
                event_type="ssh_login_failed",
                source_ip="45.33.32.156",
                username="root",
                message_raw="Mar 20 10:30:00 server sshd[1234]: Failed password for root from 45.33.32.156 port 54321 ssh2",
                severity_score=0.7,
                is_anomaly=True,
            ),
            LogEvent(
                id=uuid.uuid4(),
                timestamp_utc=datetime(2026, 3, 20, 11, 0, 0, tzinfo=timezone.utc),
                source_file="/var/log/apache2/access.log",
                log_level="ERROR",
                event_type="apache_access",
                source_ip="185.220.101.34",
                message_raw='185.220.101.34 - - [20/Mar/2026:11:00:00 +0000] "GET /../../etc/passwd HTTP/1.1" 403 287',
                message_parsed={"method": "GET", "url": "/../../etc/passwd", "status": 403},
                severity_score=0.9,
                is_anomaly=True,
            ),
            LogEvent(
                id=uuid.uuid4(),
                timestamp_utc=datetime(2026, 3, 20, 9, 0, 0, tzinfo=timezone.utc),
                source_file="/var/log/auth.log",
                log_level="INFO",
                event_type="ssh_login_accepted",
                source_ip="192.168.1.10",
                username="jzambrano",
                message_raw="Mar 20 09:00:00 server sshd[5678]: Accepted password for jzambrano from 192.168.1.10 port 45000 ssh2",
                severity_score=0.1,
                is_anomaly=False,
            ),
        ]

        for event in events:
            session.add(event)
        await session.flush()

        # Alertas de ejemplo
        alerts = [
            Alert(
                id=uuid.uuid4(),
                event_id=events[0].id,
                severity="HIGH",
                alert_type="brute_force_ssh",
                description="Fuerza bruta SSH detectada: 15 intentos fallidos desde 45.33.32.156 en 60s",
                source_ip="45.33.32.156",
            ),
            Alert(
                id=uuid.uuid4(),
                event_id=events[1].id,
                severity="CRITICAL",
                alert_type="directory_traversal",
                description="Directory traversal detectado desde 185.220.101.34: /../../etc/passwd",
                source_ip="185.220.101.34",
            ),
        ]

        for alert in alerts:
            session.add(alert)

        await session.commit()
        print(f"Seed completado: {len(events)} eventos, {len(alerts)} alertas")


if __name__ == "__main__":
    asyncio.run(seed())
