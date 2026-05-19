import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["SORTEIO_DB_URL"] = "sqlite:///:memory:"
os.environ["DISABLE_SCHEDULER"] = "1"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database
import models
from auth import hash_senha


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    database.engine = engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database.SessionLocal = SessionLocal
    models.Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def criar_juizes(db, qtd=8):
    juizes = []
    for i in range(1, qtd + 1):
        u = models.Usuario(login=f"j{i}", senha_hash=hash_senha("x"), nome=f"J{i}",
                           perfil=models.PerfilEnum.JUIZ, ativo=True)
        db.add(u); db.flush()
        j = models.Juiz(usuario_id=u.id, tipo=models.TipoJuizEnum.PRINCIPAL, ativo=True)
        db.add(j); db.flush()
        juizes.append(j)
    return juizes


def criar_assistente(db, login="a1"):
    u = models.Usuario(login=login, senha_hash=hash_senha("x"), nome=login,
                       perfil=models.PerfilEnum.ASSISTENTE, ativo=True)
    db.add(u); db.flush()
    return u


def criar_pessoa(db, doc="11111111111"):
    p = models.Pessoa(tipo=models.TipoPessoaEnum.PF, documento=doc, nome="Pessoa Teste")
    db.add(p); db.flush()
    return p


def criar_processo(db, pessoa, assistente, nivel=1, numero="P-001"):
    p = models.Processo(numero=numero, descricao="desc", nivel=nivel,
                        pessoa_id=pessoa.id, status=models.StatusProcessoEnum.PENDENTE,
                        cadastrado_por=assistente.id)
    db.add(p); db.flush()
    return p
