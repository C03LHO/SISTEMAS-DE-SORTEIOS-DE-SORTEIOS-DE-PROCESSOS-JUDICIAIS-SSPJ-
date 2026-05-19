from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date
import holidays
from database import SessionLocal
from sorteio import executar_sorteio

_TZ = "America/Belem"
_BR_HOLIDAYS = holidays.country_holidays("BR")


def _job():
    hoje = date.today()
    # so roda em dia util (seg a sex) e fora de feriado
    if hoje.weekday() >= 5 or hoje in _BR_HOLIDAYS:
        return
    db = SessionLocal()
    try:
        executar_sorteio(db)
    finally:
        db.close()


def iniciar_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone=_TZ)
    sched.add_job(_job, CronTrigger(hour=10, minute=0, timezone=_TZ),
                  id="sorteio_diario", replace_existing=True)
    sched.start()
    return sched
