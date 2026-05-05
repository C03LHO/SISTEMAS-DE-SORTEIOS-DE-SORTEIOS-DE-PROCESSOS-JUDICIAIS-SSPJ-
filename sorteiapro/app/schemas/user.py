"""
Schemas Pydantic v2 para Usuários.

Padrão de nomenclatura:
  - UserCreate: dados para criar um novo usuário (entrada)
  - UserUpdate: dados para atualizar (todos opcionais)
  - UserResponse: dados retornados pela API (saída)
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Dados necessários para criar um novo usuário."""
    name: str = Field(..., min_length=2, max_length=200, description="Nome completo")
    email: EmailStr = Field(..., description="Email único do usuário")
    password: str = Field(..., min_length=6, description="Senha (mínimo 6 caracteres)")
    role: UserRole = Field(..., description="Papel do usuário no sistema")
    judge_id: Optional[UUID] = Field(
        default=None,
        description="ID do juiz (obrigatório se role=ASSESSOR)"
    )


class UserUpdate(BaseModel):
    """Campos que podem ser atualizados (todos opcionais)."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=6)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    judge_id: Optional[UUID] = None


class UserResponse(BaseModel):
    """Dados do usuário retornados pela API (sem senha)."""
    id: UUID
    name: str
    email: str
    role: UserRole
    is_active: bool
    judge_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LinkAssessorRequest(BaseModel):
    """Dados para vincular um assessor a um juiz."""
    judge_id: UUID = Field(..., description="ID do juiz ao qual o assessor será vinculado")
