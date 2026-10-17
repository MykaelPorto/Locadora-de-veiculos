"""Testes de /categorias."""


def test_criar_categoria_retorna_201(client):
    resposta = client.post(
        "/categorias", json={"nome": "SUV", "descricao": "Utilitários esportivos", "valor_diaria": 220.5}
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] > 0
    assert corpo["nome"] == "SUV"
    assert corpo["valor_diaria"] == 220.5
    assert corpo["criado_em"]


def test_nome_duplicado_retorna_409(client, nova_categoria):
    nova_categoria(nome="SUV")
    resposta = client.post("/categorias", json={"nome": "suv", "valor_diaria": 100})
    assert resposta.status_code == 409


def test_valor_diaria_negativo_retorna_422(client):
    resposta = client.post("/categorias", json={"nome": "SUV", "valor_diaria": -10})
    assert resposta.status_code == 422


def test_valor_diaria_com_tres_casas_decimais_retorna_422(client):
    resposta = client.post("/categorias", json={"nome": "SUV", "valor_diaria": 99.999})
    assert resposta.status_code == 422


def test_campo_obrigatorio_ausente_retorna_422(client):
    resposta = client.post("/categorias", json={"nome": "SUV"})
    assert resposta.status_code == 422


def test_campo_desconhecido_retorna_422(client):
    resposta = client.post("/categorias", json={"nome": "SUV", "valor_diaria": 100, "preco": 1})
    assert resposta.status_code == 422


def test_buscar_categoria_inexistente_retorna_404(client):
    resposta = client.get("/categorias/999")
    assert resposta.status_code == 404
    assert "não existe" in resposta.json()["detail"]


def test_listar_categorias(client, nova_categoria):
    nova_categoria()
    nova_categoria()
    resposta = client.get("/categorias")
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_atualizar_parcialmente(client, nova_categoria):
    categoria = nova_categoria(nome="Econômico", valor_diaria=100)
    resposta = client.patch(f"/categorias/{categoria['id']}", json={"valor_diaria": 120})
    assert resposta.status_code == 200
    assert resposta.json()["valor_diaria"] == 120
    assert resposta.json()["nome"] == "Econômico"


def test_atualizar_com_nulo_em_campo_obrigatorio_retorna_422(client, nova_categoria):
    categoria = nova_categoria()
    resposta = client.patch(f"/categorias/{categoria['id']}", json={"nome": None})
    assert resposta.status_code == 422


def test_atualizar_para_nome_ja_usado_retorna_409(client, nova_categoria):
    nova_categoria(nome="SUV")
    outra = nova_categoria(nome="Sedan")
    resposta = client.patch(f"/categorias/{outra['id']}", json={"nome": "SUV"})
    assert resposta.status_code == 409


def test_atualizar_inexistente_retorna_404(client):
    assert client.patch("/categorias/999", json={"valor_diaria": 10}).status_code == 404


def test_remover_categoria_retorna_204(client, nova_categoria):
    categoria = nova_categoria()
    resposta = client.delete(f"/categorias/{categoria['id']}")
    assert resposta.status_code == 204
    assert resposta.content == b""
    assert client.get(f"/categorias/{categoria['id']}").status_code == 404


def test_remover_categoria_com_veiculos_retorna_409(client, novo_veiculo):
    veiculo = novo_veiculo()
    resposta = client.delete(f"/categorias/{veiculo['categoria_id']}")
    assert resposta.status_code == 409


def test_listar_veiculos_da_categoria_usa_relacionamento(client, nova_categoria, novo_veiculo):
    categoria = nova_categoria()
    novo_veiculo(categoria_id=categoria["id"])
    novo_veiculo(categoria_id=categoria["id"])
    novo_veiculo()  # outra categoria
    resposta = client.get(f"/categorias/{categoria['id']}/veiculos")
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2
    assert all(v["categoria"]["id"] == categoria["id"] for v in resposta.json())
