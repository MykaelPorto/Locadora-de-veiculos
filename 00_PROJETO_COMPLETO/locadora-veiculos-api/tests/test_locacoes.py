"""Testes de /locacoes — inclui as regras de negócio principais."""


def test_criar_locacao_calcula_valor_e_aluga_o_veiculo(client, nova_categoria, novo_veiculo, novo_cliente):
    categoria = nova_categoria(valor_diaria=150)
    veiculo = novo_veiculo(categoria_id=categoria["id"], quilometragem=10000)
    cliente = novo_cliente()

    resposta = client.post(
        "/locacoes",
        json={
            "cliente_id": cliente["id"],
            "veiculo_id": veiculo["id"],
            "data_retirada": "2026-10-20",
            "data_devolucao_prevista": "2026-10-25",
        },
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "ativa"
    assert corpo["valor_diaria"] == 150.0
    assert corpo["valor_previsto"] == 750.0  # 5 diárias x 150
    assert corpo["valor_total"] is None
    assert corpo["quilometragem_inicial"] == 10000
    assert corpo["cliente"]["id"] == cliente["id"]
    assert corpo["veiculo"]["placa"] == veiculo["placa"]

    assert client.get(f"/veiculos/{veiculo['id']}").json()["status"] == "alugado"


def test_cliente_inexistente_retorna_404(client, novo_veiculo):
    """Validação de integridade: cliente_id precisa existir."""
    veiculo = novo_veiculo()
    resposta = client.post(
        "/locacoes", json={"cliente_id": 999, "veiculo_id": veiculo["id"], "data_devolucao_prevista": "2099-01-01"}
    )
    assert resposta.status_code == 404
    assert "Cliente com id 999" in resposta.json()["detail"]


def test_veiculo_inexistente_retorna_404(client, novo_cliente):
    """Validação de integridade: veiculo_id precisa existir."""
    cliente = novo_cliente()
    resposta = client.post(
        "/locacoes", json={"cliente_id": cliente["id"], "veiculo_id": 999, "data_devolucao_prevista": "2099-01-01"}
    )
    assert resposta.status_code == 404
    assert "Veículo com id 999" in resposta.json()["detail"]


def test_veiculo_ja_alugado_retorna_409(client, nova_locacao, novo_cliente):
    locacao = nova_locacao()
    resposta = client.post(
        "/locacoes",
        json={
            "cliente_id": novo_cliente()["id"],
            "veiculo_id": locacao["veiculo_id"],
            "data_retirada": "2026-10-21",
            "data_devolucao_prevista": "2026-10-22",
        },
    )
    assert resposta.status_code == 409


def test_veiculo_em_manutencao_retorna_409(client, novo_veiculo, novo_cliente):
    veiculo = novo_veiculo()
    client.patch(f"/veiculos/{veiculo['id']}", json={"status": "manutencao"})
    resposta = client.post(
        "/locacoes",
        json={"cliente_id": novo_cliente()["id"], "veiculo_id": veiculo["id"], "data_devolucao_prevista": "2099-01-01"},
    )
    assert resposta.status_code == 409


def test_devolucao_prevista_antes_da_retirada_retorna_422(client, novo_veiculo, novo_cliente):
    resposta = client.post(
        "/locacoes",
        json={
            "cliente_id": novo_cliente()["id"],
            "veiculo_id": novo_veiculo()["id"],
            "data_retirada": "2026-10-20",
            "data_devolucao_prevista": "2026-10-19",
        },
    )
    assert resposta.status_code == 422


def test_data_retirada_padrao_e_hoje(client, novo_veiculo, novo_cliente):
    from datetime import date

    resposta = client.post(
        "/locacoes",
        json={"cliente_id": novo_cliente()["id"], "veiculo_id": novo_veiculo()["id"], "data_devolucao_prevista": "2099-01-01"},
    )
    assert resposta.status_code == 201
    assert resposta.json()["data_retirada"] == date.today().isoformat()


def test_buscar_locacao_inexistente_retorna_404(client):
    assert client.get("/locacoes/999").status_code == 404


def test_devolucao_calcula_valor_total_e_libera_o_veiculo(client, nova_categoria, novo_veiculo, nova_locacao):
    categoria = nova_categoria(valor_diaria=150)
    veiculo = novo_veiculo(categoria_id=categoria["id"], quilometragem=10000)
    locacao = nova_locacao(veiculo_id=veiculo["id"])  # 20/10 a 25/10

    resposta = client.post(
        f"/locacoes/{locacao['id']}/devolucao",
        json={"quilometragem_final": 10500, "data_devolucao_real": "2026-10-26", "observacoes": "Tanque cheio"},
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "finalizada"
    assert corpo["valor_total"] == 900.0  # devolveu 1 dia depois: 6 diárias x 150
    assert corpo["quilometragem_final"] == 10500

    veiculo_depois = client.get(f"/veiculos/{veiculo['id']}").json()
    assert veiculo_depois["status"] == "disponivel"
    assert veiculo_depois["quilometragem"] == 10500


def test_devolucao_no_mesmo_dia_cobra_uma_diaria(client, nova_categoria, novo_veiculo, nova_locacao):
    veiculo = novo_veiculo(categoria_id=nova_categoria(valor_diaria=100)["id"])
    locacao = nova_locacao(veiculo_id=veiculo["id"])
    resposta = client.post(
        f"/locacoes/{locacao['id']}/devolucao",
        json={"quilometragem_final": 10050, "data_devolucao_real": "2026-10-20"},
    )
    assert resposta.json()["valor_total"] == 100.0


def test_devolucao_duplicada_retorna_409(client, nova_locacao):
    locacao = nova_locacao()
    dados = {"quilometragem_final": 10500, "data_devolucao_real": "2026-10-25"}
    assert client.post(f"/locacoes/{locacao['id']}/devolucao", json=dados).status_code == 200
    assert client.post(f"/locacoes/{locacao['id']}/devolucao", json=dados).status_code == 409


def test_devolucao_com_quilometragem_menor_retorna_422(client, nova_locacao):
    locacao = nova_locacao()
    resposta = client.post(
        f"/locacoes/{locacao['id']}/devolucao", json={"quilometragem_final": 5, "data_devolucao_real": "2026-10-25"}
    )
    assert resposta.status_code == 422


def test_devolucao_antes_da_retirada_retorna_422(client, nova_locacao):
    locacao = nova_locacao()
    resposta = client.post(
        f"/locacoes/{locacao['id']}/devolucao",
        json={"quilometragem_final": 10500, "data_devolucao_real": "2026-10-01"},
    )
    assert resposta.status_code == 422


def test_cancelamento_libera_o_veiculo(client, nova_locacao):
    locacao = nova_locacao()
    resposta = client.post(f"/locacoes/{locacao['id']}/cancelamento")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "cancelada"
    assert resposta.json()["valor_total"] == 0
    assert client.get(f"/veiculos/{locacao['veiculo_id']}").json()["status"] == "disponivel"
    assert client.post(f"/locacoes/{locacao['id']}/cancelamento").status_code == 409


def test_prorrogar_locacao_recalcula_valor_previsto(client, nova_categoria, novo_veiculo, nova_locacao):
    veiculo = novo_veiculo(categoria_id=nova_categoria(valor_diaria=100)["id"])
    locacao = nova_locacao(veiculo_id=veiculo["id"])  # 5 diárias
    resposta = client.patch(f"/locacoes/{locacao['id']}", json={"data_devolucao_prevista": "2026-10-28"})
    assert resposta.status_code == 200
    assert resposta.json()["valor_previsto"] == 800.0  # 8 diárias x 100


def test_prorrogar_para_antes_da_retirada_retorna_422(client, nova_locacao):
    locacao = nova_locacao()
    resposta = client.patch(f"/locacoes/{locacao['id']}", json={"data_devolucao_prevista": "2026-10-10"})
    assert resposta.status_code == 422


def test_alterar_locacao_finalizada_retorna_409(client, nova_locacao):
    locacao = nova_locacao()
    client.post(f"/locacoes/{locacao['id']}/devolucao", json={"quilometragem_final": 10500, "data_devolucao_real": "2026-10-25"})
    resposta = client.patch(f"/locacoes/{locacao['id']}", json={"observacoes": "teste"})
    assert resposta.status_code == 409


def test_remover_locacao_ativa_retorna_409(client, nova_locacao):
    locacao = nova_locacao()
    assert client.delete(f"/locacoes/{locacao['id']}").status_code == 409


def test_remover_locacao_finalizada_retorna_204(client, nova_locacao):
    locacao = nova_locacao()
    client.post(f"/locacoes/{locacao['id']}/devolucao", json={"quilometragem_final": 10500, "data_devolucao_real": "2026-10-25"})
    assert client.delete(f"/locacoes/{locacao['id']}").status_code == 204
    assert client.get(f"/locacoes/{locacao['id']}").status_code == 404


def test_filtrar_locacoes(client, novo_cliente, nova_locacao):
    cliente = novo_cliente()
    ativa = nova_locacao(cliente_id=cliente["id"])
    cancelada = nova_locacao(cliente_id=cliente["id"])
    client.post(f"/locacoes/{cancelada['id']}/cancelamento")
    nova_locacao()  # de outro cliente

    assert len(client.get("/locacoes").json()) == 3
    assert len(client.get("/locacoes", params={"cliente_id": cliente["id"]}).json()) == 2
    ativas_do_cliente = client.get("/locacoes", params={"cliente_id": cliente["id"], "status": "ativa"}).json()
    assert [loc["id"] for loc in ativas_do_cliente] == [ativa["id"]]
