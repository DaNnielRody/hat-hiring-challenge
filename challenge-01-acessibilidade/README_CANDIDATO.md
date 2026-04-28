# Challenge 01 — Painel de Transparência Pública

## Como Rodar

### Local

```bash
uv pip install -e ".[dev]"
uv run uvicorn main:app --reload
```

Acesse `http://localhost:8000/docs` para explorar a API via Swagger UI — todos os endpoints, parâmetros e schemas estão documentados automaticamente pelo FastAPI.

O banco SQLite e os dados de seed são criados no primeiro startup. Nenhum passo de migração manual necessário.

### Docker

```bash
docker compose up
```

API disponível em `http://localhost:8009/docs`.

O `docker-compose.yml` monta o diretório local em `/app` via volume. Como esse mount sobrescreve o filesystem do container em runtime, o diretório `data/` (onde o SQLite reside) é criado programaticamente na inicialização do módulo `database.py` — sem dependência de `RUN mkdir` no Dockerfile.

### Testes

```bash
uv run pytest
uv run pytest --cov=src --cov-report=html
```

Cobertura atual: **~98%**. Os testes usam SQLite em memória com `StaticPool` — sem mocks de banco. Toda query passa pelo ORM real, o que garante que filtros, paginação e agregações são testados contra SQL de verdade.

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/gastos` | Lista gastos com filtros e paginação |
| `GET` | `/gastos/{id}` | Detalhe de um gasto |
| `GET` | `/gastos/resumo` | Agregações com cache (`X-Cache` header) |
| `GET` | `/orgaos` | Lista órgãos disponíveis |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Documentação OpenAPI interativa |

### Testando a API

O arquivo `api.http` na raiz do projeto contém todas as requisições prontas. Para usá-lo, instale a extensão [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) no VS Code — cada bloco vira um botão "Send Request" inline. A variável `@baseUrl` no topo do arquivo facilita trocar entre local (`8000`) e Docker (`8009`) em uma linha.

### Exemplos com curl

```bash
# Listar gastos com filtros combinados
curl "http://localhost:8000/gastos?orgao=Ministério da Saúde&ano=2024&categoria=Investimentos&page_size=5"

# Detalhe de um gasto
curl "http://localhost:8000/gastos/04b55432-60ee-46f8-bf51-716604d59f0d"

# Resumo — primeira chamada retorna X-Cache: MISS, chamadas seguintes X-Cache: HIT
curl -i "http://localhost:8000/gastos/resumo?ano=2024&mes=3"

# Filtro de valor com paginação
curl "http://localhost:8000/gastos?valor_min=1000000&valor_max=50000000&page=2&page_size=20"

# Listar órgãos
curl "http://localhost:8000/orgaos"
```

### Filtros disponíveis em `/gastos` e `/gastos/resumo`

| Parâmetro | Tipo | Exemplo |
|-----------|------|---------|
| `orgao` | string | `?orgao=Ministério da Saúde` |
| `ano` | int | `?ano=2024` |
| `mes` | int (1–12) | `?mes=3` |
| `categoria` | enum | `?categoria=Investimentos` |
| `valor_min` | decimal ≥ 0 | `?valor_min=1000.00` |
| `valor_max` | decimal ≥ 0 | `?valor_max=500000.00` |
| `page` | int ≥ 1 | `?page=2` |
| `page_size` | int (1–100) | `?page_size=50` |

---

## Decisões de Design

### Modelagem

As entidades foram separadas conforme o payload exibido no próprio challenge. Ao pesquisar o Portal da Transparência, confirmei que aquelas categorias de despesa existem de fato — então optei por um `StrEnum` nativo do Python ao invés de criar uma entidade separada. Evita um join desnecessário para dados que dificilmente mudam.

### Schemas como DTOs

Os schemas foram pensados seguindo a abordagem de DTOs: cada modelo é semanticamente referente ao seu tipo — `GastoResposta` para o retorno de um gasto, `ResumoResposta` para agregações, `PaginacaoResposta[T]` para qualquer listagem paginada. A função `_to_dict` em `services.py` funciona como um `toModel`, normalizando o objeto ORM para dicionário antes de construir o schema de resposta. Isso centraliza o mapeamento em um único lugar. Os filtros em `GastoFiltro` seguem o mesmo princípio: agrupados em um modelo com validações declarativas, reutilizados entre `/gastos` e `/gastos/resumo` sem duplicação.

### Validação de Parâmetros

Os campos de `GastoFiltro` usam `Field` do Pydantic com constraints declarativas (`ge=1, le=12` para mês, `ge=1900, le=2100` para ano, `ge=0` para valores). Isso gera documentação OpenAPI automática e retorna 422 com mensagem precisa antes de qualquer lógica de negócio.

Para a validação cruzada `valor_min > valor_max`, usei `@model_validator(mode="after")` — roda depois que todos os campos já foram validados individualmente, garantindo que os valores existem antes de compará-los.

Paginação fora do intervalo seguiu a convenção REST: retorna `200` com `items: []` e um campo `message` descritivo no body, em vez de um código de erro. O cliente continua recebendo metadados úteis (`total`, `pages`) e sabe exatamente o motivo da lista vazia sem precisar tratar uma exceção.

### Cache

O requisito pede que `/gastos/resumo` seja recalculado **no máximo uma vez a cada 60 segundos** por combinação de filtros — mesmo que chamado 100 vezes no intervalo. `TTLCache(maxsize=100, ttl=60)` do `cachetools` resolve exatamente isso: o `maxsize=100` vem diretamente do requisito. Quando o limite é atingido, a entrada menos recentemente usada é removida (LRU).

`functools.lru_cache` foi descartado por não suportar TTL nativo. O cache vive como singleton de módulo — uma instância por processo, zero overhead por request.

O header `X-Cache: HIT/MISS` expõe o comportamento ao consumidor. Interpretei esse endpoint como algo analítico. Em respostas `HIT`, o campo `cache_info` do body também informa explicitamente a defasagem possível:

```json
{
  "cache_info": "Dados em cache — podem ter até 60 segundos de defasagem em relação ao banco."
}
```

Isso torna o contrato visível tanto para quem inspeciona headers quanto para quem só lê o body — útil em clientes que não expõem headers facilmente.

### Banco de Dados

O `DATABASE_URL` é lido de variável de ambiente com SQLite como padrão:

```
DATABASE_URL=sqlite:///./data/challenge.db  # padrão local e Docker
DATABASE_URL=postgresql://user:pass@host/db  # produção
```

Trocar de banco é mudar a variável — nenhum código muda. Para produção com carga real, a sequência de mudanças seria: PostgreSQL com connection pool → réplica de leitura para `/resumo` → Redis no lugar do `TTLCache` para cache distribuído entre instâncias.

### Testes

A sessão de banco é injetada via `Depends(get_session)`. Nos testes, esse dependency é sobrescrito com uma sessão apontando para SQLite em memória com `StaticPool`. Cada teste recebe um banco isolado com dados de fixture inseridos via ORM — sem `MagicMock` sobre `session.exec` ou similar. Toda query, join e agregação executa SQL de verdade; se um filtro estiver errado, o teste quebra contra o banco, não contra um retorno fabricado.
