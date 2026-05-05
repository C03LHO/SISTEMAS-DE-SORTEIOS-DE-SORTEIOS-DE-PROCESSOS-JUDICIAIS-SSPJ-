"""
Modelo SQLAlchemy para Usuários do sistema.

Roles disponíveis:
  - TI: administrador total do sistema
  - JUDGE: juiz titular
  - ASSESSOR: assessor vinculado a um juiz
  - ASSISTANT: assistente que cadastra processos
  - TEMP_JUDGE: juiz temporário (acesso restrito a um processo)
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    TI = "TI"
    JUDGE = "JUDGE"
    ASSESSOR = "ASSESSOR"
    ASSISTANT = "ASSISTANT"
    TEMP_JUDGE = "TEMP_JUDGE"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Assessores são vinculados a um juiz específico (nullable para outros roles)
    judge_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
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

    # Auto-referência: assessor → juiz
    judge: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side="User.id",
        foreign_keys=[judge_id]
    )
