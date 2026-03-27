"""API router para geolocalización de IPs y exportación CSV."""

import csv
import io
import logging

import httpx
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.event import LogEvent
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Cache simple en memoria para GeoIP (evitar consultas repetidas)
_geo_cache: dict[str, dict] = {}


async def _geolocate_ip(ip: str) -> dict | None:
    """Consulta geolocalización de una IP usando ip-api.com (gratis, sin API key)."""
    if ip in _geo_cache:
        return _geo_cache[ip]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,lat,lon,isp,org")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    result = {
                        "ip": ip,
                        "country": data.get("country", ""),
                        "country_code": data.get("countryCode", ""),
                        "city": data.get("city", ""),
                        "lat": data.get("lat", 0),
                        "lon": data.get("lon", 0),
                        "isp": data.get("isp", ""),
                        "org": data.get("org", ""),
                    }
                    _geo_cache[ip] = result
                    return result
    except Exception:
        logger.debug("Error geolocalizando IP %s", ip)

    return None


@router.get("/map")
async def get_geo_map_data(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtiene datos de geolocalización para las IPs más activas (alertas)."""
    # Top IPs con alertas
    result = await db.execute(
        select(Alert.source_ip, func.count(Alert.id).label("alert_count"))
        .where(Alert.source_ip.isnot(None))
        .group_by(Alert.source_ip)
        .order_by(func.count(Alert.id).desc())
        .limit(limit)
    )
    ip_rows = result.all()

    markers = []
    for ip, alert_count in ip_rows:
        if not ip or ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("127."):
            continue
        geo = await _geolocate_ip(ip)
        if geo:
            geo["alert_count"] = alert_count
            markers.append(geo)

    return {"markers": markers, "total": len(markers)}


@router.get("/ip/{ip}")
async def get_ip_detail(
    ip: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detalle de una IP: geolocalización + estadísticas de eventos y alertas."""
    geo = await _geolocate_ip(ip)

    # Contar eventos de esta IP
    event_count = (await db.execute(
        select(func.count(LogEvent.id)).where(LogEvent.source_ip == ip)
    )).scalar() or 0

    # Contar alertas
    alert_count = (await db.execute(
        select(func.count(Alert.id)).where(Alert.source_ip == ip)
    )).scalar() or 0

    # Tipos de evento
    event_types_result = await db.execute(
        select(LogEvent.event_type, func.count(LogEvent.id))
        .where(LogEvent.source_ip == ip)
        .group_by(LogEvent.event_type)
    )
    event_types = {row[0]: row[1] for row in event_types_result.all()}

    # Alertas por tipo
    alert_types_result = await db.execute(
        select(Alert.alert_type, func.count(Alert.id))
        .where(Alert.source_ip == ip)
        .group_by(Alert.alert_type)
    )
    alert_types = {row[0]: row[1] for row in alert_types_result.all()}

    return {
        "ip": ip,
        "geo": geo,
        "total_events": event_count,
        "total_alerts": alert_count,
        "event_types": event_types,
        "alert_types": alert_types,
    }


@router.get("/export/events")
async def export_events_csv(
    event_type: str | None = None,
    source_ip: str | None = None,
    is_anomaly: bool | None = None,
    limit: int = Query(5000, ge=1, le=50000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exportar eventos a CSV."""
    query = select(LogEvent)
    if event_type:
        query = query.where(LogEvent.event_type == event_type)
    if source_ip:
        query = query.where(LogEvent.source_ip == source_ip)
    if is_anomaly is not None:
        query = query.where(LogEvent.is_anomaly == is_anomaly)

    query = query.order_by(LogEvent.timestamp_utc.desc()).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "event_type", "source_ip", "username", "log_level", "severity_score", "is_anomaly", "message"])

    for e in events:
        writer.writerow([
            e.timestamp_utc.isoformat() if e.timestamp_utc else "",
            e.event_type, e.source_ip or "", e.username or "",
            e.log_level, f"{e.severity_score:.2f}", e.is_anomaly,
            e.message_raw[:200],
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vigia_events.csv"},
    )


@router.get("/export/alerts")
async def export_alerts_csv(
    severity: str | None = None,
    limit: int = Query(5000, ge=1, le=50000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exportar alertas a CSV."""
    query = select(Alert)
    if severity:
        query = query.where(Alert.severity == severity)

    query = query.order_by(Alert.created_at.desc()).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "severity", "alert_type", "source_ip", "description", "acknowledged"])

    for a in alerts:
        writer.writerow([
            a.created_at.isoformat() if a.created_at else "",
            a.severity, a.alert_type, a.source_ip or "",
            a.description[:200], a.acknowledged,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vigia_alerts.csv"},
    )
