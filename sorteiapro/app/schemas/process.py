"""
Schemas Pydantic v2 para Processos Judiciais.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.process import ProcessLevel, ProcessStatus


class ProcessCreate(BaseModel):
    """Dados para cadastrar um novo processo."""
    process_number: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Número único do processo (ex: 0001234-56.2024.8.06.0001)"
    )
    level: ProcessLevel = Field(..., description="Nível de complexidade: 1=BASIC, 2=INTERMEDIATE, 3=COMPLEX")
    person_id: UUID = Field(..., description="ID da pessoa (parte do processo)")


class ProcessUpdate(BaseModel):
    """
    Dados que podem ser atualizados em um processo.
    ASSISTANT só pode alterar antes do sorteio (status=PENDING_LOTTERY).
    """
    process_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    level: Optional[ProcessLevel] = None
    person_id: Optional[UUID] = None


class ProcessResponse(BaseModel):
    """Dados completos do processo retornados pela API."""
    id: UUID
    process_number: str
    level: ProcessLevel
    status: ProcessStatus
    person_id: UUID
    assigned_judge_id: Optional[UUID] = None
    temp_judge_id: Optional[UUID] = None
    original_judge_id: Optional[UUID] = None
    lottery_scheduled_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReopenRequest(BaseModel):
    """Dados para reabrir um processo encerrado."""
    justification: str = Field(
        ...,
        min_length=10,
        description="Motivo da reabertura do processo"
    )
