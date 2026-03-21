"""Análisis de secuencias temporales por IP para detectar ataques multi-paso."""

import logging
from datetime import datetime, timezone

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

# Patrones de ataque multi-paso conocidos
ATTACK_SEQUENCES = {
    "recon_to_bruteforce": {
        "description": "Reconocimiento seguido de fuerza bruta",
        "steps": ["scan", "brute_force"],
        "window_seconds": 300,
        "severity": "CRITICAL",
    },
    "bruteforce_to_access": {
        "description": "Fuerza bruta exitosa (posible compromiso)",
        "steps": ["brute_force", "login_success"],
        "window_seconds": 600,
        "severity": "CRITICAL",
    },
    "traversal_then_injection": {
        "description": "Directory traversal seguido de SQL injection",
        "steps": ["directory_traversal", "sql_injection"],
        "window_seconds": 300,
        "severity": "CRITICAL",
    },
}

# Mapeo de event_type a categoría de secuencia
EVENT_TO_CATEGORY = {
    "ssh_login_failed": "brute_force",
    "ssh_invalid_user": "scan",
    "ssh_login_accepted": "login_success",
    "sudo_command": "privilege_escalation",
}


class SequenceAnalyzer:
    """Analiza secuencias de eventos por IP para detectar ataques multi-paso."""

    def __init__(self):
        self.redis_client: redis.Redis | None = None

    async def connect(self) -> None:
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def close(self) -> None:
        if self.redis_client:
            await self.redis_client.close()

    async def record_and_analyze(self, event: dict) -> dict | None:
        """Registra un evento en la secuencia de su IP y busca patrones.

        Returns:
            dict con alerta de secuencia si se detecta patrón, o None
        """
        if not self.redis_client:
            return None

        source_ip = event.get("source_ip")
        if not source_ip:
            return None

        event_type = event.get("event_type", "")
        parsed = event.get("message_parsed") or {}

        # Determinar categoría
        category = EVENT_TO_CATEGORY.get(event_type)
        if not category and event_type == "apache_access":
            url = parsed.get("url", "")
            status = parsed.get("status", 200)
            if any(p in url.lower() for p in ["../", "etc/passwd"]):
                category = "directory_traversal"
            elif any(p in url.lower() for p in ["union select", "or 1=1", "drop table"]):
                category = "sql_injection"
            elif status in (401, 403):
                category = "brute_force"
            elif status == 404:
                category = "scan"

        if not category:
            return None

        # Registrar en Redis con timestamp
        key = f"seq:{source_ip}"
        now = datetime.now(timezone.utc).timestamp()
        entry = f"{category}:{now}"

        pipe = self.redis_client.pipeline()
        pipe.rpush(key, entry)
        pipe.expire(key, 600)  # ventana máxima: 10 min
        await pipe.execute()

        # Obtener secuencia completa
        sequence_raw = await self.redis_client.lrange(key, 0, -1)
        sequence = []
        for item in sequence_raw:
            parts = item.split(":", 1)
            if len(parts) == 2:
                sequence.append({"category": parts[0], "timestamp": float(parts[1])})

        # Buscar patrones
        return self._match_patterns(source_ip, sequence)

    def _match_patterns(self, source_ip: str, sequence: list[dict]) -> dict | None:
        """Busca patrones de ataque multi-paso en la secuencia."""
        if len(sequence) < 2:
            return None

        categories = [s["category"] for s in sequence]
        timestamps = [s["timestamp"] for s in sequence]

        for pattern_name, pattern in ATTACK_SEQUENCES.items():
            steps = pattern["steps"]
            window = pattern["window_seconds"]

            # Buscar la subsecuencia
            step_idx = 0
            first_ts = None
            for i, cat in enumerate(categories):
                if cat == steps[step_idx]:
                    if step_idx == 0:
                        first_ts = timestamps[i]
                    step_idx += 1
                    if step_idx == len(steps):
                        # Verificar ventana temporal
                        if timestamps[i] - first_ts <= window:
                            return {
                                "severity": pattern["severity"],
                                "alert_type": f"sequence_{pattern_name}",
                                "description": (
                                    f"Ataque multi-paso detectado desde {source_ip}: "
                                    f"{pattern['description']}. "
                                    f"Secuencia: {' → '.join(steps)}"
                                ),
                                "source_ip": source_ip,
                                "pattern": pattern_name,
                                "steps_detected": steps,
                            }
                        # Reset si se pasó la ventana
                        step_idx = 0
                        first_ts = None

        return None
