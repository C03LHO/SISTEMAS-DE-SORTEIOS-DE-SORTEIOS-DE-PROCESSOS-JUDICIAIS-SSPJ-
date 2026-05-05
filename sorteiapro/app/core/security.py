"""
Funções de segurança: hash de senha e JWT.

- hash_password / verify_password: usa bcrypt via passlib
- create_access_token: cria JWT com python-jose
- decode_access_token: decodifica e valida JWT
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Contexto do passlib configurado para bcrypt
# O deprecated="auto" atualiza hashes antigos automaticamente
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Gera o hash bcrypt de uma senha em texto puro."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto puro bate com o hash armazenado."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT com os dados fornecidos.

    Args:
        data: dicionário com o payload (ex: {"sub": user_id, "role": "JUDGE"})
        expires_delta: tempo extra de expiração; usa o padrão das settings se None
    """
    payload = data.copy()

    # Calcula o momento de expiração
    expire_hours = settings.ACCESS_TOKEN_EXPIRE_HOURS
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=expire_hours))
    payload["exp"] = expire

    # Assina o token com a chave secreta
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica e valida um token JWT.

    Retorna o payload como dicionário, ou None se o token for inválido/expirado.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
