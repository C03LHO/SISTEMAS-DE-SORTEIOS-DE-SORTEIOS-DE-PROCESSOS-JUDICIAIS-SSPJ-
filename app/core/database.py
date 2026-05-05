"""
Configuração do banco de dados assíncrono.

Cria:
  - engine: conexão async com PostgreSQL via asyncpg
  - AsyncSessionLocal: fábrica de sessões assíncronas
  - Base: classe base para todos os modelos SQLAlchemy
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ─── Engine assíncrono ────────────────────────────────────────────────────────
# echo=True imprime as queries SQL no console (útil para desenvolvimento)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"),
    pool_pre_ping=True,  # verifica a conexão antes de usar (evita erros de timeout)
)

# ─── Fábrica de sessões ───────────────────────────────────────────────────────
# expire_on_commit=False: objetos continuam acessíveis após o commit sem re-query
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─── Base declarativa ─────────────────────────────────────────────────────────
# Todos os modelos herdam desta classe para o Alembic detectá-los
class Base(DeclarativeBase):
    pass
