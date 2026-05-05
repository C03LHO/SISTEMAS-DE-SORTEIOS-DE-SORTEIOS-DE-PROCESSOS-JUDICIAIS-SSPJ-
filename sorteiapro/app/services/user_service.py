"""
Serviço de Usuários.

Contém toda a lógica de negócio relacionada ao gerenciamento de usuários:
- Criação com hash de senha
- Busca por email e por ID
- Atualização e soft-delete
- Vínculo de assessor ao juiz
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
import app.services.audit_service as audit_service


async def get_user_by_id(user_id: UUID, db: AsyncSession) -> Optional[User]:
    """Busca um usuário pelo seu UUID. Retorna None se não encontrado."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    """Busca um usuário pelo email. Retorna None se não encontrado."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession) -> list[User]:
    """Retorna todos os usuários (ativos e inativos)."""
    result = await db.execute(select(User).order_by(User.name))
    return list(result.scalars().all())


async def create_user(data: UserCreate, db: AsyncSession, created_by_id: UUID) -> User:
    """
    Cria um novo usuário com a senha já hasheada.

    Validações:
    - Email não pode estar em uso
    - ASSESSOR deve ter judge_id informado
    - O juiz vinculado deve ter role=JUDGE
    """
    # Verifica se o email já está em uso
    existing = await get_user_by_email(data.email, db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{data.email}' já está em uso"
        )

    # Se for assessor, deve ter um juiz vinculado
    if data.role == UserRole.ASSESSOR:
        if not data.judge_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessores precisam ter um juiz vinculado (judge_id obrigatório)"
            )
        # Verifica se o juiz existe e tem a role correta
        judge = await get_user_by_id(data.judge_id, db)
        if not judge or judge.role != UserRole.JUDGE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O juiz vinculado não existe ou não tem role JUDGE"
            )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role.value,
        judge_id=data.judge_id,
    )
    db.add(user)

    # Registra a criação no audit log (sem commit aqui)
    await audit_service.log(
        db=db,
        action="USER_CREATED",
        entity="user",
        entity_id=str(user.id),
        user_id=created_by_id,
        details={"email": data.email, "role": data.role.value},
    )

    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession,
    updated_by_id: UUID,
) -> User:
    """
    Atualiza os campos fornecidos de um usuário existente.
    Apenas os campos não-None são alterados.
    """
    user = await get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Aplica apenas os campos que foram enviados (não-None)
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        # Verifica conflito de email com outro usuário
        existing = await get_user_by_email(data.email, db)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{data.email}' já está em uso"
            )
        user.email = data.email
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    if data.role is not None:
        user.role = data.role.value
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.judge_id is not None:
        user.judge_id = data.judge_id

    await audit_service.log(
        db=db,
        action="USER_UPDATED",
        entity="user",
        entity_id=str(user_id),
        user_id=updated_by_id,
        details={"fields_changed": list(data.model_dump(exclude_none=True).keys())},
    )

    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_user(user_id: UUID, db: AsyncSession, deactivated_by_id: UUID) -> User:
    """
    Soft-delete: desativa o usuário sem removê-lo do banco.
    O usuário perde acesso ao sistema mas seus dados históricos são preservados.
    """
    user = await get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    user.is_active = False

    await audit_service.log(
        db=db,
        action="USER_DEACTIVATED",
        entity="user",
        entity_id=str(user_id),
        user_id=deactivated_by_id,
    )

    await db.commit()
    await db.refresh(user)
    return user


async def link_assessor_to_judge(
    assessor_id: UUID,
    judge_id: UUID,
    db: AsyncSession,
    updated_by_id: UUID,
) -> User:
    """Vincula um assessor a um juiz específico."""
    assessor = await get_user_by_id(assessor_id, db)
    if not assessor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessor não encontrado"
        )
    if assessor.role != UserRole.ASSESSOR.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O usuário informado não tem role ASSESSOR"
        )

    judge = await get_user_by_id(judge_id, db)
    if not judge or judge.role != UserRole.JUDGE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Juiz não encontrado ou sem role JUDGE"
        )

    assessor.judge_id = judge_id

    await audit_service.log(
        db=db,
        action="ASSESSOR_LINKED",
        entity="user",
        entity_id=str(assessor_id),
        user_id=updated_by_id,
        details={"judge_id": str(judge_id)},
    )

    await db.commit()
    await db.refresh(assessor)
    return assessor
