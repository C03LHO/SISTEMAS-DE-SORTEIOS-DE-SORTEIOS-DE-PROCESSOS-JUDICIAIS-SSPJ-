"""
Configurações globais da aplicação.

Usa pydantic-settings para carregar variáveis do arquivo .env automaticamente.
Todas as variáveis de ambiente obrigatórias são declaradas aqui.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ─── Banco de dados ───────────────────────────────────────────────────────
    # URL async (asyncpg) usada pela aplicação em tempo de execução
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/sorteiapro",
        description="URL de conexão async com o PostgreSQL"
    )
    # URL síncrona (psycopg2) usada pelo Alembic para rodar migrations
    SYNC_DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/sorteiapro",
        description="URL de conexão síncrona para o Alembic"
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
        # Carrega variáveis do arquivo .env na raiz do projeto
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância única importada pelo resto da aplicação
settings = Settings()
