from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario, PerfilEnum

SECRET_KEY = "sspj-academic-secret-key-change-in-prod"
ALGORITHM = "HS256"
TOKEN_EXP_MIN = 60 * 12

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def hash_senha(s: str) -> str:
    return pwd_ctx.hash(s)


def verificar_senha(s: str, h: str) -> bool:
    return pwd_ctx.verify(s, h)


def criar_token(usuario_id: int) -> str:
    payload = {
        "sub": str(usuario_id),
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXP_MIN),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def usuario_atual(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    if not token:
        raise HTTPException(401, "Não autenticado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uid = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(401, "Token inválido")
    u = db.query(Usuario).filter(Usuario.id == uid, Usuario.ativo == True).first()
    if not u:
        raise HTTPException(401, "Usuário não encontrado ou inativo")
    return u


def exige_perfil(*perfis: PerfilEnum):
    def dep(u: Usuario = Depends(usuario_atual)) -> Usuario:
        if u.perfil not in perfis:
            raise HTTPException(403, "Acesso negado para este perfil")
        return u
    return dep
