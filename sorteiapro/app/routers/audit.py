"""
Router de Auditoria.

O AuditLog é APPEND-ONLY — sem rotas de DELETE ou UPDATE.

Rotas:
  GET /audit/logs                        — TI: todos os logs
  GET /audit/logs/{entity}/{entity_id}   — TI, JUDGE, ASSESSOR: logs de uma entidade
"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_roles
from app.models.audit import AuditLog
from app.models.user import UserRole

router = APIRouter(prefix="/audit", tags=["Auditoria"])


@router.get(
    "/logs",
    summary="Listar todos os logs de auditoria",
    description="Retorna todos os registros de auditoria em ordem cronológica reversa. Acesso: TI.",
)
async def listar_logs(
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI),
    entity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    Paginação via query params `limit` e `offset`.
    Filtro opcional por entidade: `?entity=process`
    Exemplo: GET /audit/logs?entity=process&limit=50&offset=100
    """
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if entity:
        query = query.where(AuditLog.entity == entity)
    result = await db.execute(query.limit(limit).offset(offset))
    logs = result.scalars().all()
    return [_format_log(log) for log in logs]


@router.get(
    "/logs/{entity}/{entity_id}",
    summary="Logs de auditoria por entidade",
    description=(
        "Retorna o histórico de auditoria de uma entidade específica. "
        "Exemplo: GET /audit/logs/process/uuid-do-processo. "
        "Acesso: TI, JUDGE, ASSESSOR."
    ),
)
async def logs_por_entidade(
    entity: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=require_roles(UserRole.TI, UserRole.JUDGE, UserRole.ASSESSOR),
):
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.entity == entity,
            AuditLog.entity_id == entity_id,
        )
        .order_by(AuditLog.created_at.asc())
    )
    logs = result.scalars().all()
    return [_format_log(log) for log in logs]


def _format_log(log: AuditLog) -> dict:
    """Formata um AuditLog como dicionário para a resposta JSON."""
    return {
        "id": str(log.id),
        "user_id": str(log.user_id) if log.user_id else None,
        "action": log.action,
        "entity": log.entity,
        "entity_id": log.entity_id,
        "details": log.details,
        "created_at": log.created_at.isoformat(),
    }
