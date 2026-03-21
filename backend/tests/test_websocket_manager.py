"""Tests para el WebSocket connection manager."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.websocket.manager import ConnectionManager, _json_serializer


class TestJsonSerializer:

    def test_serialize_datetime(self):
        dt = datetime(2026, 3, 20, 10, 30, 0)
        result = _json_serializer(dt)
        assert result == "2026-03-20T10:30:00"

    def test_serialize_unknown_raises(self):
        with pytest.raises(TypeError):
            _json_serializer(set())


class TestConnectionManager:

    @pytest.mark.asyncio
    async def test_connect(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws)
        assert len(manager.active_connections) == 1
        ws.accept.assert_called_once()

    def test_disconnect(self):
        manager = ConnectionManager()
        ws = MagicMock()
        manager.active_connections.append(ws)
        manager.disconnect(ws)
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_event_no_connections(self):
        manager = ConnectionManager()
        await manager.broadcast_event({"type": "test"})
        # No error when no connections

    @pytest.mark.asyncio
    async def test_broadcast_event_sends_to_all(self):
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.active_connections = [ws1, ws2]
        await manager.broadcast_event({"type": "test", "data": "hello"})
        assert ws1.send_text.called
        assert ws2.send_text.called

    @pytest.mark.asyncio
    async def test_broadcast_removes_failed_connections(self):
        manager = ConnectionManager()
        ws_ok = AsyncMock()
        ws_fail = AsyncMock()
        ws_fail.send_text.side_effect = Exception("Connection lost")
        manager.active_connections = [ws_ok, ws_fail]
        await manager.broadcast_event({"type": "test"})
        assert ws_ok in manager.active_connections
        assert ws_fail not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_alert(self):
        manager = ConnectionManager()
        ws = AsyncMock()
        manager.active_connections = [ws]
        await manager.broadcast_alert({"severity": "HIGH", "alert_type": "test"})
        call_args = ws.send_text.call_args[0][0]
        data = json.loads(call_args)
        assert data["type"] == "alert"
        assert data["data"]["severity"] == "HIGH"
