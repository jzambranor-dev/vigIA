"""Tests async del alert engine con Redis mockeado."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.alert_engine import AlertEngine


class TestAlertEngineAsync:

    @pytest.fixture
    def engine_with_mock_redis(self):
        engine = AlertEngine()
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipe
        engine.redis_client = mock_redis
        return engine, mock_pipe

    @pytest.mark.asyncio
    async def test_brute_force_ssh_high(self, engine_with_mock_redis):
        engine, mock_pipe = engine_with_mock_redis
        mock_pipe.execute.return_value = [5, True]

        event = {
            "event_type": "ssh_login_failed",
            "source_ip": "1.2.3.4",
            "message_parsed": {},
        }
        result = await engine.evaluate(event)
        assert result is not None
        assert result["severity"] == "HIGH"
        assert result["alert_type"] == "brute_force_ssh"

    @pytest.mark.asyncio
    async def test_brute_force_ssh_critical(self, engine_with_mock_redis):
        engine, mock_pipe = engine_with_mock_redis
        mock_pipe.execute.return_value = [20, True]

        event = {
            "event_type": "ssh_login_failed",
            "source_ip": "1.2.3.4",
            "message_parsed": {},
        }
        result = await engine.evaluate(event)
        assert result is not None
        assert result["severity"] == "CRITICAL"

    @pytest.mark.asyncio
    async def test_brute_force_ssh_below_threshold(self, engine_with_mock_redis):
        engine, mock_pipe = engine_with_mock_redis
        mock_pipe.execute.return_value = [2, True]

        event = {
            "event_type": "ssh_login_failed",
            "source_ip": "1.2.3.4",
            "message_parsed": {},
        }
        result = await engine.evaluate(event)
        assert result is None

    @pytest.mark.asyncio
    async def test_brute_force_web(self, engine_with_mock_redis):
        engine, mock_pipe = engine_with_mock_redis
        mock_pipe.execute.return_value = [10, True]

        event = {
            "event_type": "apache_access",
            "source_ip": "1.2.3.4",
            "message_parsed": {"status": 401},
        }
        result = await engine.evaluate(event)
        assert result is not None
        assert result["alert_type"] == "brute_force_web"

    @pytest.mark.asyncio
    async def test_directory_traversal(self, engine_with_mock_redis):
        engine, mock_pipe = engine_with_mock_redis
        mock_pipe.execute.return_value = [1, True]

        event = {
            "event_type": "apache_access",
            "source_ip": "1.2.3.4",
            "message_parsed": {"url": "/../../etc/passwd", "status": 200},
        }
        result = await engine.evaluate(event)
        assert result is not None
        assert result["alert_type"] == "directory_traversal"
        assert result["severity"] == "CRITICAL"

    @pytest.mark.asyncio
    async def test_sql_injection(self, engine_with_mock_redis):
        engine, mock_pipe = engine_with_mock_redis
        mock_pipe.execute.return_value = [1, True]

        event = {
            "event_type": "apache_access",
            "source_ip": "1.2.3.4",
            "message_parsed": {"url": "/search?q=1' UNION SELECT * FROM users", "status": 200},
        }
        result = await engine.evaluate(event)
        assert result is not None
        assert result["alert_type"] == "sql_injection"

    @pytest.mark.asyncio
    async def test_sudo_root(self, engine_with_mock_redis):
        engine, _ = engine_with_mock_redis
        event = {
            "event_type": "sudo_command",
            "source_ip": None,
            "username": "hacker",
            "message_parsed": {"target_user": "root", "command": "/bin/bash"},
        }
        result = await engine.evaluate(event)
        assert result is not None
        assert result["alert_type"] == "sudo_root"
        assert result["severity"] == "MEDIUM"

    @pytest.mark.asyncio
    async def test_normal_event_no_alert(self, engine_with_mock_redis):
        engine, _ = engine_with_mock_redis
        event = {
            "event_type": "ssh_login_accepted",
            "source_ip": "192.168.1.1",
            "message_parsed": {},
        }
        result = await engine.evaluate(event)
        assert result is None

    @pytest.mark.asyncio
    async def test_connect_and_close(self):
        engine = AlertEngine()
        with patch("app.core.alert_engine.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client
            await engine.connect()
            assert engine.redis_client is not None
            await engine.close()
            mock_client.close.assert_called_once()
