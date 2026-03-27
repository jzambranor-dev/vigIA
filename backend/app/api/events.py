"""API router para eventos de log."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.event import LogEvent
from app.models.user import User
from app.schemas.event import LogEventList, LogEventResponse

router = APIRouter()


@router.get("/", response_model=LogEventList)
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    event_type: str | None = None,
    source_ip: str | None = None,
    is_anomaly: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar eventos de log con filtros opcionales."""
    query = select(LogEvent)

    if event_type:
        query = query.where(LogEvent.event_type == event_type)
    if source_ip:
        query = query.where(LogEvent.source_ip == source_ip)
    if is_anomaly is not None:
        query = query.where(LogEvent.is_anomaly == is_anomaly)

    # Total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Resultados paginados
    query = query.order_by(LogEvent.timestamp_utc.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return LogEventList(total=total, items=items)


@router.get("/{event_id}", response_model=LogEventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener un evento por su ID."""
    result = await db.execute(select(LogEvent).where(LogEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return event
