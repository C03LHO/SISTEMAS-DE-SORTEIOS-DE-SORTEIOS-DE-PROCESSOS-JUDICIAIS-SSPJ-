import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship
from database import Base


class PerfilEnum(str, enum.Enum):
    TI = "TI"
    JUIZ = "JUIZ"
    ASSESSOR = "ASSESSOR"
    ASSISTENTE = "ASSISTENTE"
    JUIZ_EXTERNO = "JUIZ_EXTERNO"


class TipoJuizEnum(str, enum.Enum):
    PRINCIPAL = "PRINCIPAL"
    EXTERNO = "EXTERNO"


class TipoPessoaEnum(str, enum.Enum):
    PF = "PF"
    PJ = "PJ"


class StatusProcessoEnum(str, enum.Enum):
    PENDENTE = "PENDENTE"
    SORTEADO = "SORTEADO"
    AGUARDANDO_JUIZ_EXTERNO = "AGUARDANDO_JUIZ_EXTERNO"
    ENCERRADO = "ENCERRADO"


class MotivoLogEnum(str, enum.Enum):
    SORTEIO_NORMAL = "SORTEIO_NORMAL"
    REABERTURA = "REABERTURA"
    PRIORIDADE_COMPENSACAO = "PRIORIDADE_COMPENSACAO"
    DESIGNACAO_EXTERNA = "DESIGNACAO_EXTERNA"


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    login = Column(String, unique=True, nullable=False, index=True)
    senha_hash = Column(String, nullable=False)
    nome = Column(String, nullable=False)
    perfil = Column(Enum(PerfilEnum), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)


class Juiz(Base):
    __tablename__ = "juizes"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    tipo = Column(Enum(TipoJuizEnum), nullable=False, default=TipoJuizEnum.PRINCIPAL)
    ativo = Column(Boolean, default=True, nullable=False)
    usuario = relationship("Usuario")


class Assessor(Base):
    __tablename__ = "assessores"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    juiz_id = Column(Integer, ForeignKey("juizes.id"), nullable=False)
    usuario = relationship("Usuario")
    juiz = relationship("Juiz")


class Pessoa(Base):
    __tablename__ = "pessoas"
    id = Column(Integer, primary_key=True)
    tipo = Column(Enum(TipoPessoaEnum), nullable=False)
    documento = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)


class Processo(Base):
    __tablename__ = "processos"
    id = Column(Integer, primary_key=True)
    numero = Column(String, unique=True, nullable=False)
    descricao = Column(Text, nullable=False)
    nivel = Column(Integer, nullable=False)  # 1, 2, 3
    pessoa_id = Column(Integer, ForeignKey("pessoas.id"), nullable=False)
    status = Column(Enum(StatusProcessoEnum), default=StatusProcessoEnum.PENDENTE, nullable=False)
    juiz_id = Column(Integer, ForeignKey("juizes.id"), nullable=True)
    reaberto = Column(Boolean, default=False, nullable=False)
    juiz_anterior_id = Column(Integer, ForeignKey("juizes.id"), nullable=True)
    cadastrado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    sorteado_em = Column(DateTime, nullable=True)

    pessoa = relationship("Pessoa")
    juiz = relationship("Juiz", foreign_keys=[juiz_id])
    juiz_anterior = relationship("Juiz", foreign_keys=[juiz_anterior_id])


class ConflitoInteresse(Base):
    __tablename__ = "conflitos_interesse"
    id = Column(Integer, primary_key=True)
    processo_id = Column(Integer, ForeignKey("processos.id"), nullable=False)
    juiz_id = Column(Integer, ForeignKey("juizes.id"), nullable=False)
    justificativa = Column(Text, nullable=False)
    documento_path = Column(String, nullable=False)
    registrado_em = Column(DateTime, default=datetime.utcnow)


class PrioridadeCompensacao(Base):
    __tablename__ = "prioridades_compensacao"
    id = Column(Integer, primary_key=True)
    juiz_id = Column(Integer, ForeignKey("juizes.id"), nullable=False)
    nivel = Column(Integer, nullable=False)
    consumida = Column(Boolean, default=False, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)


class AcessoJuizExterno(Base):
    __tablename__ = "acesso_juiz_externo"
    id = Column(Integer, primary_key=True)
    juiz_externo_id = Column(Integer, ForeignKey("juizes.id"), nullable=False)
    processo_id = Column(Integer, ForeignKey("processos.id"), nullable=False)


class LogSorteio(Base):
    __tablename__ = "log_sorteio"
    id = Column(Integer, primary_key=True)
    processo_id = Column(Integer, ForeignKey("processos.id"), nullable=False)
    juiz_id = Column(Integer, ForeignKey("juizes.id"), nullable=False)
    motivo = Column(Enum(MotivoLogEnum), nullable=False)
    detalhes = Column(Text, default="")
    criado_em = Column(DateTime, default=datetime.utcnow)


class AutorizacaoEdicao(Base):
    __tablename__ = "autorizacoes_edicao"
    id = Column(Integer, primary_key=True)
    processo_id = Column(Integer, ForeignKey("processos.id"), nullable=False)
    juiz_id = Column(Integer, ForeignKey("juizes.id"), nullable=False)
    assessor_id = Column(Integer, ForeignKey("assessores.id"), nullable=False)
    concedida_em = Column(DateTime, default=datetime.utcnow)
    usada = Column(Boolean, default=False, nullable=False)
