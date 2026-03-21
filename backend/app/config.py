"""Configuración centralizada del proyecto usando pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Lee todas las variables de entorno desde .env."""

    # PostgreSQL
    POSTGRES_DB: str = "loganalyzer"
    POSTGRES_USER: str = "loguser"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # FastAPI
    SECRET_KEY: str = "changeme-in-production"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # Logs a monitorear
    LOG_PATHS: str = "/var/log/auth.log,/var/log/syslog"

    # Email (opcional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_EMAIL_TO: str = ""

    # AbuseIPDB (opcional)
    ABUSEIPDB_API_KEY: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def log_paths_list(self) -> list[str]:
        return [p.strip() for p in self.LOG_PATHS.split(",") if p.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
