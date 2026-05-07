"""
Configurações globais da aplicação.

Usa pydantic-settings para carregar variáveis do arquivo .env automaticamente.
Por padrão, usa SQLite para facilitar o desenvolvimento/teste local.
Para produção, altere para PostgreSQL no arquivo .env.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ─── Banco de dados ───────────────────────────────────────────────────────
    # Padrão: SQLite (sem precisar instalar PostgreSQL para testar)
    # Para produção: postgresql+asyncpg://user:password@localhost:5432/sorteiapro
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./sorteiapro.db",
        description="URL de conexão async. SQLite para dev, PostgreSQL para produção."
    )
    # URL síncrona para o Alembic rodar migrations
    SYNC_DATABASE_URL: str = Field(
        default="sqlite:///./sorteiapro.db",
        description="URL síncrona para o Alembic gerar/aplicar migrations."
    )

    # ─── Segurança / JWT ──────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="troque-esta-chave-segura-em-producao",
        description="Chave secreta para assinar os tokens JWT"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="Algoritmo de assinatura do JWT"
    )
    ACCESS_TOKEN_EXPIRE_HOURS: int = Field(
        default=8,
        description="Tempo de expiração do token em horas"
    )

    # ─── Upload de arquivos ───────────────────────────────────────────────────
    UPLOAD_DIR: str = Field(
        default="./uploads",
        description="Diretório onde os documentos de conflito serão salvos"
    )

    # ─── Ambiente ─────────────────────────────────────────────────────────────
    ENVIRONMENT: str = Field(
        default="development",
        description="Ambiente atual: development | production"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância única importada pelo resto da aplicação
settings = Settings()
