"""
Schemas Pydantic v2 para Pessoas (partes dos processos).
"""

from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.person import DocumentType


class PersonCreate(BaseModel):
    """Dados para cadastrar uma nova pessoa."""
    name: str = Field(..., min_length=2, max_length=200)
    document: str = Field(
        ...,
        description="CPF (11 dígitos) ou CNPJ (14 dígitos) sem formatação"
    )
    document_type: DocumentType


class PersonResponse(BaseModel):
    """Dados da pessoa retornados pela API."""
    id: UUID
    name: str
    document: str
    document_type: DocumentType
    created_at: datetime

    model_config = {"from_attributes": True}
