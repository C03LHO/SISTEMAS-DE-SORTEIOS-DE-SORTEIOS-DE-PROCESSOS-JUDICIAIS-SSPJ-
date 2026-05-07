"""
Router do Estado do Sorteio.

Expõe o estado interno do algoritmo de sorteio (singleton LotteryState).
Útil para auditoria e monitoramento do balanceamento de cargas.

Rotas:
  GET /lottery/state  — retorna o estado atual do algoritmo (TI, JUDGE, ASSESSOR)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_roles
from app.models.user import UserRole
from app.models.lottery import LotteryState, LOTTERY_STATE_ID

router = APIRouter(prefix="/lottery", tags=["Sorteio"])


@router.get(
    "/state",
    summary="Estado atual do algoritmo de sorteio",
    description=(
        "Retorna o estado interno do sorteio: participantes da rodada COMPLEX, "
        "prioridades de juízes (certeiro) e somas ponderadas de cada juiz. "
        "Acesso: TI, JUDGE, ASSESSOR."
    ),
)
async def estado_do_sorteio(
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI, UserRole.JUDGE, UserRole.ASSESSOR),
):
    """
    O LotteryState é uma tabela singleton — sempre há exatamente 1 linha.
    Criada automaticamente pelo seed.py.
    """
    result = await db.execute(
        select(LotteryState).where(LotteryState.id == LOTTERY_STATE_ID)
    )
    state = result.scalar_one_or_none()
    if not state:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Estado do sorteio não inicializado. Execute seed.py primeiro.",
        )

    return {
        "id": str(state.id),
        "complex_round_participants": state.complex_round_participants,
        "judge_priorities": state.judge_priorities,
        "judge_weighted_sums": state.judge_weighted_sums,
        "complex_round_count": len(state.complex_round_participants),
        "judges_with_priority": list(state.judge_priorities.keys()),
    }
