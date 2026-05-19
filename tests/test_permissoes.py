import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["DISABLE_SCHEDULER"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database, models
from auth import hash_senha


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "t.db"
    url = f"sqlite:///{db_file}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    SL = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", SL)
    models.Base.metadata.create_all(bind=engine)

    # Seed mínimo.
    s = SL()
    ti = models.Usuario(login="ti", senha_hash=hash_senha("ti"), nome="TI",
                        perfil=models.PerfilEnum.TI, ativo=True)
    s.add(ti)
    juizes = []
    for i in range(1, 3):
        u = models.Usuario(login=f"juiz{i}", senha_hash=hash_senha("x"),
                           nome=f"J{i}", perfil=models.PerfilEnum.JUIZ, ativo=True)
        s.add(u); s.flush()
        j = models.Juiz(usuario_id=u.id, tipo=models.TipoJuizEnum.PRINCIPAL, ativo=True)
        s.add(j); s.flush()
        juizes.append((u, j))
    assess_u = models.Usuario(login="assess1", senha_hash=hash_senha("x"), nome="A1",
                              perfil=models.PerfilEnum.ASSESSOR, ativo=True)
    s.add(assess_u); s.flush()
    assess = models.Assessor(usuario_id=assess_u.id, juiz_id=juizes[0][1].id)
    s.add(assess); s.flush()
    asst = models.Usuario(login="asst1", senha_hash=hash_senha("x"), nome="As1",
                          perfil=models.PerfilEnum.ASSISTENTE, ativo=True)
    s.add(asst); s.flush()
    pe = models.Pessoa(tipo=models.TipoPessoaEnum.PF, documento="11111111111", nome="P")
    s.add(pe); s.flush()
    proc_sorteado = models.Processo(numero="S1", descricao="d", nivel=1,
                                    pessoa_id=pe.id, status=models.StatusProcessoEnum.SORTEADO,
                                    juiz_id=juizes[0][1].id, cadastrado_por=asst.id)
    proc_outro = models.Processo(numero="S2", descricao="d", nivel=1,
                                 pessoa_id=pe.id, status=models.StatusProcessoEnum.SORTEADO,
                                 juiz_id=juizes[1][1].id, cadastrado_por=asst.id)
    proc_meu_asst = models.Processo(numero="A1", descricao="d", nivel=1,
                                    pessoa_id=pe.id, status=models.StatusProcessoEnum.SORTEADO,
                                    juiz_id=juizes[0][1].id, cadastrado_por=asst.id)
    s.add_all([proc_sorteado, proc_outro, proc_meu_asst]); s.commit()

    import main
    monkeypatch.setattr(main, "engine", engine)

    # Substitui get_db nos routers.
    def override_get_db():
        d = SL()
        try: yield d
        finally: d.close()
    from database import get_db
    main.app.dependency_overrides[get_db] = override_get_db

    c = TestClient(main.app)
    c.ids = {
        "juiz1_id": juizes[0][1].id,
        "assess_id": assess.id,
        "proc_sorteado_id": proc_sorteado.id,
        "proc_outro_id": proc_outro.id,
        "proc_meu_asst_id": proc_meu_asst.id,
    }
    return c


def _login(c, login, senha):
    r = c.post("/auth/login", json={"login": login, "senha": senha})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token): return {"Authorization": f"Bearer {token}"}


def test_assistente_nao_ve_status_do_processo(client):
    tok = _login(client, "asst1", "x")
    r = client.get("/processos/", headers=_auth(tok))
    assert r.status_code == 200
    for p in r.json():
        assert p["status"] in ("cadastrado", "em processamento")
        assert "juiz_id" not in p
        assert "sorteado_em" not in p


def test_assessor_so_ve_processos_do_seu_juiz(client):
    tok = _login(client, "assess1", "x")
    r = client.get("/processos/", headers=_auth(tok))
    assert r.status_code == 200
    juiz1 = client.ids["juiz1_id"]
    for p in r.json():
        assert p["juiz_id"] == juiz1


def test_assessor_nao_edita_sem_autorizacao(client):
    tok = _login(client, "assess1", "x")
    pid = client.ids["proc_sorteado_id"]
    r = client.patch(f"/processos/{pid}", json={"descricao": "nova"}, headers=_auth(tok))
    assert r.status_code == 403


def test_juiz_externo_so_ve_seu_processo(client):
    # Cria juiz externo via designação manual feita pelo TI.
    ti_tok = _login(client, "ti", "ti")
    # Coloca um processo em AGUARDANDO_JUIZ_EXTERNO simulando designação.
    pid = client.ids["proc_outro_id"]
    r = client.post("/conflitos/designar-juiz-externo", headers=_auth(ti_tok),
                    json={"processo_id": pid, "login": "extjuiz", "senha": "x", "nome": "Ext"})
    assert r.status_code == 200, r.text
    tok = _login(client, "extjuiz", "x")
    r = client.get("/processos/", headers=_auth(tok))
    assert r.status_code == 200
    procs = r.json()
    assert len(procs) == 1
    assert procs[0]["id"] == pid


def test_juiz_nao_cadastra_usuario(client):
    tok = _login(client, "juiz1", "x")
    r = client.post("/usuarios/", headers=_auth(tok),
                    json={"login": "x", "senha": "x", "nome": "X", "perfil": "TI"})
    assert r.status_code == 403
