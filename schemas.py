from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models import PerfilEnum, TipoPessoaEnum, StatusProcessoEnum, MotivoLogEnum


class LoginIn(BaseModel):
    login: str
    senha: str


class LoginOut(BaseModel):
    token: str
    perfil: PerfilEnum
    nome: str
    usuario_id: int
    juiz_id: Optional[int] = None
    assessor_id: Optional[int] = None


class UsuarioIn(BaseModel):
    login: str
    senha: str
    nome: str
    perfil: PerfilEnum


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    senha: Optional[str] = None
    ativo: Optional[bool] = None


class UsuarioOut(BaseModel):
    id: int
    login: str
    nome: str
    perfil: PerfilEnum
    ativo: bool

    class Config:
        from_attributes = True


class PessoaIn(BaseModel):
    tipo: TipoPessoaEnum
    documento: str
    nome: str


class PessoaOut(BaseModel):
    id: int
    tipo: TipoPessoaEnum
    documento: str
    nome: str

    class Config:
        from_attributes = True


class ProcessoIn(BaseModel):
    numero: str
    descricao: str
    nivel: int = Field(ge=1, le=3)
    pessoa_id: int


class ProcessoUpdate(BaseModel):
    descricao: Optional[str] = None
    nivel: Optional[int] = Field(default=None, ge=1, le=3)
    pessoa_id: Optional[int] = None


class ProcessoOut(BaseModel):
    id: int
    numero: str
    descricao: str
    nivel: int
    pessoa_id: int
    status: str
    juiz_id: Optional[int] = None
    reaberto: bool
    criado_em: datetime
    sorteado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class AutorizarEdicaoIn(BaseModel):
    assessor_id: int


class DesignarJuizExternoIn(BaseModel):
    processo_id: int
    login: str
    senha: str
    nome: str


class LogSorteioOut(BaseModel):
    id: int
    processo_id: int
    juiz_id: int
    motivo: MotivoLogEnum
    detalhes: str
    criado_em: datetime

    class Config:
        from_attributes = True


class ConflitoOut(BaseModel):
    id: int
    processo_id: int
    juiz_id: int
    justificativa: str
    registrado_em: datetime

    class Config:
        from_attributes = True
