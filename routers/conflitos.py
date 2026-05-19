import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from auth import usuario_atual, hash_senha
from models import (
    ConflitoInteresse, Processo, Usuario, PerfilEnum, Juiz, TipoJuizEnum,
    PrioridadeCompensacao, AcessoJuizExterno, LogSorteio, MotivoLogEnum,
    StatusProcessoEnum,
)
from schemas import ConflitoOut, DesignarJuizExternoIn

router = APIRouter(prefix="/conflitos", tags=["conflitos"])

DOCS_DIR = "./documentos_conflito"
os.makedirs(DOCS_DIR, exist_ok=True)


@router.post("/", response_model=ConflitoOut)
def registrar_conflito(
    processo_id: int = Form(...),
    justificativa: str = Form(...),
    documento: UploadFile = File(...),
    db: Session = Depends(get_db),
    u: Usuario = Depends(usuario_atual),
):
    if u.perfil != PerfilEnum.JUIZ:
        raise HTTPException(403, "Apenas JUIZ pode registrar conflito")
    j = db.query(Juiz).filter(Juiz.usuario_id == u.id).first()
    if not j:
        raise HTTPException(400, "Usuário não é juiz")
    p = db.query(Processo).filter(Processo.id == processo_id).first()
    if not p:
        raise HTTPException(404, "Processo não encontrado")
    if p.juiz_id != j.id:
        raise HTTPException(403, "Juiz só pode registrar conflito em processo dele")

    ext = os.path.splitext(documento.filename or "")[1] or ".bin"
    fname = f"{uuid.uuid4().hex}{ext}"
    fpath = os.path.join(DOCS_DIR, fname)
    with open(fpath, "wb") as f:
        f.write(documento.file.read())

    c = ConflitoInteresse(processo_id=p.id, juiz_id=j.id,
                          justificativa=justificativa, documento_path=fpath)
    db.add(c)
    # registra que esse juiz ficou devendo um processo desse nivel
    db.add(PrioridadeCompensacao(juiz_id=j.id, nivel=p.nivel))
    # processo volta pra fila
    p.juiz_id = None
    p.status = StatusProcessoEnum.PENDENTE
    p.sorteado_em = None
    db.commit(); db.refresh(c)
    return c


@router.post("/designar-juiz-externo")
def designar_juiz_externo(body: DesignarJuizExternoIn,
                          db: Session = Depends(get_db),
                          u: Usuario = Depends(usuario_atual)):
    if u.perfil != PerfilEnum.TI:
        raise HTTPException(403, "Apenas TI pode designar juiz externo")
    p = db.query(Processo).filter(Processo.id == body.processo_id).first()
    if not p:
        raise HTTPException(404, "Processo não encontrado")
    if db.query(Usuario).filter(Usuario.login == body.login).first():
        raise HTTPException(400, "Login já existe")
    novo_u = Usuario(login=body.login, senha_hash=hash_senha(body.senha),
                     nome=body.nome, perfil=PerfilEnum.JUIZ_EXTERNO, ativo=True)
    db.add(novo_u); db.flush()
    novo_j = Juiz(usuario_id=novo_u.id, tipo=TipoJuizEnum.EXTERNO, ativo=True)
    db.add(novo_j); db.flush()
    db.add(AcessoJuizExterno(juiz_externo_id=novo_j.id, processo_id=p.id))
    p.juiz_id = novo_j.id
    p.status = StatusProcessoEnum.SORTEADO
    p.sorteado_em = datetime.utcnow()
    db.add(LogSorteio(processo_id=p.id, juiz_id=novo_j.id,
                      motivo=MotivoLogEnum.DESIGNACAO_EXTERNA,
                      detalhes="Designação manual para juiz externo"))
    db.commit()
    return {"ok": True, "juiz_externo_id": novo_j.id, "usuario_id": novo_u.id}


@router.get("/")
def listar(db: Session = Depends(get_db), u: Usuario = Depends(usuario_atual)):
    if u.perfil not in (PerfilEnum.TI, PerfilEnum.JUIZ):
        raise HTTPException(403, "Acesso negado")
    items = db.query(ConflitoInteresse).order_by(ConflitoInteresse.id.desc()).all()
    return [
        {"id": c.id, "processo_id": c.processo_id, "juiz_id": c.juiz_id,
         "justificativa": c.justificativa, "registrado_em": c.registrado_em}
        for c in items
    ]
