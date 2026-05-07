"""
Router de Autenticação.

Rota:
  POST /auth/login — recebe email/senha, retorna token JWT
  POST /auth/logout — apenas registra o logout no audit (o JWT é stateless)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.services.user_service import get_user_by_email
import app.services.audit_service as audit_service

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    summary="Login de usuário",
    description="Autentica o usuário com email e senha. Retorna um token JWT válido por 8 horas.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Recebe `username` (email) e `password` via form data (padrão OAuth2).
    Retorna o token JWT para ser usado no header Authorization: Bearer <token>.
    """
    # OAuth2PasswordRequestForm usa "username" mas nós usamos email
    user = await get_user_by_email(form_data.username, db)

    # Verifica credenciais (email inexistente ou senha errada → mesma mensagem)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Conta desativada. Entre em contato com o TI.",
        )

    # Cria o token com informações do usuário no payload
    token = create_access_token(data={
        "sub": str(user.id),        # subject = ID do usuário
        "role": user.role,           # papel (para informação, validação real é no banco)
        "judge_id": str(user.judge_id) if user.judge_id else None,
    })

    # Registra o login no audit log
    await audit_service.log(
        db=db,
        action="LOGIN",
        entity="user",
        entity_id=str(user.id),
        user_id=user.id,
        details={"email": user.email},
    )
    await db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,  # em segundos
        # Dados do usuário para o frontend armazenar no localStorage
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "judge_id": str(user.judge_id) if user.judge_id else None,
        },
    }


@router.post(
    "/logout",
    summary="Logout (registro de auditoria)",
    description="Registra o logout no log de auditoria. O token JWT é invalidado no cliente.",
)
async def logout(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Como o JWT é stateless, o logout real acontece no cliente (descartar o token).
    Esta rota apenas registra o evento para fins de auditoria.
    """
    await audit_service.log(
        db=db,
        action="LOGOUT",
        entity="user",
        entity_id=str(current_user.id),
        user_id=current_user.id,
    )
    await db.commit()
    return {"detail": "Logout registrado com sucesso"}
