"""Configuração dos testes automatizados.

Os testes usam um banco SQLite temporário criado com as MESMAS migrações do Alembic
usadas no banco real (`alembic upgrade head`). Assim, os testes também garantem
que as migrações funcionam.
"""
import itertools
import os
import shutil
import tempfile
from pathlib import Path

# A URL do banco de teste precisa ser definida ANTES de importar a aplicação,
# porque as configurações são lidas no momento da importação.
_PASTA_TEMPORARIA = Path(tempfile.mkdtemp(prefix="locadora_testes_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_PASTA_TEMPORARIA / 'teste.db').as_posix()}"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402

RAIZ_DO_PROJETO = Path(__file__).resolve().parents[1]
_contador = itertools.count(1)


@pytest.fixture(scope="session")
def alembic_cfg() -> Config:
    cfg = Config(str(RAIZ_DO_PROJETO / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ_DO_PROJETO / "alembic"))
    return cfg


@pytest.fixture(scope="session", autouse=True)
def banco_de_testes(alembic_cfg):
    command.upgrade(alembic_cfg, "head")
    yield
    engine.dispose()
    shutil.rmtree(_PASTA_TEMPORARIA, ignore_errors=True)


@pytest.fixture(autouse=True)
def limpar_tabelas():
    """Depois de cada teste, apaga os dados para o próximo começar do zero."""
    yield
    with engine.begin() as conexao:
        for tabela in reversed(Base.metadata.sorted_tables):
            conexao.execute(tabela.delete())


@pytest.fixture
def client():
    with TestClient(app) as cliente_http:
        yield cliente_http


# ---------------------------------------------------------------------------
# Geradores de dados válidos e fábricas de registros
# ---------------------------------------------------------------------------

def gerar_cpf(numero: int) -> str:
    """Gera um CPF válido (com dígitos verificadores corretos) a partir de um número."""
    digitos = [int(d) for d in f"{numero:09d}"]
    for tamanho in (9, 10):
        soma = sum(d * (tamanho + 1 - i) for i, d in enumerate(digitos[:tamanho]))
        digitos.append((soma * 10 % 11) % 10)
    return "".join(map(str, digitos))


def gerar_placa(numero: int) -> str:
    """Gera uma placa no padrão Mercosul: ABC1D23."""
    return f"TST{numero % 10}{chr(65 + (numero // 10) % 26)}{numero % 100:02d}"


@pytest.fixture
def nova_categoria(client):
    def criar(**campos) -> dict:
        n = next(_contador)
        dados = {"nome": f"Categoria {n}", "valor_diaria": 100.0} | campos
        resposta = client.post("/categorias", json=dados)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return criar


@pytest.fixture
def novo_veiculo(client, nova_categoria):
    def criar(**campos) -> dict:
        n = next(_contador)
        if "categoria_id" not in campos:
            campos["categoria_id"] = nova_categoria()["id"]
        dados = {
            "placa": gerar_placa(n),
            "marca": "Fiat",
            "modelo": "Argo",
            "ano": 2023,
            "cor": "Branco",
            "quilometragem": 10000,
        } | campos
        resposta = client.post("/veiculos", json=dados)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return criar


@pytest.fixture
def novo_cliente(client):
    def criar(**campos) -> dict:
        n = next(_contador)
        dados = {
            "nome": f"Cliente {n}",
            "cpf": gerar_cpf(n),
            "email": f"cliente{n}@teste.com",
            "telefone": "86999990000",
            "cnh": f"{n:011d}",
            "data_nascimento": "1990-01-15",
        } | campos
        resposta = client.post("/clientes", json=dados)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return criar


@pytest.fixture
def nova_locacao(client, novo_cliente, novo_veiculo):
    def criar(**campos) -> dict:
        if "cliente_id" not in campos:
            campos["cliente_id"] = novo_cliente()["id"]
        if "veiculo_id" not in campos:
            campos["veiculo_id"] = novo_veiculo()["id"]
        dados = {"data_retirada": "2026-10-20", "data_devolucao_prevista": "2026-10-25"} | campos
        resposta = client.post("/locacoes", json=dados)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return criar
