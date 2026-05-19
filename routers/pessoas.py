from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import usuario_atual
from models import Pessoa, Usuario, PerfilEnum
from schemas import PessoaIn, PessoaOut

router = APIRouter(prefix="/pessoas", tags=["pessoas"])


@router.post("/", response_model=PessoaOut)
def criar(body: PessoaIn, db: Session = Depends(get_db),
          u: Usuario = Depends(usuario_atual)):
    if u.perfil not in (PerfilEnum.TI, PerfilEnum.ASSISTENTE):
        raise HTTPException(403, "Acesso negado")
    doc = "".join(c for c in body.documento if c.isdigit())
    if body.tipo.value == "PF" and len(doc) != 11:
        raise HTTPException(400, "CPF deve ter 11 dígitos")
    if body.tipo.value == "PJ" and len(doc) != 14:
        raise HTTPException(400, "CNPJ deve ter 14 dígitos")
    if db.query(Pessoa).filter(Pessoa.documento == doc).first():
        raise HTTPException(400, "Documento já cadastrado")
    p = Pessoa(tipo=body.tipo, documento=doc, nome=body.nome)
    db.add(p); db.commit(); db.refresh(p)
    return p


@router.get("/", response_model=list[PessoaOut])
def listar(db: Session = Depends(get_db), u: Usuario = Depends(usuario_atual)):
    if u.perfil not in (PerfilEnum.TI, PerfilEnum.JUIZ, PerfilEnum.ASSESSOR, PerfilEnum.ASSISTENTE):
        raise HTTPException(403, "Acesso negado")
    return db.query(Pessoa).order_by(Pessoa.nome).all()
