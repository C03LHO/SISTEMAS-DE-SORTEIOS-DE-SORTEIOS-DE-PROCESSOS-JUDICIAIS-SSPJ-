"""
Serviço de Processos Judiciais.

Gerencia o ciclo de vida dos processos:
- Cadastro com agendamento automático do sorteio
- Listagem filtrada por role
- Atualização com validação de status
- Reabertura de processo encerrado
- Histórico de sorteios
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.process import Process, ProcessStatus
from app.models.lottery import LotteryRound
from app.models.user import UserRole
from app.schemas.process import ProcessCreate, ProcessUpdate
from app.utils.business_days import next_business_day
import app.services.audit_service as audit_service


async def create_process(
    data: ProcessCreate,
    db: AsyncSession,
    created_by: object,  # objeto User
) -> Process:
    """
    Cadastra um novo processo e agenda o sorteio para o próximo dia útil às 10:00.
    """
    # Verifica se já existe um processo com este número
    result = await db.execute(
        select(Process).where(Process.process_number == data.process_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Processo '{data.process_number}' já está cadastrado"
        )

    # Calcula quando o sorteio deve acontecer
    lottery_at = next_business_day(datetime.utcnow())

    process = Process(
        process_number=data.process_number,
        level=data.level.value,
        person_id=data.person_id,
        process_type=data.process_type,
        court_unit=data.court_unit,
        description=data.description,
        lottery_scheduled_at=lottery_at,
        created_by_id=created_by.id,
    )
    db.add(process)

    await audit_service.log(
        db=db,
        action="PROCESS_CREATED",
        entity="process",
        entity_id=str(process.id),
        user_id=created_by.id,
        details={
            "process_number": data.process_number,
            "level": data.level.value,
            "lottery_scheduled_at": lottery_at.isoformat(),
        },
    )

    await db.commit()
    await db.refresh(process)
    return process


async def get_processes(
    db: AsyncSession,
    current_user: object,  # objeto User
) -> list[Process]:
    """
    Retorna processos filtrados de acordo com o role do usuário:
    - TI: todos os processos
    - JUDGE: processos atribuídos ao próprio juiz
    - ASSESSOR: processos atribuídos ao juiz vinculado ao assessor
    """
    query = select(Process)

    if current_user.role == UserRole.TI.value:
        # TI vê tudo
        pass
    elif current_user.role == UserRole.JUDGE.value:
        query = query.where(Process.assigned_judge_id == current_user.id)
    elif current_user.role == UserRole.ASSESSOR.value:
        # Assessor vê os processos do juiz ao qual está vinculado
        if not current_user.judge_id:
            return []
        query = query.where(Process.assigned_judge_id == current_user.judge_id)
    else:
        # Outros roles não têm acesso à listagem geral
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu papel não permite listar processos"
        )

    result = await db.execute(query.order_by(Process.created_at.desc()))
    return list(result.scalars().all())


async def get_process_by_id(process_id: UUID, db: AsyncSession) -> Process:
    """Busca um processo pelo UUID. Levanta 404 se não encontrado."""
    result = await db.execute(select(Process).where(Process.id == process_id))
    process = result.scalar_one_or_none()
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processo não encontrado"
        )
    return process


async def update_process(
    process_id: UUID,
    data: ProcessUpdate,
    db: AsyncSession,
    current_user: object,
) -> Process:
    """
    Atualiza um processo.

    Regras:
    - ASSISTANT: só pode editar se status == PENDING_LOTTERY
    - ASSESSOR: pode editar pós-sorteio (representa seu juiz vinculado)
    - TI: pode editar sempre
    """
    process = await get_process_by_id(process_id, db)

    # ASSISTANT só pode editar antes do sorteio
    if current_user.role == UserRole.ASSISTANT.value:
        if process.status != ProcessStatus.PENDING_LOTTERY.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assistentes só podem editar processos com status PENDING_LOTTERY"
            )

    # Aplica apenas os campos não-None
    if data.process_number is not None:
        process.process_number = data.process_number
    if data.level is not None:
        process.level = data.level.value
    if data.person_id is not None:
        process.person_id = data.person_id
    if data.process_type is not None:
        process.process_type = data.process_type
    if data.court_unit is not None:
        process.court_unit = data.court_unit
    if data.description is not None:
        process.description = data.description

    await audit_service.log(
        db=db,
        action="PROCESS_UPDATED",
        entity="process",
        entity_id=str(process_id),
        user_id=current_user.id,
        details={"fields_changed": list(data.model_dump(exclude_none=True).keys())},
    )

    await db.commit()
    await db.refresh(process)
    return process


async def reopen_process(
    process_id: UUID,
    justification: str,
    db: AsyncSession,
    current_user: object,
) -> Process:
    """
    Reabre um processo encerrado.

    Ao reabrir, o status muda para REOPENED e o sorteio seguinte atribuirá
    automaticamente o processo de volta ao juiz original (original_judge_id).
    """
    process = await get_process_by_id(process_id, db)

    if process.status != ProcessStatus.CLOSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Somente processos com status CLOSED podem ser reabertos. Status atual: {process.status}"
        )

    process.status = ProcessStatus.REOPENED.value
    # Reagenda o sorteio para o próximo dia útil
    process.lottery_scheduled_at = next_business_day(datetime.utcnow())

    await audit_service.log(
        db=db,
        action="PROCESS_REOPENED",
        entity="process",
        entity_id=str(process_id),
        user_id=current_user.id,
        details={
            "justification": justification,
            "original_judge_id": str(process.original_judge_id),
        },
    )

    await db.commit()
    await db.refresh(process)
    return process


async def get_process_history(process_id: UUID, db: AsyncSession) -> list[LotteryRound]:
    """Retorna o histórico completo de sorteios de um processo."""
    # Verifica se o processo existe
    await get_process_by_id(process_id, db)

    result = await db.execute(
        select(LotteryRound)
        .where(LotteryRound.process_id == process_id)
        .order_by(LotteryRound.executed_at)
    )
    return list(result.scalars().all())
