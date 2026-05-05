"""
Script de Seed Inicial — SorteiaPro

Cria os dados iniciais necessários para o sistema funcionar:
  - 1 usuário TI (administrador)
  - 8 juízes titulares
  - 1 assessor (vinculado ao Judge01)
  - 1 assistente
  - 1 LotteryState (estado inicial vazio do algoritmo de sorteio)

Como executar:
  python seed.py

ATENÇÃO: Execute APÓS rodar `alembic upgrade head`.
Se os usuários já existirem, o script ignora e não duplica.
"""

import asyncio
import sys
import os

# Adiciona o diretório raiz ao path para importar os módulos da aplicação
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.lottery import LotteryState, LOTTERY_STATE_ID


async def seed():
    """Função principal de seed — cria todos os dados iniciais."""
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("  SorteiaPro — Seed Inicial")
        print("=" * 60)

        # ─── 1. Usuário TI ────────────────────────────────────────────────
        await criar_usuario_se_nao_existir(
            db=db,
            name="Administrador TI",
            email="ti@tribunal.gov.br",
            password="Admin@2025",
            role=UserRole.TI,
        )

        # ─── 2. Oito Juízes Titulares ─────────────────────────────────────
        juizes_criados = []
        for i in range(1, 9):
            juiz = await criar_usuario_se_nao_existir(
                db=db,
                name=f"Juiz Titular 0{i:02d}" if i < 10 else f"Juiz Titular {i}",
                email=f"judge{i:02d}@tribunal.gov.br",
                password="Judge@2025",
                role=UserRole.JUDGE,
            )
            juizes_criados.append(juiz)

        # ─── 3. Assessor (vinculado ao Judge01) ───────────────────────────
        # Busca o judge01 para pegar o ID
        result = await db.execute(
            select(User).where(User.email == "judge01@tribunal.gov.br")
        )
        judge01 = result.scalar_one_or_none()

        await criar_usuario_se_nao_existir(
            db=db,
            name="Assessor 01",
            email="assessor01@tribunal.gov.br",
            password="Assessor@2025",
            role=UserRole.ASSESSOR,
            judge_id=judge01.id if judge01 else None,
        )

        # ─── 4. Assistente ────────────────────────────────────────────────
        await criar_usuario_se_nao_existir(
            db=db,
            name="Assistente 01",
            email="assistente01@tribunal.gov.br",
            password="Assist@2025",
            role=UserRole.ASSISTANT,
        )

        # ─── 5. LotteryState (singleton) ─────────────────────────────────
        result = await db.execute(
            select(LotteryState).where(LotteryState.id == LOTTERY_STATE_ID)
        )
        state = result.scalar_one_or_none()

        if not state:
            state = LotteryState(
                id=LOTTERY_STATE_ID,
                complex_round_participants=[],  # nenhum juiz participou ainda
                judge_priorities={},             # sem prioridades
                judge_weighted_sums={},          # sem somas de carga
            )
            db.add(state)
            await db.commit()
            print("✓ LotteryState criado (estado inicial vazio)")
        else:
            print("→ LotteryState já existe, pulando...")

        print("=" * 60)
        print("  Seed concluído com sucesso!")
        print("=" * 60)
        print()
        print("Credenciais de acesso:")
        print(f"  TI:         ti@tribunal.gov.br         / Admin@2025")
        print(f"  Juiz 01:    judge01@tribunal.gov.br    / Judge@2025")
        print(f"  Assessor:   assessor01@tribunal.gov.br / Assessor@2025")
        print(f"  Assistente: assistente01@tribunal.gov.br / Assist@2025")
        print()
        print("Acesse o Swagger em: http://localhost:8000/docs")


async def criar_usuario_se_nao_existir(
    db,
    name: str,
    email: str,
    password: str,
    role: UserRole,
    judge_id=None,
) -> User:
    """
    Cria um usuário se o email ainda não existir no banco.
    Retorna o usuário existente ou recém-criado.
    """
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  → {email} já existe, pulando...")
        return existing

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role.value,
        judge_id=judge_id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    print(f"  ✓ Criado: {email} [{role.value}]")
    return user


if __name__ == "__main__":
    asyncio.run(seed())
