"""
Modelo SQLAlchemy para Auditoria do sistema.

AuditLog é APPEND-ONLY — nunca deve ser alterado ou deletado.
Registra todas as ações relevantes: sorteios, atribuições, conflitos, logins, etc.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    # Quem executou a ação (pode ser None para ações automáticas do scheduler)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    # Descrição da ação (ex: "LOTTERY_SUCCESS", "CONFLICT_REFUSED", "LOGIN")
    action: Mapped[str] = mapped_column(String(100), nullable=False)

    # Tipo de entidade afetada (ex: "process", "user", "conflict")
    entity: Mapped[str] = mapped_column(String(50), nullable=False)

    # ID da entidade afetada (como string para suportar qualquer tipo)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Dados adicionais em formato livre (ex: juiz sorteado, motivo da recusa)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user: Mapped["User"] = relationship("User")  # noqa: F821
