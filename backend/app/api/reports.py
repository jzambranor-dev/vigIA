"""API router para generación de reportes PDF."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.pdf_generator import generate_report_pdf

router = APIRouter()


@router.get("/pdf")
async def download_report_pdf(db: AsyncSession = Depends(get_db)):
    """Genera y descarga un reporte PDF ejecutivo."""
    pdf_buffer = await generate_report_pdf(db)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_seguridad.pdf"},
    )
