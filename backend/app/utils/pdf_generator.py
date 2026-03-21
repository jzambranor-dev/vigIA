"""Generador de reportes PDF ejecutivos con ReportLab."""

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.event import LogEvent


async def generate_report_pdf(db: AsyncSession) -> io.BytesIO:
    """Genera un reporte PDF ejecutivo con estadísticas de seguridad."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Título
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"], fontSize=20, spaceAfter=30
    )
    elements.append(Paragraph("Reporte de Seguridad - Log Analyzer AI", title_style))
    elements.append(Paragraph(
        f"Generado: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 0.3 * inch))

    # Estadísticas generales
    total_events = (await db.execute(select(func.count(LogEvent.id)))).scalar() or 0
    total_anomalies = (await db.execute(
        select(func.count(LogEvent.id)).where(LogEvent.is_anomaly.is_(True))
    )).scalar() or 0
    total_alerts = (await db.execute(select(func.count(Alert.id)))).scalar() or 0

    elements.append(Paragraph("Resumen General", styles["Heading2"]))
    summary_data = [
        ["Métrica", "Valor"],
        ["Total de eventos", str(total_events)],
        ["Anomalías detectadas", str(total_anomalies)],
        ["Alertas generadas", str(total_alerts)],
    ]
    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Alertas por severidad
    severity_result = await db.execute(
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    )
    severity_data = [["Severidad", "Cantidad"]]
    for row in severity_result.all():
        severity_data.append([row[0], str(row[1])])

    if len(severity_data) > 1:
        elements.append(Paragraph("Alertas por Severidad", styles["Heading2"]))
        sev_table = Table(severity_data, colWidths=[3 * inch, 2 * inch])
        sev_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e94560")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(sev_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
