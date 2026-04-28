from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


class CategoriaGasto(StrEnum):
    PESSOAL = "Pessoal e Encargos Sociais"
    JUROS = "Juros e Encargos da Dívida"
    OUTRAS_CORRENTES = "Outras Despesas Correntes"
    INVESTIMENTOS = "Investimentos"
    INVERSOES_FINANCEIRAS = "Inversões Financeiras"
    AMORTIZACAO_DIVIDA = "Amortização da Dívida"


class GastoFiltro(BaseModel):
    orgao: Optional[str] = None
    ano: Optional[int] = Field(default=None, ge=1900, le=2100)
    mes: Optional[int] = Field(default=None, ge=1, le=12)
    categoria: Optional[CategoriaGasto] = Field(default=None, examples=["Investimentos"])
    valor_min: Optional[Decimal] = Field(default=None, ge=0)
    valor_max: Optional[Decimal] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def verificar_intervalo_precos(self) -> GastoFiltro:
        if self.valor_min is not None and self.valor_max is not None:
            if self.valor_min > self.valor_max:
                raise ValueError("O valor_min não pode ser maior que o valor_max")
        return self

    def cache_key(self) -> tuple:
        return (self.orgao, self.ano, self.mes, self.categoria, self.valor_min, self.valor_max)


class OrgaoResposta(BaseModel):
    id: int
    nome: str
    sigla: str

    model_config = ConfigDict(from_attributes=True)


class GastoResposta(BaseModel):
    id: UUID
    orgao: str
    categoria: str
    descricao: str
    valor: Decimal
    data_lancamento: date
    favorecido: str

    model_config = ConfigDict(from_attributes=True)


class TopDespesa(GastoResposta):
    pass

class ResumoCategoria(BaseModel):
    categoria: str
    total: Decimal


class ResumoResposta(BaseModel):
    total_categoria: list[ResumoCategoria]
    top5_maiores_despesas: list[TopDespesa]
    cache_info: Optional[str] = None


class PaginacaoParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginacaoResposta(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
    message: Optional[str] = None
