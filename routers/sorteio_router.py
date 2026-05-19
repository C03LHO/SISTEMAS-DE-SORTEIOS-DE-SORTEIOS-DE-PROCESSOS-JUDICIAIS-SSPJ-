from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import exige_perfil, usuario_atual
from models import PerfilEnum, Usuario, LogSorteio
from schemas import LogSorteioOut
from sorteio import executar_sorteio
from fastapi import HTTPException

router = APIRouter(prefix="/sorteio", tags=["sorteio"])


@router.post("/executar")
def executar(db: Session = Depends(get_db),
             _=Depends(exige_perfil(PerfilEnum.TI))):
    logs = executar_sorteio(db)
    return {"processos_sorteados": len(logs)}


@router.get("/logs", response_model=list[LogSorteioOut])
def logs(db: Session = Depends(get_db),
         u: Usuario = Depends(usuario_atual)):
    if u.perfil not in (PerfilEnum.TI, PerfilEnum.JUIZ):
        raise HTTPException(403, "Acesso negado")
    return db.query(LogSorteio).order_by(LogSorteio.id.desc()).all()
