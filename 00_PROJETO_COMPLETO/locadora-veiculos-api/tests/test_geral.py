"""Testes gerais: rota raiz, Swagger e migrações."""
from alembic import command


def test_raiz_informa_documentacao(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert resposta.json()["documentacao"] == "/docs"


def test_swagger_disponivel(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


ROTAS = {"categorias": "categoria_id", "veiculos": "veiculo_id", "clientes": "cliente_id", "locacoes": "locacao_id"}


def test_api_usa_os_quatro_metodos_http_em_todos_os_modelos(client):
    paths = client.get("/openapi.json").json()["paths"]
    for recurso, parametro in ROTAS.items():
        metodos = set(paths[f"/{recurso}"]) | set(paths[f"/{recurso}/{{{parametro}}}"])
        assert {"get", "post", "patch", "delete"} <= metodos, recurso


def test_rotas_de_criacao_documentam_status_201(client):
    paths = client.get("/openapi.json").json()["paths"]
    for recurso in ("categorias", "veiculos", "clientes", "locacoes"):
        assert "201" in paths[f"/{recurso}"]["post"]["responses"]


def test_migracoes_estao_sincronizadas_com_os_modelos(alembic_cfg):
    """Falha se algum modelo foi alterado sem gerar a migração correspondente."""
    command.check(alembic_cfg)
