"""Schemas Pydantic para autenticación."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Schema para login."""

    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=4, max_length=128)


class TokenResponse(BaseModel):
    """Schema de respuesta con JWT token."""

    access_token: str
    token_type: str = "bearer"
    username: str
    is_admin: bool


class UserResponse(BaseModel):
    """Schema de respuesta de usuario."""

    id: UUID
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Schema para crear usuario (solo admin)."""

    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    is_admin: bool = False
