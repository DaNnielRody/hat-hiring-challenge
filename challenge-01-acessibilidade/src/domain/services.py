from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, col, func, select

from src.domain.models import Gasto, Orgao
from src.domain.schemas import (
    GastoFiltro,
    GastoResposta,
    OrgaoResposta,
    PaginacaoParams,
    PaginacaoResposta,
    ResumoCategoria,
    ResumoResposta,
    TopDespesa,
)


def _apply_filters(statement, filtro: GastoFiltro):
    if filtro.orgao:
        statement = statement.join(Orgao).where(Orgao.nome == filtro.orgao)
    if filtro.ano:
        statement = statement.where(Gasto.ano == filtro.ano)
    if filtro.mes:
        statement = statement.where(Gasto.mes == filtro.mes)
    if filtro.categoria:
        statement = statement.where(Gasto.categoria == filtro.categoria)
    if filtro.valor_min is not None:
        statement = statement.where(col(Gasto.valor) >= filtro.valor_min)
    if filtro.valor_max is not None:
        statement = statement.where(col(Gasto.valor) <= filtro.valor_max)

    return statement


def _to_dict(gasto: Gasto) -> dict:
    return {
        "id": gasto.id,
        "orgao": gasto.orgao.nome if gasto.orgao else "",
        "categoria": gasto.categoria,
        "descricao": gasto.descricao,
        "valor": gasto.valor,
        "data_lancamento": gasto.data_lancamento,
        "favorecido": gasto.favorecido,
    }


def _calcular_total_paginas(total: int, page_size: int) -> int:
    return (total + page_size - 1) // page_size


def lista_gastos(
    session: Session,
    filtro: GastoFiltro,
    paginacao: PaginacaoParams,
) -> PaginacaoResposta[GastoResposta]:
    statement = _apply_filters(select(Gasto), filtro)

    total = session.exec(
        select(func.count()).select_from(statement.subquery())
    ).one()

    total_pages = _calcular_total_paginas(total, paginacao.page_size)
    if total > 0 and paginacao.page > total_pages:
        return PaginacaoResposta(
            items=[],
            total=total,
            page=paginacao.page,
            page_size=paginacao.page_size,
            pages=total_pages,
            message=f"Página {paginacao.page} não existe. Total de páginas: {total_pages}",
        )

    offset = (paginacao.page - 1) * paginacao.page_size

    gastos = session.exec(
        statement.offset(offset).limit(paginacao.page_size)
    ).all()

    return PaginacaoResposta(
        items=[GastoResposta(**_to_dict(gasto)) for gasto in gastos],
        total=total,
        page=paginacao.page,
        page_size=paginacao.page_size,
        pages=total_pages,
    )


def get_gasto(session: Session, gasto_id: UUID) -> GastoResposta:
    gasto = session.exec(
        select(Gasto).where(Gasto.id == gasto_id)
    ).first()

    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto não encontrado")

    return GastoResposta(**_to_dict(gasto))


def get_resumo(session: Session, filtro: GastoFiltro) -> ResumoResposta:
    total_categoria_statement = _apply_filters(
        select(
            Gasto.categoria,
            func.sum(Gasto.valor).label("total"),
        ),
        filtro,
    ).group_by(Gasto.categoria)

    total_categoria = [
        ResumoCategoria(categoria=categoria, total=total)
        for categoria, total in session.exec(total_categoria_statement).all()
    ]

    top5_statement = _apply_filters(
        select(Gasto),
        filtro,
    ).order_by(col(Gasto.valor).desc()).limit(5)

    top5 = [
        TopDespesa(**_to_dict(gasto))
        for gasto in session.exec(top5_statement).all()
    ]

    return ResumoResposta(
        total_categoria=total_categoria,
        top5_maiores_despesas=top5,
    )


def lista_orgaos(
    session: Session,
    paginacao: PaginacaoParams,
) -> PaginacaoResposta[OrgaoResposta]:
    total = session.exec(
        select(func.count()).select_from(Orgao)
    ).one()

    total_pages = _calcular_total_paginas(total, paginacao.page_size)
    if total > 0 and paginacao.page > total_pages:
        return PaginacaoResposta(
            items=[],
            total=total,
            page=paginacao.page,
            page_size=paginacao.page_size,
            pages=total_pages,
            message=f"Página {paginacao.page} não existe. Total de páginas: {total_pages}",
        )

    offset = (paginacao.page - 1) * paginacao.page_size

    orgaos = session.exec(
        select(Orgao)
        .offset(offset)
        .limit(paginacao.page_size)
    ).all()

    return PaginacaoResposta(
        items=[OrgaoResposta.model_validate(orgao) for orgao in orgaos],
        total=total,
        page=paginacao.page,
        page_size=paginacao.page_size,
        pages=total_pages,
    )