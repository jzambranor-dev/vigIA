"""API router para configuracion del sistema (solo admin)."""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import require_admin
from app.config import settings
from app.models.user import User
from app.utils.email_sender import send_alert_email

logger = logging.getLogger(__name__)

router = APIRouter()

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")


def _read_env() -> dict:
    """Lee el archivo .env y retorna como diccionario."""
    env = {}
    try:
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return env


def _write_env(env: dict) -> None:
    """Escribe el diccionario al archivo .env preservando comentarios."""
    lines = []
    try:
        with open(ENV_PATH, "r") as f:
            original_lines = f.readlines()
    except FileNotFoundError:
        original_lines = []

    written_keys = set()
    for line in original_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in env:
                lines.append(f"{key}={env[key]}\n")
                written_keys.add(key)
            else:
                lines.append(line)
        else:
            lines.append(line)

    # Agregar keys nuevas que no existian
    for key, value in env.items():
        if key not in written_keys:
            lines.append(f"{key}={value}\n")

    with open(ENV_PATH, "w") as f:
        f.writelines(lines)


class SMTPSettings(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_ssl: bool = True
    smtp_user: str
    smtp_password: str
    alert_email_to: str


class GeneralSettings(BaseModel):
    log_paths: str
    cors_origins: str
    jwt_expire_minutes: int = 480


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.get("/current")
async def get_settings(admin: User = Depends(require_admin)):
    """Obtener configuracion actual (solo admin)."""
    return {
        "smtp": {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "ssl": settings.SMTP_SSL,
            "user": settings.SMTP_USER,
            "password_set": bool(settings.SMTP_PASSWORD),
            "alert_email_to": settings.ALERT_EMAIL_TO,
        },
        "general": {
            "log_paths": settings.LOG_PATHS,
            "cors_origins": settings.CORS_ORIGINS,
            "jwt_expire_minutes": settings.JWT_EXPIRE_MINUTES,
            "debug": settings.DEBUG,
        },
        "info": {
            "version": "0.3.0",
            "postgres_host": settings.POSTGRES_HOST,
            "postgres_db": settings.POSTGRES_DB,
            "redis_host": settings.REDIS_HOST,
        },
    }


@router.put("/smtp")
async def update_smtp(body: SMTPSettings, admin: User = Depends(require_admin)):
    """Actualizar configuracion SMTP (requiere restart del backend)."""
    env = _read_env()
    env["SMTP_HOST"] = body.smtp_host
    env["SMTP_PORT"] = str(body.smtp_port)
    env["SMTP_SSL"] = str(body.smtp_ssl).lower()
    env["SMTP_USER"] = body.smtp_user
    env["SMTP_PASSWORD"] = body.smtp_password
    env["ALERT_EMAIL_TO"] = body.alert_email_to
    _write_env(env)

    # Actualizar settings en memoria
    settings.SMTP_HOST = body.smtp_host
    settings.SMTP_PORT = body.smtp_port
    settings.SMTP_SSL = body.smtp_ssl
    settings.SMTP_USER = body.smtp_user
    settings.SMTP_PASSWORD = body.smtp_password
    settings.ALERT_EMAIL_TO = body.alert_email_to

    logger.info("Configuracion SMTP actualizada por %s", admin.username)
    return {"status": "ok", "message": "Configuracion SMTP actualizada"}


@router.put("/general")
async def update_general(body: GeneralSettings, admin: User = Depends(require_admin)):
    """Actualizar configuracion general (requiere restart para LOG_PATHS)."""
    env = _read_env()
    env["LOG_PATHS"] = body.log_paths
    env["CORS_ORIGINS"] = body.cors_origins
    env["JWT_EXPIRE_MINUTES"] = str(body.jwt_expire_minutes)
    _write_env(env)

    settings.CORS_ORIGINS = body.cors_origins
    settings.JWT_EXPIRE_MINUTES = body.jwt_expire_minutes

    logger.info("Configuracion general actualizada por %s", admin.username)
    return {"status": "ok", "message": "Configuracion general actualizada"}


@router.post("/test-email")
async def test_email(admin: User = Depends(require_admin)):
    """Enviar email de prueba con la configuracion actual."""
    result = send_alert_email({
        "severity": "CRITICAL",
        "alert_type": "test_email",
        "description": f"Email de prueba enviado por {admin.username} desde vigIA. Si recibes este mensaje, la configuracion SMTP es correcta.",
        "source_ip": "127.0.0.1",
    })

    if result:
        return {"status": "ok", "message": f"Email de prueba enviado a {settings.ALERT_EMAIL_TO}"}
    else:
        raise HTTPException(status_code=500, detail="Error enviando email. Verifica la configuracion SMTP.")
