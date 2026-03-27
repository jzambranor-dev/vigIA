"""API router para generación de reportes PDF."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.utils.pdf_generator import generate_report_pdf

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.get("/pdf")
@limiter.limit("20/hour")
async def download_report_pdf(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Genera y descarga un reporte PDF ejecutivo."""
    pdf_buffer = await generate_report_pdf(db)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_seguridad.pdf"},
    )
