"""Motor de alertas basado en reglas con contadores Redis."""

import logging
import re
from datetime import datetime, timezone

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

# Patrones de ataque
SQL_INJECTION_PATTERNS = re.compile(
    r"(union\s+select|or\s+1\s*=\s*1|drop\s+table|insert\s+into|"
    r"select\s+.*\s+from|;\s*delete\s+from|'\s*or\s*'|--\s*$|/\*.*\*/)",
    re.IGNORECASE,
)

DIRECTORY_TRAVERSAL_PATTERNS = re.compile(
    r"(\.\./|\.\.%2[fF]|etc/passwd|etc/shadow|proc/self)", re.IGNORECASE
)


class AlertEngine:
    """Evalúa eventos contra reglas de seguridad usando Redis para contadores."""

    def __init__(self):
        self.redis_client: redis.Redis | None = None

    async def connect(self) -> None:
        """Conectar al servidor Redis."""
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def close(self) -> None:
        """Cerrar conexión Redis."""
        if self.redis_client:
            await self.redis_client.close()

    async def _increment_counter(self, key: str, window_seconds: int = 60) -> int:
        """Incrementa un contador con TTL en Redis."""
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()
        return results[0]

    async def evaluate(self, event: dict) -> dict | None:
        """Evalúa un evento y retorna una alerta si corresponde, o None."""
        event_type = event.get("event_type", "")
        source_ip = event.get("source_ip", "")
        parsed = event.get("message_parsed") or {}

        # BRUTE FORCE SSH
        if event_type == "ssh_login_failed" and source_ip:
            key = f"brute_ssh:{source_ip}"
            count = await self._increment_counter(key, window_seconds=60)

            if count >= 20:
                return self._create_alert(
                    event, "CRITICAL", "brute_force_ssh",
                    f"Fuerza bruta SSH crítica: {count} intentos fallidos desde {source_ip} en 60s",
                )
            elif count >= 5:
                return self._create_alert(
                    event, "HIGH", "brute_force_ssh",
                    f"Fuerza bruta SSH detectada: {count} intentos fallidos desde {source_ip} en 60s",
                )

        # BRUTE FORCE WEB (401/403)
        if event_type == "apache_access" and source_ip:
            status = parsed.get("status", 0)
            if status in (401, 403):
                key = f"brute_web:{source_ip}"
                count = await self._increment_counter(key, window_seconds=60)

                if count >= 10:
                    return self._create_alert(
                        event, "HIGH", "brute_force_web",
                        f"Fuerza bruta web: {count} respuestas {status} desde {source_ip} en 60s",
                    )

        # DIRECTORY TRAVERSAL
        if event_type == "apache_access":
            url = parsed.get("url", "")
            if DIRECTORY_TRAVERSAL_PATTERNS.search(url):
                return self._create_alert(
                    event, "CRITICAL", "directory_traversal",
                    f"Directory traversal detectado desde {source_ip}: {url}",
                )

        # SQL INJECTION
        if event_type == "apache_access":
            url = parsed.get("url", "")
            if SQL_INJECTION_PATTERNS.search(url):
                return self._create_alert(
                    event, "CRITICAL", "sql_injection",
                    f"SQL injection detectado desde {source_ip}: {url}",
                )

        # SUDO A ROOT por usuario no habitual
        if event_type == "sudo_command":
            target_user = parsed.get("target_user", "")
            if target_user == "root":
                return self._create_alert(
                    event, "MEDIUM", "sudo_root",
                    f"Comando sudo a root por usuario {event.get('username')}: {parsed.get('command')}",
                )

        return None

    def _create_alert(
        self, event: dict, severity: str, alert_type: str, description: str
    ) -> dict:
        """Crea un dict de alerta."""
        return {
            "severity": severity,
            "alert_type": alert_type,
            "description": description,
            "source_ip": event.get("source_ip"),
            "created_at": datetime.now(timezone.utc),
        }
