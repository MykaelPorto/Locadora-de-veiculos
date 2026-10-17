"""Testes de /veiculos."""

DADOS = {"placa": "QRS1A23", "marca": "Jeep", "modelo": "Compass", "ano": 2024, "cor": "Prata", "quilometragem": 15000}


def test_criar_veiculo_retorna_201_com_categoria_aninhada(client, nova_categoria):
    categoria = nova_categoria(nome="SUV", valor_diaria=220)
    resposta = client.post("/veiculos", json=DADOS | {"categoria_id": categoria["id"]})
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "disponivel"
    assert corpo["categoria"] == {"id": categoria["id"], "nome": "SUV", "valor_diaria": 220.0}


def test_placa_e_normalizada(client, nova_categoria):
    categoria = nova_categoria()
    resposta = client.post("/veiculos", json=DADOS | {"placa": "qrs-1a23", "categoria_id": categoria["id"]})
    assert resposta.status_code == 201
    assert resposta.json()["placa"] == "QRS1A23"


def test_categoria_inexistente_retorna_404(client):
    """Validação de integridade: a chave estrangeira categoria_id precisa existir."""
    resposta = client.post("/veiculos", json=DADOS | {"categoria_id": 999})
    assert resposta.status_code == 404
    assert "Categoria com id 999" in resposta.json()["detail"]


def test_placa_duplicada_retorna_409(client, novo_veiculo, nova_categoria):
    novo_veiculo(placa="QRS1A23")
    resposta = client.post("/veiculos", json=DADOS | {"categoria_id": nova_categoria()["id"]})
    assert resposta.status_code == 409


def test_placa_invalida_retorna_422(client, nova_categoria):
    resposta = client.post("/veiculos", json=DADOS | {"placa": "12ABC34", "categoria_id": nova_categoria()["id"]})
    assert resposta.status_code == 422


def test_ano_invalido_retorna_422(client, nova_categoria):
    resposta = client.post("/veiculos", json=DADOS | {"ano": 1950, "categoria_id": nova_categoria()["id"]})
    assert resposta.status_code == 422


def test_buscar_veiculo_inexistente_retorna_404(client):
    assert client.get("/veiculos/999").status_code == 404


def test_filtrar_por_status_e_categoria(client, nova_categoria, novo_veiculo):
    categoria = nova_categoria()
    v1 = novo_veiculo(categoria_id=categoria["id"])
    novo_veiculo(categoria_id=categoria["id"])
    novo_veiculo()
    client.patch(f"/veiculos/{v1['id']}", json={"status": "manutencao"})

    assert len(client.get("/veiculos").json()) == 3
    assert len(client.get("/veiculos", params={"categoria_id": categoria["id"]}).json()) == 2
    em_manutencao = client.get("/veiculos", params={"status": "manutencao"}).json()
    assert [v["id"] for v in em_manutencao] == [v1["id"]]


def test_colocar_em_manutencao(client, novo_veiculo):
    veiculo = novo_veiculo()
    resposta = client.patch(f"/veiculos/{veiculo['id']}", json={"status": "manutencao", "cor": "Preto"})
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "manutencao"
    assert resposta.json()["cor"] == "Preto"


def test_definir_status_alugado_manualmente_retorna_422(client, novo_veiculo):
    veiculo = novo_veiculo()
    assert client.patch(f"/veiculos/{veiculo['id']}", json={"status": "alugado"}).status_code == 422


def test_alterar_status_de_veiculo_alugado_retorna_409(client, nova_locacao):
    locacao = nova_locacao()
    resposta = client.patch(f"/veiculos/{locacao['veiculo_id']}", json={"status": "manutencao"})
    assert resposta.status_code == 409


def test_trocar_para_categoria_inexistente_retorna_404(client, novo_veiculo):
    veiculo = novo_veiculo()
    assert client.patch(f"/veiculos/{veiculo['id']}", json={"categoria_id": 999}).status_code == 404


def test_quilometragem_nao_pode_diminuir(client, novo_veiculo):
    veiculo = novo_veiculo(quilometragem=10000)
    assert client.patch(f"/veiculos/{veiculo['id']}", json={"quilometragem": 9000}).status_code == 422


def test_remover_veiculo_retorna_204(client, novo_veiculo):
    veiculo = novo_veiculo()
    assert client.delete(f"/veiculos/{veiculo['id']}").status_code == 204
    assert client.get(f"/veiculos/{veiculo['id']}").status_code == 404


def test_remover_veiculo_com_locacoes_retorna_409(client, nova_locacao):
    locacao = nova_locacao()
    assert client.delete(f"/veiculos/{locacao['veiculo_id']}").status_code == 409


def test_historico_de_locacoes_do_veiculo(client, nova_locacao):
    locacao = nova_locacao()
    resposta = client.get(f"/veiculos/{locacao['veiculo_id']}/locacoes")
    assert resposta.status_code == 200
    assert [loc["id"] for loc in resposta.json()] == [locacao["id"]]
