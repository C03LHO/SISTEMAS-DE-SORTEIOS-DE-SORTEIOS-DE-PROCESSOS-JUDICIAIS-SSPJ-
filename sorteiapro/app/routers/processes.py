"""
Router de Processos Judiciais.

Rotas e permissões:
  POST   /processes/               — ASSISTANT, TI
  GET    /processes/               — TI, JUDGE, ASSESSOR
  GET    /processes/{id}           — TI, JUDGE, ASSESSOR, TEMP_JUDGE
  PUT    /processes/{id}           — ASSISTANT (só PENDING_LOTTERY), ASSESSOR, TI
  POST   /processes/{id}/reopen   — TI, JUDGE
  GET    /processes/{id}/history  — TI, JUDGE, ASSESSOR
  POST   /processes/{id}/run-lottery — TI (sorteio manual para testes)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import UserRole
from app.models.process import ProcessStatus
from app.schemas.process import ProcessCreate, ProcessUpdate, ProcessResponse, ReopenRequest
from app.schemas.lottery import LotteryRoundResponse
from app.services import process_service
from app.services.lottery_engine import run_lottery

router = APIRouter(prefix="/processes", tags=["Processos"])


@router.post(
    "/",
    response_model=ProcessResponse,
    status_code=201,
    summary="Cadastrar processo",
    description="Cadastra um novo processo e agenda o sorteio para o próximo dia útil às 10:00. Acesso: ASSISTANT, TI.",
)
async def cadastrar_processo(
    data: ProcessCreate,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.ASSISTANT, UserRole.TI),
):
    return await process_service.create_process(data, db, created_by=current_user)


@router.get(
    "/",
    response_model=list[ProcessResponse],
    summary="Listar processos",
    description=(
        "Lista processos conforme o papel do usuário: "
        "TI vê todos; JUDGE vê os seus; ASSESSOR vê os do juiz vinculado. Acesso: TI, JUDGE, ASSESSOR."
    ),
)
async def listar_processos(
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI, UserRole.JUDGE, UserRole.ASSESSOR),
):
    return await process_service.get_processes(db, current_user)


@router.get(
    "/{process_id}",
    response_model=ProcessResponse,
    summary="Obter processo por ID",
    description=(
        "Retorna os detalhes de um processo. "
        "TEMP_JUDGE só pode acessar o processo ao qual foi designado. "
        "Acesso: TI, JUDGE, ASSESSOR, TEMP_JUDGE."
    ),
)
async def obter_processo(
    process_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI, UserRole.JUDGE, UserRole.ASSESSOR, UserRole.TEMP_JUDGE),
):
    process = await process_service.get_process_by_id(process_id, db)

    # TEMP_JUDGE só acessa o processo ao qual foi especificamente designado
    if current_user.role == UserRole.TEMP_JUDGE.value:
        if process.temp_judge_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Juiz temporário só pode acessar o processo ao qual foi designado"
            )

    return process


@router.put(
    "/{process_id}",
    response_model=ProcessResponse,
    summary="Atualizar processo",
    description=(
        "Atualiza dados do processo. "
        "ASSISTANT só pode editar se status for PENDING_LOTTERY. Acesso: ASSISTANT, ASSESSOR, TI."
    ),
)
async def atualizar_processo(
    process_id: UUID,
    data: ProcessUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.ASSISTANT, UserRole.ASSESSOR, UserRole.TI),
):
    return await process_service.update_process(process_id, data, db, current_user)


@router.post(
    "/{process_id}/reopen",
    response_model=ProcessResponse,
    summary="Reabrir processo",
    description=(
        "Reabre um processo CLOSED. O próximo sorteio atribuirá o processo "
        "de volta ao juiz original automaticamente. Acesso: TI, JUDGE."
    ),
)
async def reabrir_processo(
    process_id: UUID,
    data: ReopenRequest,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI, UserRole.JUDGE),
):
    return await process_service.reopen_process(
        process_id, data.justification, db, current_user
    )


@router.get(
    "/{process_id}/history",
    response_model=list[LotteryRoundResponse],
    summary="Histórico de sorteios",
    description="Retorna o histórico completo de sorteios de um processo. Acesso: TI, JUDGE, ASSESSOR.",
)
async def historico_processo(
    process_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI, UserRole.JUDGE, UserRole.ASSESSOR),
):
    return await process_service.get_process_history(process_id, db)


@router.post(
    "/{process_id}/run-lottery",
    summary="Forçar sorteio manual (apenas para testes)",
    description=(
        "Executa imediatamente o sorteio para um processo específico, "
        "sem esperar o scheduler às 10:00. Útil para testes e desenvolvimento. Acesso: TI."
    ),
)
async def forcar_sorteio(
    process_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI),
):
    """
    Útil para testar o algoritmo de sorteio sem precisar esperar o horário do cron.
    Apenas TI pode usar esta rota (rota de teste/administração).
    """
    process = await process_service.get_process_by_id(process_id, db)

    valid_statuses = {ProcessStatus.PENDING_LOTTERY.value, ProcessStatus.REOPENED.value}
    if process.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O processo precisa ter status PENDING_LOTTERY ou REOPENED. Status atual: {process.status}"
        )

    await run_lottery(process_id, db)

    # Recarrega o processo atualizado após o sorteio
    updated_process = await process_service.get_process_by_id(process_id, db)
    return {
        "detail": "Sorteio executado com sucesso",
        "process_id": str(process_id),
        "new_status": updated_process.status,
        "assigned_judge_id": str(updated_process.assigned_judge_id) if updated_process.assigned_judge_id else None,
    }
