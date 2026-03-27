"""API router para estadísticas y resumen."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.event import LogEvent
from app.models.user import User

router = APIRouter()


@router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resumen general del sistema."""
    total_events = (
        await db.execute(select(func.count(LogEvent.id)))
    ).scalar() or 0

    total_anomalies = (
        await db.execute(
            select(func.count(LogEvent.id)).where(LogEvent.is_anomaly.is_(True))
        )
    ).scalar() or 0

    total_alerts = (
        await db.execute(select(func.count(Alert.id)))
    ).scalar() or 0

    unacknowledged_alerts = (
        await db.execute(
            select(func.count(Alert.id)).where(Alert.acknowledged.is_(False))
        )
    ).scalar() or 0

    # Eventos por tipo
    events_by_type_result = await db.execute(
        select(LogEvent.event_type, func.count(LogEvent.id))
        .group_by(LogEvent.event_type)
        .order_by(func.count(LogEvent.id).desc())
        .limit(10)
    )
    events_by_type = {row[0]: row[1] for row in events_by_type_result.all()}

    # Alertas por severidad
    alerts_by_severity_result = await db.execute(
        select(Alert.severity, func.count(Alert.id))
        .group_by(Alert.severity)
    )
    alerts_by_severity = {row[0]: row[1] for row in alerts_by_severity_result.all()}

    return {
        "total_events": total_events,
        "total_anomalies": total_anomalies,
        "total_alerts": total_alerts,
        "unacknowledged_alerts": unacknowledged_alerts,
        "events_by_type": events_by_type,
        "alerts_by_severity": alerts_by_severity,
    }
