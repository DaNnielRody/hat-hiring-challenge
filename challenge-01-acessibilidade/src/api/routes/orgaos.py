"""Rotas para órgãos."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.domain import services
from src.domain.schemas import OrgaoResposta, PaginacaoParams, PaginacaoResposta
from src.infra.database import get_session

router = APIRouter()


@router.get("", response_model=PaginacaoResposta[OrgaoResposta])
def listar_orgaos(
    paginacao: Annotated[PaginacaoParams, Depends()],
    session: Session = Depends(get_session),
):
    return services.lista_orgaos(session, paginacao)
