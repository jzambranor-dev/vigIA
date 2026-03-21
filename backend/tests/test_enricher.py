"""Tests para el enriquecedor de eventos."""

import pytest

from app.core.enricher import _is_private_ip, enrich_event


class TestPrivateIP:

    def test_private_10(self):
        assert _is_private_ip("10.0.0.1") is True
        assert _is_private_ip("10.255.255.255") is True

    def test_private_172(self):
        assert _is_private_ip("172.16.0.1") is True
        assert _is_private_ip("172.31.255.255") is True
        assert _is_private_ip("172.15.0.1") is False
        assert _is_private_ip("172.32.0.1") is False

    def test_private_192(self):
        assert _is_private_ip("192.168.1.1") is True
        assert _is_private_ip("192.169.1.1") is False

    def test_loopback(self):
        assert _is_private_ip("127.0.0.1") is True

    def test_public(self):
        assert _is_private_ip("8.8.8.8") is False
        assert _is_private_ip("45.33.32.156") is False

    def test_invalid_ip(self):
        assert _is_private_ip("not-an-ip") is False
        assert _is_private_ip("999.999.999") is False


class TestEnrichEvent:

    @pytest.mark.asyncio
    async def test_enrich_private_ip_unchanged(self):
        event = {"source_ip": "192.168.1.10", "message_parsed": {}}
        result = await enrich_event(event)
        assert "enrichment" not in (result.get("message_parsed") or {})

    @pytest.mark.asyncio
    async def test_enrich_no_ip_unchanged(self):
        event = {"source_ip": None, "message_parsed": {}}
        result = await enrich_event(event)
        assert result == event

    @pytest.mark.asyncio
    async def test_enrich_public_ip_no_key(self):
        """Sin API key, no enriquece pero no falla."""
        event = {"source_ip": "45.33.32.156", "message_parsed": {}}
        result = await enrich_event(event)
        # Sin API key configurada, no debería agregar enrichment
        assert result["source_ip"] == "45.33.32.156"
