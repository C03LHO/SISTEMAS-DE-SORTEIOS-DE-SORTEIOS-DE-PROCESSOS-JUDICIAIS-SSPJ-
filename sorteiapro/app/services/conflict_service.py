"""
Serviço de Conflitos de Interesse.

Gerencia:
1. Recusa formal de um juiz: salva documento, cria ConflictRecord,
   adiciona prioridade ao LotteryState e reagenda o sorteio.
2. Atribuição de juiz temporário pelo TI.
3. Encerramento do acesso temporário.
4. Conflitos pré-cadastrados (JudgeConflict).
"""

import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.config import settings
from app.models.conflict import ConflictRecord, JudgeConflict
from app.models.lottery import LotteryState, LOTTERY_STATE_ID
from app.models.process import Process, ProcessStatus
from app.models.user import User, UserRole
from app.utils.business_days import next_business_day
import app.services.audit_service as audit_service


async def get_lottery_state(db: AsyncSession) -> LotteryState:
    """Retorna o singleton LotteryState. Levanta 500 se não existir."""
    result = await db.execute(
        select(LotteryState).where(LotteryState.id == LOTTERY_STATE_ID)
    )
    state = result.scalar_one_or_none()
    if not state:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LotteryState não inicializado. Execute seed.py."
        )
    return state


async def get_conflicts_for_person(person_id: UUID, db: AsyncSession) -> list[JudgeConflict]:
    """Retorna todos os JudgeConflicts pré-cadastrados para uma pessoa."""
    result = await db.execute(
        select(JudgeConflict).where(JudgeConflict.person_id == person_id)
    )
    return list(result.scalars().all())


async def refuse_process(
    process_id: UUID,
    judge_id: UUID,
    justification: str,
    document: Optional[UploadFile],
    db: AsyncSession,
) -> ConflictRecord:
    """
    Registra a recusa formal de um juiz para um processo.

    Fluxo:
    1. Salva o documento enviado em /uploads/{process_id}/
    2. Cria um ConflictRecord
    3. Adiciona prioridade ao LotteryState para o próximo sorteio
    4. Verifica se TODOS os juízes recusaram → CONFLICT_PENDING
    5. Caso contrário, reagenda o sorteio para o próximo dia útil
    """
    # Busca o processo
    result = await db.execute(select(Process).where(Process.id == process_id))
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(status_code=404, detail="Processo não encontrado")

    # Salva o arquivo de documento, se fornecido
    document_path: Optional[str] = None
    if document and document.filename:
        # Cria o diretório específico do processo
        upload_dir = os.path.join(settings.UPLOAD_DIR, str(process_id))
        os.makedirs(upload_dir, exist_ok=True)

        # Usa timestamp para evitar conflito de nomes
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{document.filename}"
        document_path = os.path.join(upload_dir, filename)

        # Lê e salva o conteúdo do arquivo
        content = await document.read()
        with open(document_path, "wb") as f:
            f.write(content)

    # Cria o registro de conflito/recusa
    conflict_record = ConflictRecord(
        process_id=process_id,
        judge_id=judge_id,
        justification=justification,
        document_path=document_path,
    )
    db.add(conflict_record)

    # Adiciona o juiz à lista de prioridades do LotteryState
    # "Sorteio certeiro": na próxima rodada deste nível, este juiz será preferido
    state = await get_lottery_state(db)
    priorities = dict(state.judge_priorities)
    priorities[str(judge_id)] = process.level
    state.judge_priorities = priorities
    flag_modified(state, "judge_priorities")

    # Conta quantos juízes ativos existem e quantos já recusaram este processo
    result_judges = await db.execute(
        select(User).where(
            User.role == UserRole.JUDGE.value,
            User.is_active == True
        )
    )
    all_judges = result_judges.scalars().all()
    total_judges = len(all_judges)

    result_refusals = await db.execute(
        select(ConflictRecord).where(ConflictRecord.process_id == process_id)
    )
    # +1 porque o registro atual ainda não foi contabilizado (não commitado)
    refusal_count = len(result_refusals.scalars().all()) + 1

    if refusal_count >= total_judges:
        # Todos os juízes recusaram — nomear juiz temporário via TI
        process.status = ProcessStatus.CONFLICT_PENDING.value
        await audit_service.log(
            db=db,
            action="LOTTERY_ALL_CONFLICT",
            entity="process",
            entity_id=str(process_id),
            details={
                "message": "Todos os juízes recusaram. Aguardando nomeação de juiz temporário.",
                "total_judges": total_judges,
            },
        )
    else:
        # Ainda há juízes disponíveis — reagenda o sorteio
        process.lottery_scheduled_at = next_business_day(datetime.utcnow())

    await audit_service.log(
        db=db,
        action="CONFLICT_REFUSED",
        entity="process",
        entity_id=str(process_id),
        user_id=judge_id,
        details={
            "justification": justification,
            "document_saved": document_path is not None,
            "refusal_count": refusal_count,
            "total_judges": total_judges,
        },
    )

    await db.commit()
    await db.refresh(conflict_record)
    return conflict_record


async def assign_temp_judge(
    process_id: UUID,
    temp_judge_user_id: UUID,
    db: AsyncSession,
    assigned_by_id: UUID,
) -> Process:
    """
    TI nomeia um juiz temporário para um processo em CONFLICT_PENDING.

    O usuário escolhido deve ter role TEMP_JUDGE ou JUDGE.
    """
    result = await db.execute(select(Process).where(Process.id == process_id))
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(status_code=404, detail="Processo não encontrado")

    if process.status != ProcessStatus.CONFLICT_PENDING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Processo deve ter status CONFLICT_PENDING para receber juiz temporário. Status atual: {process.status}"
        )

    # Verifica se o usuário existe e tem role compatível
    result_judge = await db.execute(select(User).where(User.id == temp_judge_user_id))
    temp_judge = result_judge.scalar_one_or_none()
    if not temp_judge:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    allowed_roles = {UserRole.TEMP_JUDGE.value, UserRole.JUDGE.value}
    if temp_judge.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="O usuário selecionado deve ter role TEMP_JUDGE ou JUDGE"
        )

    process.temp_judge_id = temp_judge_user_id
    process.status = ProcessStatus.TEMP_ASSIGNED.value

    await audit_service.log(
        db=db,
        action="TEMP_JUDGE_ASSIGNED",
        entity="process",
        entity_id=str(process_id),
        user_id=assigned_by_id,
        details={"temp_judge_id": str(temp_judge_user_id)},
    )

    await db.commit()
    await db.refresh(process)
    return process


async def close_temp_access(
    process_id: UUID,
    db: AsyncSession,
    closed_by_id: UUID,
) -> Process:
    """
    Encerra o acesso do juiz temporário ao processo.
    Remove o temp_judge_id e volta o status para ASSIGNED (juiz original).
    """
    result = await db.execute(select(Process).where(Process.id == process_id))
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(status_code=404, detail="Processo não encontrado")

    if process.status != ProcessStatus.TEMP_ASSIGNED.value:
        raise HTTPException(
            status_code=400,
            detail="Processo não possui juiz temporário ativo"
        )

    process.temp_judge_id = None
    process.status = ProcessStatus.ASSIGNED.value

    await audit_service.log(
        db=db,
        action="TEMP_ACCESS_CLOSED",
        entity="process",
        entity_id=str(process_id),
        user_id=closed_by_id,
    )

    await db.commit()
    await db.refresh(process)
    return process
