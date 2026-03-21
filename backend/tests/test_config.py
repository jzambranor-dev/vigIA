"""Tests para la configuración."""

from app.config import settings


class TestConfig:

    def test_database_url_format(self):
        url = settings.DATABASE_URL
        assert url.startswith("postgresql+asyncpg://")
        assert settings.POSTGRES_USER in url
        assert settings.POSTGRES_DB in url

    def test_redis_url_format(self):
        url = settings.REDIS_URL
        assert url.startswith("redis://")

    def test_log_paths_list(self):
        paths = settings.log_paths_list
        assert isinstance(paths, list)
        assert len(paths) > 0
        for p in paths:
            assert p.strip() == p  # no leading/trailing whitespace

    def test_default_values(self):
        assert settings.API_PORT == 8000
        assert settings.SMTP_PORT == 587
