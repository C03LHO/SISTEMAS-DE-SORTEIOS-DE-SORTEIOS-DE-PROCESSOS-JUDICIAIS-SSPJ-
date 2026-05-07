"""
Modelo SQLAlchemy para Processos Judiciais.

Ciclo de vida de um processo:
  PENDING_LOTTERY → (sorteio) → ASSIGNED → IN_PROGRESS → CLOSED
                                                       ↘ REOPENED → ASSIGNED
  Em caso de conflito: → CONFLICT_PENDING → (TI nomeia temp) → TEMP_ASSIGNED

Níveis do processo:
  BASIC (1): sem rodízio, peso 1 no balanceamento
  INTERMEDIATE (2): sem rodízio, peso 2
  COMPLEX (3): rodízio obrigatório entre os 8 juízes, peso 3
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProcessLevel(int, Enum):
    BASIC = 1
    INTERMEDIATE = 2
    COMPLEX = 3


class ProcessStatus(str, Enum):
    PENDING_LOTTERY = "PENDING_LOTTERY"     # aguardando sorteio
    SCHEDULED = "SCHEDULED"                  # sorteio agendado
    ASSIGNED = "ASSIGNED"                    # juiz atribuído
    IN_PROGRESS = "IN_PROGRESS"              # em andamento
    CLOSED = "CLOSED"                        # encerrado
    REOPENED = "REOPENED"                    # reaberto (volta ao juiz original)
    CONFLICT_PENDING = "CONFLICT_PENDING"    # todos os juízes recusaram
    TEMP_ASSIGNED = "TEMP_ASSIGNED"          # juiz temporário nomeado


class Process(Base):
    __tablename__ = "processes"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    # Número único do processo (ex: "0001234-56.2024.8.06.0001")
    process_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    # Tipo/natureza do processo (ex: "Ação Civil Pública", "Habeas Corpus")
    process_type: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True
    )

    # Vara ou unidade judicial responsável
    court_unit: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    # Descrição/resumo livre do processo
    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )

    level: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=ProcessStatus.PENDING_LOTTERY.value,
        nullable=False
    )

    # Pessoa (parte) do processo
    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("persons.id"),
        nullable=False
    )

    # Juiz atualmente responsável pelo processo
    assigned_judge_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    # Juiz temporário (quando todos os titulares recusaram)
    temp_judge_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    # Guarda o juiz original para reatribuição em caso de reabertura
    original_judge_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    # Data/hora agendada para o sorteio (próximo dia útil às 10:00)
    lottery_scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # Data/hora em que o processo foi atribuído a um juiz
    assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # Quem cadastrou o processo
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relacionamentos para facilitar o acesso aos objetos relacionados
    person: Mapped["Person"] = relationship("Person")  # noqa: F821
    assigned_judge: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User", foreign_keys=[assigned_judge_id]
    )
    temp_judge: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User", foreign_keys=[temp_judge_id]
    )
    original_judge: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User", foreign_keys=[original_judge_id]
    )
    created_by: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[created_by_id]
    )
