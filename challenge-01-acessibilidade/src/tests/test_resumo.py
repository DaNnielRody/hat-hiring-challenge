def test_resumo_miss_no_primeiro_acesso(client):
    """First /resumo call returns X-Cache: MISS."""
    r = client.get("/gastos/resumo")
    assert r.status_code == 200
    assert r.headers["x-cache"] == "MISS"


def test_resumo_hit_no_segundo_acesso(client):
    """Second identical /resumo call returns X-Cache: HIT."""
    client.get("/gastos/resumo")
    r = client.get("/gastos/resumo")
    assert r.status_code == 200
    assert r.headers["x-cache"] == "HIT"


def test_resumo_cache_por_combinacao_de_filtros(client):
    """Different filter combos get separate cache entries."""
    r1 = client.get("/gastos/resumo?ano=2024")
    assert r1.headers["x-cache"] == "MISS"

    r2 = client.get("/gastos/resumo?ano=2023")
    assert r2.headers["x-cache"] == "MISS"

    r3 = client.get("/gastos/resumo?ano=2024")
    assert r3.headers["x-cache"] == "HIT"


def test_resumo_estrutura_resposta(client):
    """Response has total_categoria and top5_maiores_despesas."""
    r = client.get("/gastos/resumo")
    data = r.json()
    assert "total_categoria" in data
    assert "top5_maiores_despesas" in data
    assert len(data["top5_maiores_despesas"]) <= 5


def test_resumo_top5_ordenado_por_valor_desc(client):
    """top5_maiores_despesas is sorted by valor descending."""
    r = client.get("/gastos/resumo")
    valores = [float(item["valor"]) for item in r.json()["top5_maiores_despesas"]]
    assert valores == sorted(valores, reverse=True)


def test_resumo_total_categoria_soma_correta(client):
    """total_categoria sums correctly per category."""
    r = client.get("/gastos/resumo")
    cats = {c["categoria"]: float(c["total"]) for c in r.json()["total_categoria"]}
    # Pessoal e Encargos Sociais: 1_250_000 + 2_100_000 = 3_350_000
    assert abs(cats["Pessoal e Encargos Sociais"] - 3_350_000.00) < 0.01
    # Investimentos: 850_000 + 5_000_000 = 5_850_000
    assert abs(cats["Investimentos"] - 5_850_000.00) < 0.01


def test_resumo_filtro_orgao(client):
    """Filtered /resumo only aggregates matching records."""
    r = client.get("/gastos/resumo?orgao=Ministério da Educação")
    data = r.json()
    cats = {c["categoria"]: float(c["total"]) for c in data["total_categoria"]}
    assert "Pessoal e Encargos Sociais" not in cats
    assert "Outras Despesas Correntes" in cats


def test_resumo_valor_min_maior_que_valor_max(client):
    """valor_min > valor_max on /resumo returns 422."""
    r = client.get("/gastos/resumo?valor_min=9999&valor_max=1")
    assert r.status_code == 422


def test_resumo_lru_eviction(client):
    """101ª combinação diferente evicta a entrada LRU; próximo acesso à 1ª combo é MISS."""
    # preenche os 100 slots
    for ano in range(1900, 2000):
        r = client.get(f"/gastos/resumo?ano={ano}")
        assert r.headers["x-cache"] == "MISS"

    # ano=1901..1999 - HIT; 1900 sai.
    assert client.get("/gastos/resumo?ano=1999").headers["x-cache"] == "HIT"

    # ano=2000 (101ª combinação) remove LRU = ano=1900
    assert client.get("/gastos/resumo?ano=2000").headers["x-cache"] == "MISS"

    # ano=2000 e ano=1999 ainda no cache
    assert client.get("/gastos/resumo?ano=2000").headers["x-cache"] == "HIT"
    assert client.get("/gastos/resumo?ano=1999").headers["x-cache"] == "HIT"

    # ano=1900 foi removido — nova consulta é MISS
    assert client.get("/gastos/resumo?ano=1900").headers["x-cache"] == "MISS"


def test_resumo_100_chamadas_mesmos_filtros(client):
    """100 chamadas idênticas resultam em 1 MISS e 99 HITs — banco consultado uma vez."""
    respostas = [client.get("/gastos/resumo?ano=2024") for _ in range(100)]

    assert all(r.status_code == 200 for r in respostas)
    assert respostas[0].headers["x-cache"] == "MISS"
    assert all(r.headers["x-cache"] == "HIT" for r in respostas[1:])

    misses = sum(1 for r in respostas if r.headers["x-cache"] == "MISS")
    assert misses == 1
