"""
Configuração do banco de dados assíncrono.

Cria:
  - engine: conexão async com PostgreSQL (asyncpg) ou SQLite (aiosqlite)
  - AsyncSessionLocal: fábrica de sessões assíncronas
  - Base: classe base para todos os modelos SQLAlchemy

Detecção automática de SQLite:
  - Usa StaticPool (conexão única em memória/arquivo) para evitar problemas de
    thread com SQLite
  - Desativa pool_pre_ping (não suportado pelo aiosqlite)
  - Passa check_same_thread=False nos connect_args
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# ─── Detecção de banco de dados ───────────────────────────────────────────────
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# ─── Kwargs do engine (diferem entre SQLite e PostgreSQL) ────────────────────
_engine_kwargs: dict = {
    "echo": (settings.ENVIRONMENT == "development"),
}

if _is_sqlite:
    # SQLite precisa de StaticPool para funcionar corretamente com asyncio
    # e check_same_thread=False para permitir uso em múltiplas coroutines
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    _engine_kwargs["poolclass"] = StaticPool
else:
    # PostgreSQL: verifica a conexão antes de usar (evita erros de timeout)
    _engine_kwargs["pool_pre_ping"] = True

# ─── Engine assíncrono ────────────────────────────────────────────────────────
engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

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
