"""Enriquecimiento de eventos con GeoIP y AbuseIPDB."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def enrich_event(event: dict) -> dict:
    """Enriquece un evento con información de IP externa."""
    source_ip = event.get("source_ip")
    if not source_ip or _is_private_ip(source_ip):
        return event

    enrichment = {}

    # AbuseIPDB (si hay API key)
    if settings.ABUSEIPDB_API_KEY:
        try:
            abuse_data = await _check_abuseipdb(source_ip)
            if abuse_data:
                enrichment["abuseipdb"] = abuse_data
        except Exception:
            logger.exception(f"Error consultando AbuseIPDB para {source_ip}")

    if enrichment:
        parsed = event.get("message_parsed") or {}
        parsed["enrichment"] = enrichment
        event["message_parsed"] = parsed

    return event


def _is_private_ip(ip: str) -> bool:
    """Verifica si una IP es privada (RFC 1918)."""
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    first, second = int(parts[0]), int(parts[1])
    return (
        first == 10
        or (first == 172 and 16 <= second <= 31)
        or (first == 192 and second == 168)
        or first == 127
    )


async def _check_abuseipdb(ip: str) -> dict | None:
    """Consulta la API de AbuseIPDB para una IP."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            "https://api.abuseipdb.com/api/v2/check",
            params={"ipAddress": ip, "maxAgeInDays": 90},
            headers={
                "Key": settings.ABUSEIPDB_API_KEY,
                "Accept": "application/json",
            },
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            return {
                "abuse_confidence_score": data.get("abuseConfidenceScore", 0),
                "country_code": data.get("countryCode", ""),
                "isp": data.get("isp", ""),
                "total_reports": data.get("totalReports", 0),
            }
    return None
