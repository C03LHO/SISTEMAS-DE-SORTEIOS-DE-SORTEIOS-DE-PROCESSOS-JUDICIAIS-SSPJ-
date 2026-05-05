"""
Router de Conflitos de Interesse.

Rotas:
  POST /conflicts/refuse               — JUDGE: recusa formal com documento
  POST /conflicts/assign-temp-judge    — TI: nomeia juiz temporário
  POST /conflicts/close-temp-access/{process_id} — TI: encerra acesso temporário
  GET  /conflicts/judge/{judge_id}     — TI: lista conflitos pré-cadastrados de um juiz
  POST /conflicts/pre-register         — TI: cadastra conflito de proximidade
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_roles
from app.models.conflict import JudgeConflict
from app.models.user import UserRole
from app.schemas.conflict import (
    AssignTempJudgeRequest,
    ConflictRecordResponse,
    JudgeConflictCreate,
    JudgeConflictResponse,
)
from app.schemas.process import ProcessResponse
from app.services import conflict_service

router = APIRouter(prefix="/conflicts", tags=["Conflitos de Interesse"])


@router.post(
    "/refuse",
    response_model=ConflictRecordResponse,
    status_code=201,
    summary="Recusar processo (juiz)",
    description=(
        "O juiz recusa formalmente um processo por conflito de interesse. "
        "Deve enviar justificativa e documento comprobatório. "
        "O processo será reagendado para o próximo dia útil. Acesso: JUDGE."
    ),
)
async def recusar_processo(
    # Campos do formulário multipart/form-data
    process_id: UUID = Form(..., description="ID do processo a ser recusado"),
    justification: str = Form(..., min_length=10, description="Justificativa detalhada da recusa"),
    document: Optional[UploadFile] = File(default=None, description="Documento comprobatório (opcional)"),
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.JUDGE),
):
    return await conflict_service.refuse_process(
        process_id=process_id,
        judge_id=current_user.id,
        justification=justification,
        document=document,
        db=db,
    )


@router.post(
    "/assign-temp-judge",
    response_model=ProcessResponse,
    summary="Nomear juiz temporário (TI)",
    description=(
        "TI nomeia um juiz temporário para processo em CONFLICT_PENDING "
        "(quando todos os juízes titulares recusaram). Acesso: TI."
    ),
)
async def nomear_juiz_temporario(
    data: AssignTempJudgeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI),
):
    return await conflict_service.assign_temp_judge(
        process_id=data.process_id,
        temp_judge_user_id=data.temp_judge_user_id,
        db=db,
        assigned_by_id=current_user.id,
    )


@router.post(
    "/close-temp-access/{process_id}",
    response_model=ProcessResponse,
    summary="Encerrar acesso do juiz temporário (TI)",
    description=(
        "Remove o juiz temporário do processo e restaura o status para ASSIGNED. "
        "Acesso: TI."
    ),
)
async def encerrar_acesso_temporario(
    process_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI),
):
    return await conflict_service.close_temp_access(
        process_id=process_id,
        db=db,
        closed_by_id=current_user.id,
    )


@router.post(
    "/pre-register",
    response_model=JudgeConflictResponse,
    status_code=201,
    summary="Pré-cadastrar conflito de proximidade (TI)",
    description=(
        "Registra um conflito de proximidade entre um juiz e uma pessoa. "
        "O juiz será automaticamente excluído do sorteio para processos que "
        "envolvam essa pessoa. Acesso: TI."
    ),
)
async def pre_cadastrar_conflito(
    data: JudgeConflictCreate,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI),
):
    conflict = JudgeConflict(
        judge_id=data.judge_id,
        person_id=data.person_id,
        reason=data.reason,
    )
    db.add(conflict)
    await db.commit()
    await db.refresh(conflict)
    return conflict


@router.get(
    "/judge/{judge_id}",
    response_model=list[JudgeConflictResponse],
    summary="Listar conflitos de um juiz (TI)",
    description="Lista todos os conflitos de proximidade pré-cadastrados de um juiz. Acesso: TI.",
)
async def listar_conflitos_juiz(
    judge_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI),
):
    result = await db.execute(
        select(JudgeConflict).where(JudgeConflict.judge_id == judge_id)
    )
    return list(result.scalars().all())
