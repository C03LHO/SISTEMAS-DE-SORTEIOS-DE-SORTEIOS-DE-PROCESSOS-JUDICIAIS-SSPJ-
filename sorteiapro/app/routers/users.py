"""
Router de Usuários.

Todas as rotas são restritas ao role TI.

Rotas:
  GET    /users/                     — lista todos os usuários
  POST   /users/                     — cria novo usuário
  PUT    /users/{user_id}            — atualiza usuário
  DELETE /users/{user_id}            — soft-delete (desativa)
  POST   /users/{user_id}/link-assessor — vincula assessor ao juiz
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse, LinkAssessorRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Usuários"])

# Dependência reutilizável: apenas TI pode acessar estas rotas
somente_ti = require_roles(UserRole.TI)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Perfil do usuário autenticado",
    description="Retorna os dados do usuário que está autenticado no momento.",
)
async def meu_perfil(
    current_user=Depends(get_current_user),
):
    """Útil para o frontend exibir o nome e papel do usuário logado."""
    return current_user


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Listar usuários",
    description="Retorna todos os usuários do sistema (ativos e inativos). Acesso: TI.",
)
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    current_user=somente_ti,
):
    return await user_service.get_all_users(db)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
    summary="Criar usuário",
    description="Cria um novo usuário. ASSESSOR requer judge_id. Acesso: TI.",
)
async def criar_usuario(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user=somente_ti,
):
    return await user_service.create_user(data, db, created_by_id=current_user.id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Atualizar usuário",
    description="Atualiza os dados de um usuário existente. Acesso: TI.",
)
async def atualizar_usuario(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=somente_ti,
):
    return await user_service.update_user(user_id, data, db, updated_by_id=current_user.id)


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    summary="Desativar usuário (soft-delete)",
    description="Desativa o usuário sem removê-lo do banco. Dados históricos são preservados. Acesso: TI.",
)
async def desativar_usuario(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=somente_ti,
):
    return await user_service.deactivate_user(user_id, db, deactivated_by_id=current_user.id)


@router.post(
    "/{user_id}/link-assessor",
    response_model=UserResponse,
    summary="Vincular assessor ao juiz",
    description="Associa um assessor a um juiz específico. Acesso: TI.",
)
async def vincular_assessor(
    user_id: UUID,
    data: LinkAssessorRequest,
    db: AsyncSession = Depends(get_db),
    current_user=somente_ti,
):
    return await user_service.link_assessor_to_judge(
        assessor_id=user_id,
        judge_id=data.judge_id,
        db=db,
        updated_by_id=current_user.id,
    )
