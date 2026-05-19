import random
from sorteio import executar_sorteio
import models
from tests.conftest import criar_juizes, criar_assistente, criar_pessoa, criar_processo


def test_reabertura_volta_para_juiz_anterior(db):
    juizes = criar_juizes(db)
    a = criar_assistente(db); pe = criar_pessoa(db)
    p = criar_processo(db, pe, a, nivel=2)
    p.reaberto = True
    p.juiz_anterior_id = juizes[3].id
    db.commit()
    executar_sorteio(db)
    db.refresh(p)
    assert p.juiz_id == juizes[3].id
    assert p.status == models.StatusProcessoEnum.SORTEADO


def test_complexo_nao_repete_consecutivo(db):
    random.seed(0)
    juizes = criar_juizes(db)
    a = criar_assistente(db); pe = criar_pessoa(db)
    p1 = criar_processo(db, pe, a, nivel=3, numero="C1")
    db.commit()
    executar_sorteio(db)
    db.refresh(p1)
    primeiro = p1.juiz_id

    p2 = criar_processo(db, pe, a, nivel=3, numero="C2")
    db.commit()
    executar_sorteio(db)
    db.refresh(p2)
    assert p2.juiz_id != primeiro


def test_rodizio_completo_de_complexos(db):
    random.seed(1)
    criar_juizes(db, qtd=8)
    a = criar_assistente(db); pe = criar_pessoa(db)
    procs = []
    for i in range(8):
        procs.append(criar_processo(db, pe, a, nivel=3, numero=f"C{i}"))
    db.commit()
    executar_sorteio(db)
    jids = set()
    for p in procs:
        db.refresh(p)
        jids.add(p.juiz_id)
    assert len(jids) == 8  # cada juiz recebeu exatamente um complexo


def test_conflito_remove_juiz_dos_elegiveis(db):
    random.seed(2)
    juizes = criar_juizes(db)
    a = criar_assistente(db); pe = criar_pessoa(db)
    p = criar_processo(db, pe, a, nivel=2)
    # Registra conflito para 7 dos 8 — só sobra um.
    for j in juizes[:7]:
        db.add(models.ConflitoInteresse(processo_id=p.id, juiz_id=j.id,
                                         justificativa="x", documento_path="x"))
    db.commit()
    executar_sorteio(db)
    db.refresh(p)
    assert p.juiz_id == juizes[7].id


def test_prioridade_compensacao_consumida_no_proximo_do_mesmo_nivel(db):
    random.seed(3)
    juizes = criar_juizes(db)
    a = criar_assistente(db); pe = criar_pessoa(db)
    # Juiz 0 tem prioridade nível 2.
    db.add(models.PrioridadeCompensacao(juiz_id=juizes[0].id, nivel=2))
    p = criar_processo(db, pe, a, nivel=2)
    db.commit()
    executar_sorteio(db)
    db.refresh(p)
    assert p.juiz_id == juizes[0].id
    prio = db.query(models.PrioridadeCompensacao).first()
    assert prio.consumida is True


def test_conflito_de_todos_marca_aguardando_juiz_externo(db):
    juizes = criar_juizes(db)
    a = criar_assistente(db); pe = criar_pessoa(db)
    p = criar_processo(db, pe, a, nivel=1)
    for j in juizes:
        db.add(models.ConflitoInteresse(processo_id=p.id, juiz_id=j.id,
                                         justificativa="x", documento_path="x"))
    db.commit()
    executar_sorteio(db)
    db.refresh(p)
    assert p.status == models.StatusProcessoEnum.AGUARDANDO_JUIZ_EXTERNO


def test_basico_e_intermediario_podem_repetir(db):
    random.seed(4)
    juizes = criar_juizes(db)
    a = criar_assistente(db); pe = criar_pessoa(db)
    # 20 processos de nível 1: 8 juízes → pelos menos um juiz vai receber 2+.
    for i in range(20):
        criar_processo(db, pe, a, nivel=1, numero=f"B{i}")
    db.commit()
    executar_sorteio(db)
    distrib = {}
    for p in db.query(models.Processo).all():
        distrib[p.juiz_id] = distrib.get(p.juiz_id, 0) + 1
    assert max(distrib.values()) >= 2  # houve repetição — permitido para nível 1
