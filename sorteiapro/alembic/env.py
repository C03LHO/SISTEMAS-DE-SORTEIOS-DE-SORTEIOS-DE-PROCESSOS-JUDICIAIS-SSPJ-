"""
Configuração do Alembic para geração e execução de migrations.

Este arquivo é executado pelo Alembic ao rodar:
  alembic revision --autogenerate -m "descrição"
  alembic upgrade head

Importante:
- Usa a URL SÍNCRONA (psycopg2) porque o Alembic não suporta async nativamente
- Importa todos os modelos para que o autogenerate detecte as tabelas
- Lê a DATABASE_URL do arquivo .env via python-dotenv
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# ─── Configuração do Alembic ──────────────────────────────────────────────────
config = context.config

# Configura o logging do Alembic a partir do alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Substitui a URL do alembic.ini pela variável de ambiente
# (usa URL síncrona — psycopg2, não asyncpg)
sync_url = os.getenv("SYNC_DATABASE_URL", "postgresql://user:password@localhost:5432/sorteiapro")
config.set_main_option("sqlalchemy.url", sync_url)

# ─── Importação de todos os modelos ───────────────────────────────────────────
# OBRIGATÓRIO: sem estas importações, o autogenerate não detecta as tabelas
from app.core.database import Base  # noqa: E402 — Base deve ser importada primeiro
import app.models  # noqa: E402 — importa todos os modelos via __init__.py

target_metadata = Base.metadata


# ─── Modo offline (sem conexão live com o banco) ───────────────────────────────
def run_migrations_offline() -> None:
    """
    Gera o SQL das migrations sem conectar ao banco.
    Útil para revisar o SQL antes de executar.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ─── Modo online (conecta ao banco e executa) ─────────────────────────────────
def run_migrations_online() -> None:
    """
    Executa as migrations diretamente no banco de dados.
    Usado pelo comando `alembic upgrade head`.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # sem pooling para migrations (evita conexões penduradas)
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ─── Execução ─────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
