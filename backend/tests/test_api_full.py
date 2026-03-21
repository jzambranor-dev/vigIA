"""Tests completos de API con base de datos SQLite en memoria."""

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import event as sa_event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from app.database import Base, get_db
from app.api import alerts, events, reports, stats

# SQLite async en memoria para tests
TEST_ENGINE = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = async_sessionmaker(bind=TEST_ENGINE, class_=AsyncSession, expire_on_commit=False)


@sa_event.listens_for(TEST_ENGINE.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def create_test_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(events.router, prefix="/api/events")
    test_app.include_router(alerts.router, prefix="/api/alerts")
    test_app.include_router(stats.router, prefix="/api/stats")
    test_app.include_router(reports.router, prefix="/api/reports")

    @test_app.get("/")
    async def root():
        return {"status": "ok", "project": "Log Analyzer AI"}

    test_app.dependency_overrides[get_db] = override_get_db
    return test_app


@pytest_asyncio.fixture
async def client():
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app = create_test_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestRootEndpoint:
    @pytest.mark.asyncio
    async def test_root(self, client):
        r = await client.get("/")
        assert r.status_code == 200
        assert r.json()["project"] == "Log Analyzer AI"


class TestEventsAPI:
    @pytest.mark.asyncio
    async def test_list_events_empty(self, client):
        r = await client.get("/api/events/")
        assert r.status_code == 200
        assert r.json()["total"] == 0
        assert r.json()["items"] == []

    @pytest.mark.asyncio
    async def test_list_events_with_all_filters(self, client):
        r = await client.get("/api/events/", params={
            "event_type": "ssh_login_failed",
            "is_anomaly": True,
            "source_ip": "1.2.3.4",
            "limit": 10,
            "skip": 0,
        })
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_get_event_not_found(self, client):
        r = await client.get("/api/events/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404


class TestAlertsAPI:
    @pytest.mark.asyncio
    async def test_list_alerts_empty(self, client):
        r = await client.get("/api/alerts/")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_list_alerts_with_filters(self, client):
        r = await client.get("/api/alerts/", params={
            "severity": "HIGH",
            "alert_type": "brute_force_ssh",
            "acknowledged": False,
        })
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_get_alert_not_found(self, client):
        r = await client.get("/api/alerts/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_acknowledge_not_found(self, client):
        r = await client.patch(
            "/api/alerts/00000000-0000-0000-0000-000000000000/acknowledge",
            json={"acknowledged": True},
        )
        assert r.status_code == 404


class TestStatsAPI:
    @pytest.mark.asyncio
    async def test_summary_empty(self, client):
        r = await client.get("/api/stats/summary")
        assert r.status_code == 200
        data = r.json()
        assert data["total_events"] == 0
        assert data["total_alerts"] == 0


class TestReportsAPI:
    @pytest.mark.asyncio
    async def test_pdf_report(self, client):
        r = await client.get("/api/reports/pdf")
        assert r.status_code == 200
        assert b"%PDF" in r.content
