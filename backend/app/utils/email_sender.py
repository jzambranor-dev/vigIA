"""Servicio de envio de alertas por email via SMTP."""

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_alert_email(alert_data: dict) -> bool:
    """Envia un email de alerta critica. Retorna True si se envio correctamente."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD or not settings.ALERT_EMAIL_TO:
        return False

    try:
        severity = alert_data.get("severity", "UNKNOWN")
        alert_type = alert_data.get("alert_type", "unknown")
        description = alert_data.get("description", "")
        source_ip = alert_data.get("source_ip", "N/A")

        subject = f"[vigIA] Alerta {severity}: {alert_type}"

        html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #1a1a2e; color: #ffffff; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #16213e; border-radius: 12px; overflow: hidden; border: 1px solid #0f3460;">
                <div style="background-color: {'#dc2626' if severity == 'CRITICAL' else '#f97316' if severity == 'HIGH' else '#eab308'}; padding: 16px 24px;">
                    <h1 style="margin: 0; font-size: 20px; color: #ffffff;">
                        Alerta {severity}
                    </h1>
                </div>
                <div style="padding: 24px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; color: #9ca3af; width: 120px;">Tipo:</td>
                            <td style="padding: 8px 0; font-weight: bold;">{alert_type}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #9ca3af;">IP Origen:</td>
                            <td style="padding: 8px 0; font-family: monospace;">{source_ip}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #9ca3af;">Descripcion:</td>
                            <td style="padding: 8px 0;">{description}</td>
                        </tr>
                    </table>
                    <hr style="border-color: #0f3460; margin: 20px 0;">
                    <p style="color: #6b7280; font-size: 12px; margin: 0;">
                        Este email fue enviado automaticamente por vigIA - Sistema de Monitoreo de Seguridad
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"vigIA Alerts <{settings.SMTP_USER}>"
        msg["To"] = settings.ALERT_EMAIL_TO
        msg.attach(MIMEText(description, "plain"))
        msg.attach(MIMEText(html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, settings.ALERT_EMAIL_TO.split(","), msg.as_string())

        logger.info("Email de alerta enviado: %s -> %s", subject, settings.ALERT_EMAIL_TO)
        return True

    except Exception:
        logger.exception("Error enviando email de alerta")
        return False
