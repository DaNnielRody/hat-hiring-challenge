import random
from datetime import date
from decimal import Decimal

from faker import Faker
from sqlmodel import Session, select

from src.domain.models import Gasto, Orgao
from src.infra.database import create_db_and_tables, engine

fake = Faker("pt_BR")

ORGAOS = [
    ("Ministério da Saúde", "MS"),
    ("Ministério da Educação", "MEC"),
    ("Ministério da Defesa", "MD"),
    ("Ministério da Fazenda", "MF"),
    ("Ministério do Trabalho e Emprego", "MTE"),
    ("Ministério da Infraestrutura", "MINFRA"),
    ("Ministério da Ciência, Tecnologia e Inovações", "MCTI"),
    ("Ministério das Relações Exteriores", "MRE"),
    ("Ministério da Justiça e Segurança Pública", "MJSP"),
    ("Ministério do Meio Ambiente", "MMA"),
    ("Ministério da Agricultura, Pecuária e Abastecimento", "MAPA"),
    ("Ministério do Desenvolvimento Social", "MDS"),
    ("Ministério da Previdência Social", "MPS"),
    ("Ministério das Comunicações", "MCOM"),
    ("Ministério do Turismo", "MTur"),
]

CATEGORIAS = [
    "Pessoal e Encargos Sociais",
    "Juros e Encargos da Dívida",
    "Outras Despesas Correntes",
    "Investimentos",
    "Inversões Financeiras",
    "Amortização da Dívida",
]

DESCRICOES = {
    "Pessoal e Encargos Sociais": [
        "Pagamento de servidores ativos",
        "Pagamento de aposentados e pensionistas",
        "Encargos patronais INSS",
        "13º salário servidores",
        "Férias servidores",
    ],
    "Juros e Encargos da Dívida": [
        "Juros da dívida interna",
        "Juros da dívida externa",
        "Encargos financeiros contratuais",
    ],
    "Outras Despesas Correntes": [
        "Auxílio-alimentação servidores",
        "Serviços de limpeza e conservação",
        "Material de consumo",
        "Passagens e diárias",
        "Serviços de tecnologia da informação",
        "Publicidade legal",
        "Bolsas de pesquisa e extensão",
    ],
    "Investimentos": [
        "Construção de unidade hospitalar",
        "Aquisição de equipamentos médicos",
        "Obras de infraestrutura viária",
        "Modernização de sistemas informatizados",
        "Construção de escola federal",
        "Aquisição de aeronaves",
    ],
    "Inversões Financeiras": [
        "Aquisição de imóveis",
        "Participação em fundos públicos",
        "Concessão de empréstimos",
    ],
    "Amortização da Dívida": [
        "Amortização da dívida interna",
        "Amortização da dívida externa",
        "Refinanciamento de operações de crédito",
    ],
}

VALOR_RANGES = {
    "Pessoal e Encargos Sociais": (500_000, 50_000_000),
    "Juros e Encargos da Dívida": (1_000_000, 100_000_000),
    "Outras Despesas Correntes": (10_000, 5_000_000),
    "Investimentos": (100_000, 30_000_000),
    "Inversões Financeiras": (500_000, 20_000_000),
    "Amortização da Dívida": (1_000_000, 50_000_000),
}


def seed(total: int = 600) -> None:
    create_db_and_tables()

    with Session(engine) as session:
        if session.exec(select(Gasto)).first():
            print("Banco já populado, pulando seed.")
            return

        Faker.seed(42)
        random.seed(42)

        orgaos = []
        for nome, sigla in ORGAOS:
            orgao = Orgao(nome=nome, sigla=sigla)
            session.add(orgao)
            orgaos.append(orgao)
        session.commit()
        for orgao in orgaos:
            session.refresh(orgao)

        for _ in range(total):
            orgao = random.choice(orgaos)
            categoria = random.choice(CATEGORIAS)
            v_min, v_max = VALOR_RANGES[categoria]
            data: date = fake.date_between(start_date=date(2023, 1, 1), end_date=date(2024, 12, 31))

            session.add(Gasto(
                orgao_id=orgao.id,
                categoria=categoria,
                descricao=random.choice(DESCRICOES[categoria]),
                valor=Decimal(str(round(random.uniform(v_min, v_max), 2))),
                data_lancamento=data,
                ano=data.year,
                mes=data.month,
                favorecido=fake.company(),
            ))

        session.commit()
        print(f"{total} gastos inseridos para {len(orgaos)} órgãos.")


if __name__ == "__main__":
    seed()
