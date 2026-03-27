"""API router para alertas de seguridad."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertAcknowledge, AlertList, AlertResponse

router = APIRouter()


@router.get("/", response_model=AlertList)
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    severity: str | None = None,
    alert_type: str | None = None,
    acknowledged: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar alertas con filtros opcionales."""
    query = select(Alert)

    if severity:
        query = query.where(Alert.severity == severity)
    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
    if acknowledged is not None:
        query = query.where(Alert.acknowledged == acknowledged)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return AlertList(total=total, items=items)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener una alerta por su ID."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alert


@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    body: AlertAcknowledge,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marcar una alerta como reconocida."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    alert.acknowledged = body.acknowledged
    alert.acknowledged_at = datetime.now(timezone.utc) if body.acknowledged else None
    db.add(alert)

    return alert
