"""WebSocket manager para streaming de eventos en tiempo real."""

import json
import logging
from datetime import datetime

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Gestiona conexiones WebSocket activas."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Acepta una nueva conexión WebSocket."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket conectado. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remueve una conexión WebSocket."""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket desconectado. Total: {len(self.active_connections)}")

    async def broadcast_event(self, event: dict) -> None:
        """Envía un evento a todos los clientes conectados."""
        if not self.active_connections:
            return

        # Serializar datetimes
        message = json.dumps(event, default=_json_serializer)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.active_connections.remove(conn)

    async def broadcast_alert(self, alert: dict) -> None:
        """Envía una alerta a todos los clientes conectados."""
        payload = {"type": "alert", "data": alert}
        await self.broadcast_event(payload)


def _json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Tipo no serializable: {type(obj)}")


# Singleton
ws_manager = ConnectionManager()
