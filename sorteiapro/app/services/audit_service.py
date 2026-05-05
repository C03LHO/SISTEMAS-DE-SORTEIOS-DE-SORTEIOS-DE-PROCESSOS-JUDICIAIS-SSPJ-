"""
Serviço de Auditoria.

Responsável por registrar todas as ações importantes no AuditLog.
O log é APPEND-ONLY — nunca é alterado ou deletado.

Uso:
    await audit_service.log(db, action="LOGIN", entity="user",
                            entity_id=str(user.id), user_id=user.id)
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log(
    db: AsyncSession,
    action: str,
    entity: str,
    entity_id: str,
    details: Optional[dict] = None,
    user_id: Optional[UUID] = None,
) -> AuditLog:
    """
    Cria uma entrada no log de auditoria.

    Args:
        db: sessão assíncrona do banco de dados
        action: identificador da ação (ex: "LOTTERY_SUCCESS", "LOGIN", "CONFLICT_REFUSED")
        entity: tipo da entidade afetada (ex: "process", "user")
        entity_id: ID da entidade como string
        details: dicionário com informações adicionais (opcional)
        user_id: ID do usuário que executou a ação (None para ações automáticas)

    Returns:
        O objeto AuditLog criado (ainda não commitado).
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details or {},
    )
    db.add(entry)
    # Não fazemos commit aqui — deixamos para o chamador decidir o momento
    return entry
