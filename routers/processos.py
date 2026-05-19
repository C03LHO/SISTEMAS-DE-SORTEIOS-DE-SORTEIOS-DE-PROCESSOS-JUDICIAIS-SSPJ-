from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import usuario_atual
from models import (
    Processo, Usuario, PerfilEnum, Juiz, Assessor, AutorizacaoEdicao,
    AcessoJuizExterno, StatusProcessoEnum,
)
from schemas import ProcessoIn, ProcessoOut, ProcessoUpdate, AutorizarEdicaoIn

router = APIRouter(prefix="/processos", tags=["processos"])


def _serializar(p: Processo) -> dict:
    return {
        "id": p.id, "numero": p.numero, "descricao": p.descricao,
        "nivel": p.nivel, "pessoa_id": p.pessoa_id, "status": p.status.value,
        "juiz_id": p.juiz_id, "reaberto": p.reaberto,
        "criado_em": p.criado_em, "sorteado_em": p.sorteado_em,
    }


@router.post("/")
def cadastrar(body: ProcessoIn, db: Session = Depends(get_db),
              u: Usuario = Depends(usuario_atual)):
    if u.perfil != PerfilEnum.ASSISTENTE:
        raise HTTPException(403, "Apenas ASSISTENTE pode cadastrar processo")
    if db.query(Processo).filter(Processo.numero == body.numero).first():
        raise HTTPException(400, "Número de processo já existe")
    p = Processo(numero=body.numero, descricao=body.descricao, nivel=body.nivel,
                 pessoa_id=body.pessoa_id, cadastrado_por=u.id,
                 status=StatusProcessoEnum.PENDENTE)
    db.add(p); db.commit(); db.refresh(p)
    return _serializar(p)


@router.patch("/{pid}")
def editar(pid: int, body: ProcessoUpdate, db: Session = Depends(get_db),
           u: Usuario = Depends(usuario_atual)):
    p = db.query(Processo).filter(Processo.id == pid).first()
    if not p:
        raise HTTPException(404, "Processo não encontrado")

    if p.status == StatusProcessoEnum.PENDENTE:
        # antes do sorteio so o assistente que cadastrou pode mexer
        if u.perfil != PerfilEnum.ASSISTENTE or p.cadastrado_por != u.id:
            raise HTTPException(403, "Somente o assistente que cadastrou pode editar")
    elif p.status == StatusProcessoEnum.SORTEADO:
        # depois do sorteio, so o assessor do juiz e com autorizacao
        if u.perfil != PerfilEnum.ASSESSOR:
            raise HTTPException(403, "Somente assessor pode editar processo sorteado")
        a = db.query(Assessor).filter(Assessor.usuario_id == u.id).first()
        if not a or a.juiz_id != p.juiz_id:
            raise HTTPException(403, "Assessor não vinculado ao juiz responsável")
        autz = (db.query(AutorizacaoEdicao)
                .filter(AutorizacaoEdicao.processo_id == p.id,
                        AutorizacaoEdicao.assessor_id == a.id,
                        AutorizacaoEdicao.usada == False)
                .order_by(AutorizacaoEdicao.id.desc()).first())
        if not autz:
            raise HTTPException(403, "Sem autorização do juiz para editar este processo")
        autz.usada = True  # autorizacao serve uma vez so
    else:
        raise HTTPException(403, "Edição não permitida neste status")

    if body.descricao is not None:
        p.descricao = body.descricao
    if body.nivel is not None:
        p.nivel = body.nivel
    if body.pessoa_id is not None:
        p.pessoa_id = body.pessoa_id
    db.commit(); db.refresh(p)
    return _serializar(p)


@router.get("/")
def listar(db: Session = Depends(get_db), u: Usuario = Depends(usuario_atual)):
    if u.perfil == PerfilEnum.TI:
        items = db.query(Processo).order_by(Processo.id).all()
        return [_serializar(p) for p in items]
    if u.perfil == PerfilEnum.JUIZ:
        items = db.query(Processo).order_by(Processo.id).all()
        return [_serializar(p) for p in items]
    if u.perfil == PerfilEnum.ASSESSOR:
        a = db.query(Assessor).filter(Assessor.usuario_id == u.id).first()
        if not a:
            return []
        items = db.query(Processo).filter(Processo.juiz_id == a.juiz_id).order_by(Processo.id).all()
        return [_serializar(p) for p in items]
    if u.perfil == PerfilEnum.JUIZ_EXTERNO:
        j = db.query(Juiz).filter(Juiz.usuario_id == u.id).first()
        if not j:
            return []
        acessos = db.query(AcessoJuizExterno).filter(
            AcessoJuizExterno.juiz_externo_id == j.id).all()
        pids = [a.processo_id for a in acessos]
        items = db.query(Processo).filter(Processo.id.in_(pids)).all()
        return [_serializar(p) for p in items]
    if u.perfil == PerfilEnum.ASSISTENTE:
        # assistente nao pode ver juiz nem status real
        items = db.query(Processo).filter(Processo.cadastrado_por == u.id).order_by(Processo.id).all()
        out = []
        for p in items:
            status_publico = "cadastrado" if p.status == StatusProcessoEnum.PENDENTE else "em processamento"
            out.append({
                "id": p.id, "numero": p.numero, "descricao": p.descricao,
                "nivel": p.nivel, "pessoa_id": p.pessoa_id,
                "status": status_publico, "reaberto": p.reaberto,
                "criado_em": p.criado_em,
            })
        return out
    raise HTTPException(403, "Perfil não autorizado")


@router.post("/{pid}/marcar-reabertura")
def marcar_reabertura(pid: int, db: Session = Depends(get_db),
                      u: Usuario = Depends(usuario_atual)):
    if u.perfil not in (PerfilEnum.TI, PerfilEnum.JUIZ):
        raise HTTPException(403, "Acesso negado")
    p = db.query(Processo).filter(Processo.id == pid).first()
    if not p:
        raise HTTPException(404, "Processo não encontrado")
    p.reaberto = True
    p.juiz_anterior_id = p.juiz_id
    p.juiz_id = None
    p.status = StatusProcessoEnum.PENDENTE
    p.sorteado_em = None
    db.commit(); db.refresh(p)
    return _serializar(p)


@router.post("/{pid}/autorizar-edicao")
def autorizar_edicao(pid: int, body: AutorizarEdicaoIn,
                     db: Session = Depends(get_db),
                     u: Usuario = Depends(usuario_atual)):
    if u.perfil != PerfilEnum.JUIZ:
        raise HTTPException(403, "Apenas o juiz pode autorizar edição")
    p = db.query(Processo).filter(Processo.id == pid).first()
    if not p:
        raise HTTPException(404, "Processo não encontrado")
    j = db.query(Juiz).filter(Juiz.usuario_id == u.id).first()
    if not j or p.juiz_id != j.id:
        raise HTTPException(403, "Juiz não é o responsável por este processo")
    a = db.query(Assessor).filter(Assessor.id == body.assessor_id,
                                  Assessor.juiz_id == j.id).first()
    if not a:
        raise HTTPException(400, "Assessor inválido ou não vinculado ao juiz")
    autz = AutorizacaoEdicao(processo_id=p.id, juiz_id=j.id, assessor_id=a.id)
    db.add(autz); db.commit(); db.refresh(autz)
    return {"id": autz.id, "ok": True}
