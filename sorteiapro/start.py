"""
start.py — Inicializador de desenvolvimento para SorteiaPro com SQLite

Executa na ordem:
  1. Cria as tabelas no banco (CREATE TABLE IF NOT EXISTS)
  2. Popula com dados iniciais (seed)
  3. Inicia o servidor Uvicorn

Como usar:
  python start.py

Depois acesse:
  API:      http://localhost:8000/docs
  Frontend: http://localhost:8000/app/

Credenciais padrão:
  TI:         ti@tribunal.gov.br         / Admin@2025
  Juiz 01:    judge01@tribunal.gov.br    / Judge@2025
  Assessor:   assessor01@tribunal.gov.br / Assessor@2025
  Assistente: assistente01@tribunal.gov.br / Assist@2025
"""

import asyncio
import sys
import os

# Garante que importações locais funcionem
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def init_db():
    """Cria todas as tabelas e executa o seed."""
    # Importa o engine e a Base DEPOIS de garantir que o path está certo
    from app.core.database import engine, Base

    # Importa todos os modelos para que o SQLAlchemy os conheça
    import app.models  # noqa: F401 — registra todos os modelos em Base.metadata

    print("─" * 50)
    print("  Criando tabelas no banco de dados…")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ Tabelas prontas")

    # Executa o seed
    from seed import seed
    await seed()


def main():
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║         SorteiaPro — Modo Desenvolvimento        ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    # Passo 1 & 2: tabelas + seed
    asyncio.run(init_db())

    # Passo 3: inicia o servidor
    print()
    print("─" * 50)
    print("  Iniciando servidor Uvicorn…")
    print("  API:      http://localhost:8000/docs")
    print("  Frontend: http://localhost:8000/app/")
    print("  Parar:    Ctrl+C")
    print("─" * 50)
    print()

    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,          # reinicia ao salvar arquivos .py
        reload_dirs=["app"],
    )


if __name__ == "__main__":
    main()
