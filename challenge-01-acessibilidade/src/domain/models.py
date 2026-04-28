from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship, SQLModel


class Orgao(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    nome: str = Field(index=True)
    sigla: str

    gastos: list["Gasto"] = Relationship(back_populates="orgao")


class Gasto(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    orgao_id: int = Field(foreign_key="orgao.id", index=True)
    categoria: str = Field(index=True)
    descricao: str
    valor: Decimal = Field(sa_column=Column(Numeric(15, 2)))
    data_lancamento: date
    ano: int = Field(index=True)
    mes: int = Field(index=True)
    favorecido: str

    orgao: Optional[Orgao] = Relationship(back_populates="gastos")
