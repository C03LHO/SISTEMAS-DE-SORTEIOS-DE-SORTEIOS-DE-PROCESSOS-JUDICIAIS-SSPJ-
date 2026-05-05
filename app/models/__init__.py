"""
Exporta todos os modelos para que o Alembic os detecte automaticamente.
Basta importar este pacote para registrar todos os modelos na Base.
"""

from app.models.user import User, UserRole
from app.models.person import Person, DocumentType
from app.models.process import Process, ProcessLevel, ProcessStatus
from app.models.lottery import LotteryRound, LotteryState, LOTTERY_STATE_ID
from app.models.conflict import JudgeConflict, ConflictRecord
from app.models.audit import AuditLog

__all__ = [
    "User", "UserRole",
    "Person", "DocumentType",
    "Process", "ProcessLevel", "ProcessStatus",
    "LotteryRound", "LotteryState", "LOTTERY_STATE_ID",
    "JudgeConflict", "ConflictRecord",
    "AuditLog",
]
