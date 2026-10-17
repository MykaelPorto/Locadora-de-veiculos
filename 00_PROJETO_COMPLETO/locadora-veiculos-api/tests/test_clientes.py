"""Testes de /clientes."""
from datetime import date

DADOS = {
    "nome": "Maria Souza",
    "cpf": "529.982.247-25",
    "email": "Maria.Souza@Email.com",
    "telefone": "(86) 99999-0000",
    "cnh": "12345678900",
    "data_nascimento": "1995-04-12",
}


def test_criar_cliente_retorna_201_e_normaliza_dados(client):
    resposta = client.post("/clientes", json=DADOS)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["cpf"] == "52998224725"
    assert corpo["email"] == "maria.souza@email.com"
    assert corpo["telefone"] == "86999990000"


def test_cpf_invalido_retorna_422(client):
    assert client.post("/clientes", json=DADOS | {"cpf": "123.456.789-00"}).status_code == 422


def test_email_invalido_retorna_422(client):
    assert client.post("/clientes", json=DADOS | {"email": "maria-sem-arroba"}).status_code == 422


def test_menor_de_idade_retorna_422(client):
    nascimento = date(date.today().year - 17, 1, 1).isoformat()
    resposta = client.post("/clientes", json=DADOS | {"data_nascimento": nascimento})
    assert resposta.status_code == 422


def test_cpf_duplicado_retorna_409(client):
    client.post("/clientes", json=DADOS)
    resposta = client.post("/clientes", json=DADOS | {"email": "outro@email.com", "cnh": "99999999999"})
    assert resposta.status_code == 409
    assert "CPF" in resposta.json()["detail"]


def test_email_duplicado_retorna_409(client):
    client.post("/clientes", json=DADOS)
    resposta = client.post("/clientes", json=DADOS | {"cpf": "111.444.777-35", "cnh": "99999999999"})
    assert resposta.status_code == 409
    assert "e-mail" in resposta.json()["detail"]


def test_buscar_cliente_inexistente_retorna_404(client):
    assert client.get("/clientes/999").status_code == 404


def test_buscar_clientes_por_nome(client, novo_cliente):
    novo_cliente(nome="Ana Paula")
    novo_cliente(nome="Bruno Lima")
    resposta = client.get("/clientes", params={"nome": "ana"})
    assert [c["nome"] for c in resposta.json()] == ["Ana Paula"]


def test_atualizar_cliente(client, novo_cliente):
    cliente = novo_cliente()
    resposta = client.patch(f"/clientes/{cliente['id']}", json={"telefone": "(86) 98888-1111"})
    assert resposta.status_code == 200
    assert resposta.json()["telefone"] == "86988881111"


def test_atualizar_para_email_de_outro_cliente_retorna_409(client, novo_cliente):
    primeiro = novo_cliente()
    segundo = novo_cliente()
    resposta = client.patch(f"/clientes/{segundo['id']}", json={"email": primeiro["email"]})
    assert resposta.status_code == 409


def test_cpf_nao_pode_ser_alterado(client, novo_cliente):
    cliente = novo_cliente()
    assert client.patch(f"/clientes/{cliente['id']}", json={"cpf": "11144477735"}).status_code == 422


def test_remover_cliente_retorna_204(client, novo_cliente):
    cliente = novo_cliente()
    assert client.delete(f"/clientes/{cliente['id']}").status_code == 204


def test_remover_cliente_com_locacoes_retorna_409(client, nova_locacao):
    locacao = nova_locacao()
    assert client.delete(f"/clientes/{locacao['cliente_id']}").status_code == 409


def test_historico_de_locacoes_do_cliente(client, novo_cliente, nova_locacao):
    cliente = novo_cliente()
    primeira = nova_locacao(cliente_id=cliente["id"])
    segunda = nova_locacao(cliente_id=cliente["id"])
    resposta = client.get(f"/clientes/{cliente['id']}/locacoes")
    assert resposta.status_code == 200
    assert [loc["id"] for loc in resposta.json()] == [segunda["id"], primeira["id"]]
