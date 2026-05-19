"""Zera o banco e cria os dados iniciais."""
import os
from database import Base, engine, SessionLocal
from auth import hash_senha
from models import (
    Usuario, Juiz, Assessor, Pessoa, Processo, PerfilEnum,
    TipoJuizEnum, TipoPessoaEnum, StatusProcessoEnum,
)

DB_FILE = "sorteio.db"


def main():
    if os.path.exists(DB_FILE):
        engine.dispose()
        os.remove(DB_FILE)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # TI
        ti = Usuario(login="ti", senha_hash=hash_senha("ti123"),
                     nome="Administrador TI", perfil=PerfilEnum.TI, ativo=True)
        db.add(ti); db.flush()

        # 8 juízes principais
        juizes = []
        for i in range(1, 9):
            u = Usuario(login=f"juiz{i}", senha_hash=hash_senha("juiz123"),
                        nome=f"Juiz(a) {i}", perfil=PerfilEnum.JUIZ, ativo=True)
            db.add(u); db.flush()
            j = Juiz(usuario_id=u.id, tipo=TipoJuizEnum.PRINCIPAL, ativo=True)
            db.add(j); db.flush()
            juizes.append(j)

        # 8 assessores
        for i in range(1, 9):
            u = Usuario(login=f"assessor{i}", senha_hash=hash_senha("assessor123"),
                        nome=f"Assessor(a) {i}", perfil=PerfilEnum.ASSESSOR, ativo=True)
            db.add(u); db.flush()
            db.add(Assessor(usuario_id=u.id, juiz_id=juizes[i - 1].id))

        # 2 assistentes
        assistentes = []
        for i in range(1, 3):
            u = Usuario(login=f"assistente{i}", senha_hash=hash_senha("assistente123"),
                        nome=f"Assistente {i}", perfil=PerfilEnum.ASSISTENTE, ativo=True)
            db.add(u); db.flush()
            assistentes.append(u)

        # 5 pessoas (3 PF + 2 PJ)
        pessoas_data = [
            (TipoPessoaEnum.PF, "11111111111", "Ana Silva"),
            (TipoPessoaEnum.PF, "22222222222", "Bruno Costa"),
            (TipoPessoaEnum.PF, "33333333333", "Carla Dias"),
            (TipoPessoaEnum.PJ, "11111111000111", "Empresa Alpha Ltda"),
            (TipoPessoaEnum.PJ, "22222222000122", "Beta S.A."),
        ]
        pessoas = []
        for tp, doc, nome in pessoas_data:
            p = Pessoa(tipo=tp, documento=doc, nome=nome)
            db.add(p); db.flush()
            pessoas.append(p)

        # 10 processos pendentes misturando os niveis
        niveis = [1, 2, 3, 1, 2, 3, 1, 2, 3, 2]
        for i, niv in enumerate(niveis, start=1):
            db.add(Processo(
                numero=f"000{i:04d}-2026", descricao=f"Processo de exemplo {i}",
                nivel=niv, pessoa_id=pessoas[i % len(pessoas)].id,
                status=StatusProcessoEnum.PENDENTE,
                cadastrado_por=assistentes[i % 2].id,
            ))

        db.commit()
        print("Seed concluído. Credenciais: ti/ti123, juiz1..8/juiz123, "
              "assessor1..8/assessor123, assistente1..2/assistente123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
