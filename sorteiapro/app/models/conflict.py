"""
Modelos SQLAlchemy para Conflitos de Interesse.

JudgeConflict: relação de proximidade pré-cadastrada entre juiz e pessoa.
  - Usada para filtrar juízes inelegíveis ANTES do sorteio.

ConflictRecord: registro de recusa formal de um juiz durante o sorteio.
  - Criado quando o juiz recusa o processo com justificativa + documento.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class JudgeConflict(Base):
    """Relação de proximidade pré-cadastrada: juiz X pessoa."""

    __tablename__ = "judge_conflicts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    judge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("persons.id"),
        nullable=False
    )
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    judge: Mapped["User"] = relationship("User", foreign_keys=[judge_id])  # noqa: F821
    person: Mapped["Person"] = relationship("Person")  # noqa: F821


class ConflictRecord(Base):
    """Registro de recusa formal de um juiz durante o processo de sorteio."""

    __tablename__ = "conflict_records"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    process_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("processes.id"),
        nullable=False
    )
    judge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    # Texto explicando o motivo da recusa
    justification: Mapped[str] = mapped_column(Text, nullable=False)

    # Caminho do arquivo salvo em /uploads/{process_id}/
    document_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    judge: Mapped["User"] = relationship("User", foreign_keys=[judge_id])  # noqa: F821
    process: Mapped["Process"] = relationship("Process")  # noqa: F821
