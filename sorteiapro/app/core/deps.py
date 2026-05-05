"""
Dependências reutilizáveis do FastAPI (Depends).

- get_db: abre e fecha uma sessão de banco de dados por requisição
- get_current_user: decodifica o JWT e retorna o usuário autenticado
- require_roles: cria uma dependência que exige um ou mais roles específicos
"""

from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token

# Esquema OAuth2 — aponta para a rota de login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência que fornece uma sessão assíncrona do banco de dados.
    A sessão é aberta no início da requisição e fechada ao final (via finally).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Decodifica o token JWT e retorna o objeto User correspondente.
    Levanta 401 se o token for inválido ou o usuário não existir/estiver inativo.
    """
    # Importação local evita import circular com os models
    from app.models.user import User

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decodifica o token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    # Extrai o ID do usuário do campo "sub"
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_error

    # Busca o usuário no banco de dados
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_error

    return user


def require_roles(*roles):
    """
    Fábrica de dependências para controle de acesso por papel (RBAC).

    Uso:
        @router.get("/admin", dependencies=[require_roles(UserRole.TI)])

    Ou como parâmetro:
        current_user: User = require_roles(UserRole.TI, UserRole.JUDGE)
    """
    async def dependency(current_user=Depends(get_current_user)):
        if current_user.role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Roles permitidas: {[r.value for r in roles]}"
            )
        return current_user
    return Depends(dependency)
