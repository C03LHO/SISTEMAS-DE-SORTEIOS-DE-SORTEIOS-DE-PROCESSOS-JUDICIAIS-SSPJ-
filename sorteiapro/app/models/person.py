"""
Modelo SQLAlchemy para Pessoas (partes dos processos judiciais).

Uma Person é a parte interessada no processo (CPF ou CNPJ).
Os juízes podem ter conflito de interesse com determinadas Persons.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentType(str, Enum):
    CPF = "CPF"
    CNPJ = "CNPJ"


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Documento único da pessoa (CPF ou CNPJ sem formatação)
    document: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )
    document_type: Mapped[str] = mapped_column(
        String(5),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
