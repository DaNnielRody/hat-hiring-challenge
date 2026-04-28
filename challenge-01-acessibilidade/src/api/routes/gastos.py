"""Rotas para gastos públicos."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from src.domain import services
from src.domain.schemas import (
    GastoFiltro,
    GastoResposta,
    PaginacaoParams,
    PaginacaoResposta,
    ResumoResposta,
)
from src.infra.cache import cache
from src.infra.database import get_session

router = APIRouter()


@router.get("", response_model=PaginacaoResposta[GastoResposta])
def listar_gastos(
    filtro: Annotated[GastoFiltro, Depends()],
    paginacao: Annotated[PaginacaoParams, Depends()],
    session: Session = Depends(get_session),
):
    return services.lista_gastos(session, filtro, paginacao)


@router.get("/resumo", response_model=ResumoResposta)
def resumo_gastos(
    filtro: Annotated[GastoFiltro, Depends()],
    response: Response,
    session: Session = Depends(get_session),
):
    cache_key = f"resumo:{filtro.cache_key()}"
    cached = cache.get(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return ResumoResposta(
            **cached,
            cache_info="Dados em cache — podem ter até 60 segundos de defasagem em relação ao banco.",
        )
    result = services.get_resumo(session, filtro)
    cache[cache_key] = result.model_dump(mode="json", exclude={"cache_info"})
    response.headers["X-Cache"] = "MISS"
    return result


@router.get("/{gasto_id}", response_model=GastoResposta)
def detalhar_gasto(
    gasto_id: UUID,
    session: Session = Depends(get_session),
):
    return services.get_gasto(session, gasto_id)
