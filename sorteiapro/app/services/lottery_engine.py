"""
Kernel de Sorteio — coração do sistema SorteiaPro.

Este módulo implementa todo o algoritmo de sorteio, incluindo:

1. Carregamento de dados (processo, juízes, estado)
2. Atalho para processos REOPENED (volta ao juiz original)
3. Filtragem de juízes elegíveis:
   a. Remove juízes com conflito pré-cadastrado com a Person do processo
   b. Aplica rodízio obrigatório para processos COMPLEX
   c. Verifica juízes com prioridade ("sorteio certeiro" após recusa)
4. Seleção aleatória (ou prioritária) do juiz
5. Atribuição e persistência
6. Verificação de balanceamento de carga

Todos os campos JSONB do LotteryState são marcados com flag_modified()
para garantir que o SQLAlchemy detecte as mudanças.
"""

import random
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.lottery import LotteryRound, LotteryState, LOTTERY_STATE_ID
from app.models.process import Process, ProcessLevel, ProcessStatus
from app.models.user import User, UserRole
import app.services.audit_service as audit_service
from app.services.conflict_service import get_conflicts_for_person


async def _get_lottery_state(db: AsyncSession) -> LotteryState:
    """Carrega o singleton LotteryState do banco."""
    result = await db.execute(
        select(LotteryState).where(LotteryState.id == LOTTERY_STATE_ID)
    )
    state = result.scalar_one_or_none()
    if not state:
        raise RuntimeError(
            "LotteryState não encontrado. Certifique-se de ter executado seed.py."
        )
    return state


