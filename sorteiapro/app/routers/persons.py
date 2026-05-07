"""
Router de Pessoas (partes dos processos).

Rotas:
  GET  /persons/        — lista todas as pessoas (TI, ASSESSOR, ASSISTANT)
  GET  /persons/{id}    — obtém pessoa por ID
  POST /persons/        — cadastra nova pessoa (ASSISTANT, TI)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_roles
from app.models.user import UserRole
from app.models.person import Person
from app.schemas.person import PersonCreate, PersonResponse

router = APIRouter(prefix="/persons", tags=["Pessoas"])


@router.get(
    "/",
    response_model=list[PersonResponse],
    summary="Listar pessoas",
    description="Retorna todas as pessoas cadastradas. Acesso: TI, ASSESSOR, ASSISTANT.",
)
async def listar_pessoas(
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI, UserRole.ASSESSOR, UserRole.ASSISTANT),
):
    result = await db.execute(select(Person).order_by(Person.name))
    return result.scalars().all()


@router.get(
    "/{person_id}",
    response_model=PersonResponse,
    summary="Obter pessoa por ID",
    description="Retorna os dados de uma pessoa específica. Acesso: TI, ASSESSOR, ASSISTANT.",
)
async def obter_pessoa(
    person_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI, UserRole.ASSESSOR, UserRole.ASSISTANT),
):
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return person


@router.post(
    "/",
    response_model=PersonResponse,
    status_code=201,
    summary="Cadastrar pessoa",
    description=(
        "Cadastra uma nova pessoa (parte do processo). "
        "O documento (CPF/CNPJ) deve ser único no sistema. Acesso: ASSISTANT, TI."
    ),
)
async def cadastrar_pessoa(
    data: PersonCreate,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.ASSISTANT, UserRole.TI),
):
    # Verifica duplicidade de documento
    result = await db.execute(select(Person).where(Person.document == data.document))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Documento {data.document} já cadastrado no sistema",
        )

    person = Person(
        name=data.name,
        document=data.document,
        document_type=data.document_type.value,
    )
    db.add(person)
    await db.commit()
    await db.refresh(person)
    return person
