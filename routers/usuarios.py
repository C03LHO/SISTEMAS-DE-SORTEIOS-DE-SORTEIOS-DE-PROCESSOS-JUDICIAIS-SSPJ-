from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import exige_perfil, hash_senha
from models import Usuario, PerfilEnum, Juiz, Assessor, TipoJuizEnum
from schemas import UsuarioIn, UsuarioOut, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
_so_ti = exige_perfil(PerfilEnum.TI)


@router.post("/", response_model=UsuarioOut)
def criar(body: UsuarioIn, db: Session = Depends(get_db), _=Depends(_so_ti)):
    if db.query(Usuario).filter(Usuario.login == body.login).first():
        raise HTTPException(400, "Login já existe")
    u = Usuario(login=body.login, senha_hash=hash_senha(body.senha),
                nome=body.nome, perfil=body.perfil, ativo=True)
    db.add(u)
    db.flush()
    # se for juiz, cria tambem o registro na tabela de juizes
    if body.perfil == PerfilEnum.JUIZ:
        db.add(Juiz(usuario_id=u.id, tipo=TipoJuizEnum.PRINCIPAL, ativo=True))
    db.commit()
    db.refresh(u)
    return u


@router.get("/", response_model=list[UsuarioOut])
def listar(db: Session = Depends(get_db), _=Depends(_so_ti)):
    return db.query(Usuario).order_by(Usuario.id).all()


@router.patch("/{uid}", response_model=UsuarioOut)
def editar(uid: int, body: UsuarioUpdate, db: Session = Depends(get_db), _=Depends(_so_ti)):
    u = db.query(Usuario).filter(Usuario.id == uid).first()
    if not u:
        raise HTTPException(404, "Usuário não encontrado")
    if body.nome is not None:
        u.nome = body.nome
    if body.senha is not None:
        u.senha_hash = hash_senha(body.senha)
    if body.ativo is not None:
        u.ativo = body.ativo
    db.commit()
    db.refresh(u)
    return u


@router.delete("/{uid}")
def desativar(uid: int, db: Session = Depends(get_db), _=Depends(_so_ti)):
    u = db.query(Usuario).filter(Usuario.id == uid).first()
    if not u:
        raise HTTPException(404, "Usuário não encontrado")
    u.ativo = False
    db.commit()
    return {"ok": True}


@router.post("/assessor/{aid}/vincular/{jid}")
def vincular_assessor(aid: int, jid: int, db: Session = Depends(get_db), _=Depends(_so_ti)):
    a = db.query(Assessor).filter(Assessor.id == aid).first()
    j = db.query(Juiz).filter(Juiz.id == jid).first()
    if not a or not j:
        raise HTTPException(404, "Assessor ou juiz não encontrado")
    a.juiz_id = j.id
    db.commit()
    return {"ok": True}
