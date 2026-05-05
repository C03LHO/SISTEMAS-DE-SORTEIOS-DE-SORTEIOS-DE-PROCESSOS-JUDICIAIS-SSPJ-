"""
Agendador de tarefas — APScheduler com BackgroundScheduler.

O scheduler é iniciado e parado usando o padrão `lifespan` do FastAPI,
que substitui os antigos eventos @app.on_event("startup"/"shutdown").

Tarefa agendada:
  - run_pending_lotteries: roda de seg a sex às 10:00 (horário de Brasília)
    Busca todos os processos com status PENDING_LOTTERY ou REOPENED cujo
    lottery_scheduled_at já passou e executa o sorteio para cada um.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Cria o scheduler configurado para o fuso horário de Brasília
scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")


def run_pending_lotteries() -> None:
    """
    Função executada pelo APScheduler em uma thread separada.

    Como o FastAPI é assíncrono mas o APScheduler é síncrono, usamos
    asyncio.run() para criar um novo event loop e executar as corrotinas.

    Processo:
    1. Abre uma sessão assíncrona do banco
    2. Busca todos os processos elegíveis (aguardando sorteio, data chegou)
    3. Executa run_lottery para cada um
    """
    # Importações locais para evitar import circular na inicialização do módulo
    from app.core.database import AsyncSessionLocal
    from app.services.lottery_engine import run_lottery
    from app.models.process import Process, ProcessStatus
    from sqlalchemy import select, or_

    async def _executar_sorteios() -> None:
        """Corrotina interna que faz o trabalho real."""
        async with AsyncSessionLocal() as db:
            agora = datetime.utcnow()

            # Busca processos que estão aguardando sorteio E já passaram da hora
            result = await db.execute(
                select(Process).where(
                    or_(
                        Process.status == ProcessStatus.PENDING_LOTTERY.value,
                        Process.status == ProcessStatus.REOPENED.value,
                    ),
                    Process.lottery_scheduled_at <= agora,
                )
            )
            processos = result.scalars().all()

            if processos:
                logger.info(f"[Scheduler] Executando sorteio para {len(processos)} processo(s).")
            else:
                logger.info("[Scheduler] Nenhum processo pendente para sorteio.")

            for processo in processos:
                try:
                    await run_lottery(processo.id, db)
                    logger.info(f"[Scheduler] Sorteio concluído: processo {processo.process_number}")
                except Exception as e:
                    logger.error(
                        f"[Scheduler] Erro no sorteio do processo {processo.process_number}: {e}",
                        exc_info=True,
                    )

    # Cria e executa um novo event loop síncrono para a corrotina
    asyncio.run(_executar_sorteios())


@asynccontextmanager
async def lifespan(app):
    """
    Gerenciador de ciclo de vida do FastAPI.

    Código ANTES do `yield` → executado na inicialização do servidor.
    Código APÓS o `yield`  → executado no encerramento do servidor.
    """
    # ── Inicialização ──────────────────────────────────────────────────────
    scheduler.add_job(
        func=run_pending_lotteries,
        trigger=CronTrigger(
            day_of_week="mon-fri",  # segunda a sexta
            hour=10,
            minute=0,
            timezone="America/Sao_Paulo",
        ),
        id="daily_lottery",
        replace_existing=True,  # evita duplicatas ao reiniciar o servidor
    )
    scheduler.start()
    logger.info("[Scheduler] APScheduler iniciado. Sorteios agendados para seg-sex às 10:00.")

    yield  # servidor rodando

    # ── Encerramento ───────────────────────────────────────────────────────
    scheduler.shutdown(wait=False)
    logger.info("[Scheduler] APScheduler encerrado.")
