"""
Modelos SQLAlchemy para o sistema de sorteio.

LotteryRound: histórico de cada sorteio realizado.
  - Registra qual juiz foi sorteado para qual processo em qual rodada.

LotteryState: estado global do algoritmo de sorteio (tabela singleton).
  - Sempre há exatamente 1 linha nesta tabela.
  - Armazena os dados de balanceamento e rodízio em colunas JSONB.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# ID fixo da linha singleton do LotteryState
LOTTERY_STATE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class LotteryRound(Base):
    """Registro histórico de cada execução de sorteio."""

    __tablename__ = "lottery_rounds"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    process_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("processes.id"),
        nullable=False
    )
    judge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    # Número da rodada dentro do ciclo de rodízio COMPLEX
    round_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    process: Mapped["Process"] = relationship("Process")  # noqa: F821
    judge: Mapped["User"] = relationship("User")  # noqa: F821


class LotteryState(Base):
    """
    Estado global do algoritmo de sorteio — sempre 1 linha (singleton).

    Campos JSONB:
      complex_round_participants: lista de judge_ids que já receberam processo
        COMPLEX na rodada atual. Reiniciada quando todos os 8 participarem.

      judge_priorities: dict {judge_id: level} — juízes que recusaram recebem
        prioridade para o próximo sorteio do mesmo nível ("sorteio certeiro").

      judge_weighted_sums: dict {judge_id: soma_pesos} — soma dos pesos
        dos processos atribuídos a cada juiz (BASIC=1, INTERMEDIATE=2, COMPLEX=3).
        Usado para alertar sobre desequilíbrio na distribuição.
    """

    __tablename__ = "lottery_state"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=lambda: LOTTERY_STATE_ID
    )

    # Lista de IDs dos juízes que já receberam processo COMPLEX na rodada atual
    complex_round_participants: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False
    )

    # Juízes com prioridade no próximo sorteio (após recusa de processo)
    judge_priorities: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False
    )

    # Soma ponderada dos processos por juiz (para verificar balanceamento)
    judge_weighted_sums: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False
    )