async def run_lottery(process_id: UUID, db: AsyncSession) -> None:
    """
    Executa o sorteio para um processo.

    Esta função é chamada:
    - Pelo APScheduler automaticamente (seg-sex às 10:00)
    - Manualmente via rota POST /processes/{id}/run-lottery (para testes)

    Args:
        process_id: UUID do processo a ser sorteado
        db: sessão assíncrona do banco de dados
    """

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO 1: Carregar dados
    # ─────────────────────────────────────────────────────────────────────────
    result = await db.execute(select(Process).where(Process.id == process_id))
    process = result.scalar_one_or_none()

    if not process:
        raise ValueError(f"Processo {process_id} não encontrado")

    # Apenas processa estados válidos para sorteio
    valid_statuses = {ProcessStatus.PENDING_LOTTERY.value, ProcessStatus.REOPENED.value}
    if process.status not in valid_statuses:
        return  # Silenciosamente ignora processos que não precisam de sorteio

    # Carrega todos os juízes ativos
    result = await db.execute(
        select(User).where(
            User.role == UserRole.JUDGE.value,
            User.is_active == True,
        )
    )
    all_judges: list[User] = list(result.scalars().all())

    # Carrega o estado global do sorteio
    state = await _get_lottery_state(db)

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO 2: Caso especial — processo REOPENED
    # Volta diretamente ao juiz original sem sorteio
    # ─────────────────────────────────────────────────────────────────────────
    if process.status == ProcessStatus.REOPENED.value and process.original_judge_id:
        process.assigned_judge_id = process.original_judge_id
        process.status = ProcessStatus.ASSIGNED.value
        process.assigned_at = datetime.utcnow()

        # Registra no histórico de sorteios
        lottery_round = LotteryRound(
            executed_at=datetime.utcnow(),
            process_id=process.id,
            judge_id=process.original_judge_id,
            round_number=0,
        )
        db.add(lottery_round)

        await audit_service.log(
            db=db,
            action="LOTTERY_REOPEN_ASSIGNED",
            entity="process",
            entity_id=str(process.id),
            details={"judge_id": str(process.original_judge_id), "reason": "Reabertura de processo"},
        )
        await db.commit()
        return  # Encerra aqui — não continua para o sorteio comum

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO 3a: Remover juízes com conflito pré-cadastrado com a Person
    # ─────────────────────────────────────────────────────────────────────────
    conflicts = await get_conflicts_for_person(process.person_id, db)
    conflict_judge_ids = {c.judge_id for c in conflicts}

    eligible_judges = [j for j in all_judges if j.id not in conflict_judge_ids]

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO 3b: Rodízio para processos COMPLEX
    # Garante que todos os juízes recebam um processo COMPLEX antes de reiniciar
    # ─────────────────────────────────────────────────────────────────────────
    if process.level == ProcessLevel.COMPLEX.value:
        participants = set(state.complex_round_participants)

        if len(participants) >= len(all_judges):
            # Todos os juízes já participaram desta rodada → reinicia o ciclo
            state.complex_round_participants = []
            flag_modified(state, "complex_round_participants")
            participants = set()

        # Remove da lista elegível quem já participou nesta rodada
        eligible_judges = [
            j for j in eligible_judges
            if str(j.id) not in participants
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO 3c: Verificar juízes com prioridade ("sorteio certeiro")
    # Um juiz recebe prioridade quando recusa um processo e depois é sorteado
    # para um do mesmo nível — ele recebe o processo sem concorrência
    # ─────────────────────────────────────────────────────────────────────────
    priority_judge_id: UUID | None = None
    priorities = dict(state.judge_priorities)  # cópia para manipular

    for judge_id_str, priority_level in list(priorities.items()):
        if priority_level == process.level:
            # Verifica se este juiz ainda está elegível
            candidate = next(
                (j for j in eligible_judges if str(j.id) == judge_id_str),
                None
            )
            if candidate:
                priority_judge_id = candidate.id
                # Remove a prioridade usada
                del priorities[judge_id_str]
                state.judge_priorities = priorities
                flag_modified(state, "judge_priorities")
                break

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO 4: Verificar se há juízes elegíveis
    # ─────────────────────────────────────────────────────────────────────────
    if not eligible_judges:
        # Nenhum juiz está disponível (todos têm conflito ou rodízio esgotado)
        process.status = ProcessStatus.CONFLICT_PENDING.value

        await audit_service.log(
            db=db,
            action="LOTTERY_ALL_CONFLICT",
            entity="process",
            entity_id=str(process.id),
            details={
                "message": "Nenhum juiz elegível. Aguardando nomeação de juiz temporário.",
                "conflict_judge_ids": [str(cid) for cid in conflict_judge_ids],
            },
        )
        await db.commit()
        return

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO 5: Selecionar o juiz
    # Usa prioridade se disponível, caso contrário sorteia aleatoriamente
    # ─────────────────────────────────────────────────────────────────────────
    if priority_judge_id:
        selected_judge = next(
            j for j in eligible_judges if j.id == priority_judge_id
        )
    else:
        selected_judge = random.choice(eligible_judges)

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO 6: Atribuir o processo ao juiz selecionado
    # ─────────────────────────────────────────────────────────────────────────
    process.assigned_judge_id = selected_judge.id
    process.original_judge_id = selected_judge.id  # guarda para reabertura futura
    process.status = ProcessStatus.ASSIGNED.value
    process.assigned_at = datetime.utcnow()

    # Atualiza o rodízio COMPLEX (adiciona o juiz à rodada atual)
    if process.level == ProcessLevel.COMPLEX.value:
        participants_list = list(state.complex_round_participants)
        participants_list.append(str(selected_judge.id))
        state.complex_round_participants = participants_list
        flag_modified(state, "complex_round_participants")

    # Atualiza a soma ponderada de carga de trabalho do juiz
    sums = dict(state.judge_weighted_sums)
    judge_id_str = str(selected_judge.id)
    sums[judge_id_str] = sums.get(judge_id_str, 0) + process.level
    state.judge_weighted_sums = sums
    flag_modified(state, "judge_weighted_sums")

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO 7: Registrar o sorteio no histórico
    # ─────────────────────────────────────────────────────────────────────────
    lottery_round = LotteryRound(
        executed_at=datetime.utcnow(),
        process_id=process.id,
        judge_id=selected_judge.id,
        round_number=len(state.complex_round_participants),
    )
    db.add(lottery_round)

    await audit_service.log(
        db=db,
        action="LOTTERY_SUCCESS",
        entity="process",
        entity_id=str(process.id),
        details={
            "judge_id": str(selected_judge.id),
            "judge_name": selected_judge.name,
            "process_level": process.level,
            "used_priority": priority_judge_id is not None,
        },
    )

    await db.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # PASSO 8: Verificar balanceamento de carga após atribuição
    # Gera alerta no audit log se a diferença entre o máximo e mínimo > 3
    # ─────────────────────────────────────────────────────────────────────────
    current_sums = list(state.judge_weighted_sums.values())
    if current_sums and (max(current_sums) - min(current_sums)) > 3:
        await audit_service.log(
            db=db,
            action="BALANCE_ALERT",
            entity="lottery_state",
            entity_id=str(LOTTERY_STATE_ID),
            details={
                "sums": state.judge_weighted_sums,
                "max": max(current_sums),
                "min": min(current_sums),
                "diff": max(current_sums) - min(current_sums),
            },
        )
        await db.commit()
