"""Algoritmo de sorteio."""
import random
from datetime import datetime
from sqlalchemy.orm import Session
from models import (
    Processo, Juiz, ConflitoInteresse, PrioridadeCompensacao, LogSorteio,
    StatusProcessoEnum, MotivoLogEnum, TipoJuizEnum,
)


def _juizes_principais_ativos(db: Session) -> list[Juiz]:
    return (
        db.query(Juiz)
        .filter(Juiz.tipo == TipoJuizEnum.PRINCIPAL, Juiz.ativo == True)
        .order_by(Juiz.id)
        .all()
    )


def _ultimo_complexo(db: Session) -> int | None:
    # pega o ultimo juiz que recebeu um processo complexo
    log = (
        db.query(LogSorteio)
        .join(Processo, Processo.id == LogSorteio.processo_id)
        .filter(Processo.nivel == 3,
                LogSorteio.motivo.in_([MotivoLogEnum.SORTEIO_NORMAL,
                                       MotivoLogEnum.PRIORIDADE_COMPENSACAO]))
        .order_by(LogSorteio.id.desc())
        .first()
    )
    return log.juiz_id if log else None


def _rodada_atual_complexos(db: Session, total_juizes: int) -> set[int]:
    # juizes que ja receberam complexo na rodada atual
    # quando os 8 receberem, zera e comeca de novo
    logs = (
        db.query(LogSorteio)
        .join(Processo, Processo.id == LogSorteio.processo_id)
        .filter(Processo.nivel == 3,
                LogSorteio.motivo.in_([MotivoLogEnum.SORTEIO_NORMAL,
                                       MotivoLogEnum.PRIORIDADE_COMPENSACAO]))
        .order_by(LogSorteio.id.asc())
        .all()
    )
    rodada: set[int] = set()
    for lg in logs:
        rodada.add(lg.juiz_id)
        if len(rodada) >= total_juizes:
            rodada = set()
    return rodada


def executar_sorteio(db: Session) -> list[LogSorteio]:
    logs_criados: list[LogSorteio] = []
    try:
        pendentes = (
            db.query(Processo)
            .filter(Processo.status == StatusProcessoEnum.PENDENTE)
            .order_by(Processo.criado_em.asc(), Processo.id.asc())
            .all()
        )
        principais = _juizes_principais_ativos(db)
        total = len(principais)

        for proc in pendentes:
            # 1) reabertura volta direto pro juiz anterior
            if proc.reaberto and proc.juiz_anterior_id:
                jant = db.query(Juiz).filter(Juiz.id == proc.juiz_anterior_id,
                                             Juiz.ativo == True).first()
                if jant:
                    proc.juiz_id = jant.id
                    proc.status = StatusProcessoEnum.SORTEADO
                    proc.sorteado_em = datetime.utcnow()
                    log = LogSorteio(processo_id=proc.id, juiz_id=jant.id,
                                     motivo=MotivoLogEnum.REABERTURA,
                                     detalhes="Reabertura: retorno ao juiz anterior")
                    db.add(log)
                    db.flush()
                    logs_criados.append(log)
                    continue

            # 2) tira da lista os juizes com conflito declarado
            conflitos_jids = {
                c.juiz_id for c in db.query(ConflitoInteresse)
                .filter(ConflitoInteresse.processo_id == proc.id).all()
            }
            elegiveis = [j for j in principais if j.id not in conflitos_jids]
            if not elegiveis:
                proc.status = StatusProcessoEnum.AGUARDANDO_JUIZ_EXTERNO
                continue

            # 3) complexo: nao pode ser o ultimo, e tem que respeitar a rodada
            if proc.nivel == 3:
                ultimo = _ultimo_complexo(db)
                if ultimo is not None and len(elegiveis) > 1:
                    elegiveis = [j for j in elegiveis if j.id != ultimo]
                rodada = _rodada_atual_complexos(db, total)
                restantes = [j for j in elegiveis if j.id not in rodada]
                if not restantes:
                    restantes = elegiveis
                elegiveis = restantes

            # 4) quem ficou devendo (compensacao) tem prioridade
            elegiveis_ids = {j.id for j in elegiveis}
            prio = (
                db.query(PrioridadeCompensacao)
                .filter(PrioridadeCompensacao.consumida == False,
                        PrioridadeCompensacao.nivel == proc.nivel,
                        PrioridadeCompensacao.juiz_id.in_(elegiveis_ids))
                .order_by(PrioridadeCompensacao.criado_em.asc(),
                          PrioridadeCompensacao.id.asc())
                .first()
            )
            if prio:
                prio.consumida = True
                escolhido_id = prio.juiz_id
                motivo = MotivoLogEnum.PRIORIDADE_COMPENSACAO
                detalhes = f"Compensação por conflito prévio (nível {proc.nivel})"
            else:
                # 5) senao, sorteia
                escolhido = random.choice(elegiveis)
                escolhido_id = escolhido.id
                motivo = MotivoLogEnum.SORTEIO_NORMAL
                detalhes = f"Sorteio aleatório (nível {proc.nivel})"

            proc.juiz_id = escolhido_id
            proc.status = StatusProcessoEnum.SORTEADO
            proc.sorteado_em = datetime.utcnow()
            log = LogSorteio(processo_id=proc.id, juiz_id=escolhido_id,
                             motivo=motivo, detalhes=detalhes)
            db.add(log)
            db.flush()
            logs_criados.append(log)

        db.commit()
        for lg in logs_criados:
            db.refresh(lg)
        return logs_criados
    except Exception:
        db.rollback()
        raise
