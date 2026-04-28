from uuid import uuid4

from sqlmodel import select

from src.domain.models import Gasto


def test_listar_gastos_filtro_vazio(client):
    """Empty filter returns all records."""
    r = client.get("/gastos")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5
    assert data["page"] == 1


def test_listar_gastos_filtro_combinado(client):
    """orgao + ano filters return only matching records."""
    r = client.get("/gastos?orgao=Ministério da Saúde&ano=2024")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    for item in data["items"]:
        assert item["orgao"] == "Ministério da Saúde"


def test_listar_gastos_pagina_inexistente(client):
    """Page beyond range returns 200 with empty items and descriptive message."""
    r = client.get("/gastos?page=9999")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 5
    assert "não existe" in data["message"]


def test_listar_gastos_valor_min_maior_que_valor_max(client):
    """valor_min > valor_max triggers 422 validation error."""
    r = client.get("/gastos?valor_min=1000000&valor_max=500")
    assert r.status_code == 422


def test_listar_gastos_filtro_categoria(client):
    """Filtering by categoria returns only matching records."""
    r = client.get("/gastos?categoria=Investimentos")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["categoria"] == "Investimentos"


def test_listar_gastos_filtro_valor_min(client):
    """valor_min filters out records below threshold."""
    r = client.get("/gastos?valor_min=1000000")
    assert r.status_code == 200
    data = r.json()
    for item in data["items"]:
        assert float(item["valor"]) >= 1_000_000


def test_listar_gastos_paginacao(client):
    """page_size limits items; pages count is correct."""
    r = client.get("/gastos?page=1&page_size=2")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 2
    assert data["pages"] == 3


def test_listar_gastos_page_size_maximo(client):
    """page_size > 100 triggers 422."""
    r = client.get("/gastos?page_size=101")
    assert r.status_code == 422


def test_detalhar_gasto_encontrado(client, session):
    """GET /gastos/{id} returns the correct record."""
    gasto = session.exec(select(Gasto)).first()
    r = client.get(f"/gastos/{gasto.id}")
    assert r.status_code == 200
    assert r.json()["id"] == str(gasto.id)


def test_detalhar_gasto_nao_encontrado(client):
    """GET /gastos/{id} with unknown UUID returns 404."""
    r = client.get(f"/gastos/{uuid4()}")
    assert r.status_code == 404


def test_listar_orgaos(client):
    """GET /orgaos returns paginated organ list."""
    r = client.get("/orgaos")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    nomes = {item["nome"] for item in data["items"]}
    assert "Ministério da Saúde" in nomes
    assert "Ministério da Educação" in nomes


def test_listar_orgaos_paginacao(client):
    """Pagination on /orgaos respects page_size."""
    r = client.get("/orgaos?page=1&page_size=1")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 1
    assert data["pages"] == 2
