"""
Schemas Pydantic v2 para Conflitos de Interesse.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class JudgeConflictCreate(BaseModel):
    """Dados para registrar um conflito pré-cadastrado entre juiz e pessoa."""
    judge_id: UUID
    person_id: UUID
    reason: str = Field(..., min_length=5, max_length=500)


class JudgeConflictResponse(BaseModel):
    id: UUID
    judge_id: UUID
    person_id: UUID
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConflictRefuseRequest(BaseModel):
    """
    Dados para um juiz recusar formalmente um processo.
    O documento é enviado via multipart/form-data (campo separado).
    """
    process_id: UUID = Field(..., description="ID do processo recusado")
    justification: str = Field(
        ...,
        min_length=10,
        description="Justificativa detalhada da recusa"
    )


class ConflictRecordResponse(BaseModel):
    """Dados do registro de recusa retornados pela API."""
    id: UUID
    process_id: UUID
    judge_id: UUID
    justification: str
    document_path: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignTempJudgeRequest(BaseModel):
    """Dados para TI nomear um juiz temporário."""
    process_id: UUID = Field(..., description="ID do processo")
    temp_judge_user_id: UUID = Field(..., description="ID do usuário (TEMP_JUDGE ou JUDGE)")
