"""
Ponto de entrada da aplicação SorteiaPro.

Configura:
- Instância FastAPI com metadados para o Swagger UI
- Lifespan (inicialização e encerramento do scheduler)
- Registro de todos os routers
- Middleware CORS (configurado para desenvolvimento)
- Rota de healthcheck em /health
- StaticFiles: serve o frontend SPA em /app
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.jobs.scheduler import lifespan
from app.routers import auth, users, processes, conflicts, audit, persons, lottery_state

# ─── Criação da aplicação ─────────────────────────────────────────────────────
app = FastAPI(
    title="SorteiaPro — Sistema de Sorteio do Tribunal Regional",
    description=(
        "Backend completo para gerenciamento de processos judiciais com "
        "sorteio automático de juízes, controle de conflitos de interesse "
        "e auditoria completa de todas as ações.\n\n"
        "**Usuários de teste após seed.py:**\n"
        "- TI: `ti@tribunal.gov.br` / `Admin@2025`\n"
        "- Juiz: `judge01@tribunal.gov.br` / `Judge@2025`\n"
        "- Assessor: `assessor01@tribunal.gov.br` / `Assessor@2025`\n"
        "- Assistente: `assistente01@tribunal.gov.br` / `Assist@2025`\n\n"
        "**Como autenticar no Swagger:** clique em 'Authorize' e informe "
        "email no campo `username` e a senha no campo `password`."
    ),
    version="1.0.0",
    contact={
        "name": "Setor de TI — Tribunal Regional",
        "email": "ti@tribunal.gov.br",
    },
    lifespan=lifespan,  # Conecta o scheduler ao ciclo de vida da aplicação
    docs_url="/docs",   # Swagger UI disponível em /docs
    redoc_url="/redoc", # ReDoc disponível em /redoc
)

# ─── Middleware CORS ───────────────────────────────────────────────────────────
# Em produção, substitua "*" pelos domínios permitidos do front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers da API ───────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(processes.router)
app.include_router(conflicts.router)
app.include_router(audit.router)
app.include_router(persons.router)
app.include_router(lottery_state.router)


# ─── Healthcheck ──────────────────────────────────────────────────────────────
@app.get(
    "/health",
    tags=["Sistema"],
    summary="Verificar saúde da aplicação",
    description="Retorna status 200 se a aplicação estiver funcionando corretamente.",
)
async def healthcheck():
    """Endpoint simples para monitoramento e balanceadores de carga."""
    return {"status": "ok", "sistema": "SorteiaPro"}


# ─── Frontend SPA ─────────────────────────────────────────────────────────────
# Serve os arquivos estáticos do frontend.
# DEVE ficar DEPOIS das rotas da API para não interceptar /health, /docs, etc.
# Acesse em: http://localhost:8000/app/
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/app", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
