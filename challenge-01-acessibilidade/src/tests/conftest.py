from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from main import app
from src.domain.models import Gasto, Orgao
from src.infra.cache import cache
from src.infra.database import get_session


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as s:
        ms = Orgao(nome="Ministério da Saúde", sigla="MS")
        mec = Orgao(nome="Ministério da Educação", sigla="MEC")
        s.add_all([ms, mec])
        s.commit()
        s.refresh(ms)
        s.refresh(mec)

        s.add_all([
            Gasto(
                id=uuid4(), orgao_id=ms.id,
                categoria="Pessoal e Encargos Sociais",
                descricao="Pagamento de servidores ativos",
                valor=Decimal("1250000.00"),
                data_lancamento=date(2024, 1, 15),
                ano=2024, mes=1,
                favorecido="Folha MS Jan/2024",
            ),
            Gasto(
                id=uuid4(), orgao_id=ms.id,
                categoria="Investimentos",
                descricao="Compra de equipamentos médicos",
                valor=Decimal("850000.00"),
                data_lancamento=date(2024, 3, 22),
                ano=2024, mes=3,
                favorecido="MedEquip Ltda",
            ),
            Gasto(
                id=uuid4(), orgao_id=mec.id,
                categoria="Outras Despesas Correntes",
                descricao="Bolsas de pesquisa",
                valor=Decimal("320000.00"),
                data_lancamento=date(2023, 6, 10),
                ano=2023, mes=6,
                favorecido="CNPq",
            ),
            Gasto(
                id=uuid4(), orgao_id=ms.id,
                categoria="Pessoal e Encargos Sociais",
                descricao="13º salário servidores",
                valor=Decimal("2100000.00"),
                data_lancamento=date(2024, 12, 20),
                ano=2024, mes=12,
                favorecido="Folha MS Dez/2024",
            ),
            Gasto(
                id=uuid4(), orgao_id=mec.id,
                categoria="Investimentos",
                descricao="Construção de escola federal",
                valor=Decimal("5000000.00"),
                data_lancamento=date(2024, 7, 1),
                ano=2024, mes=7,
                favorecido="Construtora Federal SA",
            ),
        ])
        s.commit()

        yield s

    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def client(session: Session):
    def override():
        yield session

    app.dependency_overrides[get_session] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
