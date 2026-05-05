"""
Schemas Pydantic v2 para o sistema de sorteio.
"""

from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class LotteryRoundResponse(BaseModel):
    """Dados de um registro de sorteio."""
    id: UUID
    executed_at: datetime
    process_id: UUID
    judge_id: UUID
    round_number: int

    model_config = {"from_attributes": True}


class LotteryStateResponse(BaseModel):
    """Estado atual do algoritmo de sorteio."""
    id: UUID
    complex_round_participants: list
    judge_priorities: dict
    judge_weighted_sums: dict

    model_config = {"from_attributes": True}
