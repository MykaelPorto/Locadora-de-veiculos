"""Regras de negócio de Locações — o coração do sistema.

Ciclo de vida de uma locação:
    ativa ──(devolução)──► finalizada
      └───(cancelamento)──► cancelada

Enquanto a locação está ativa, o veículo fica com status `alugado`.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflitoDeDados, RecursoNaoEncontrado, RegraDeNegocioViolada
from app.models import Locacao
from app.models.enums import StatusLocacao, StatusVeiculo
from app.schemas.locacao import LocacaoCreate, LocacaoDevolucao, LocacaoUpdate
from app.services import cliente_service, veiculo_service


def calcular_diarias(inicio: date, fim: date) -> int:
    """Quantidade de diárias entre duas datas (mínimo de 1, para devolução no mesmo dia)."""
    return max(1, (fim - inicio).days)


def listar(
    db: Session,
    status: StatusLocacao | None = None,
    cliente_id: int | None = None,
    veiculo_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Locacao]:
    consulta = (
        select(Locacao)
        .options(joinedload(Locacao.cliente), joinedload(Locacao.veiculo))
        .order_by(Locacao.id.desc())
    )
    if status is not None:
        consulta = consulta.where(Locacao.status == status)
    if cliente_id is not None:
        consulta = consulta.where(Locacao.cliente_id == cliente_id)
    if veiculo_id is not None:
        consulta = consulta.where(Locacao.veiculo_id == veiculo_id)
    return list(db.scalars(consulta.offset(skip).limit(limit)))


def buscar_por_id(db: Session, locacao_id: int) -> Locacao:
    locacao = db.get(Locacao, locacao_id)
    if locacao is None:
        raise RecursoNaoEncontrado("Locação", locacao_id)
    return locacao


def _garantir_ativa(locacao: Locacao, acao: str) -> None:
    if locacao.status != StatusLocacao.ATIVA:
        raise ConflitoDeDados(
            f"Não é possível {acao}: a locação {locacao.id} está com status '{locacao.status.value}'."
        )


def criar(db: Session, dados: LocacaoCreate) -> Locacao:
    # Validação de integridade: cliente e veículo precisam existir (senão 404)
    cliente = cliente_service.buscar_por_id(db, dados.cliente_id)
    veiculo = veiculo_service.buscar_por_id(db, dados.veiculo_id)

    if veiculo.status != StatusVeiculo.DISPONIVEL:
        raise ConflitoDeDados(
            f"O veículo {veiculo.placa} não está disponível para locação (status atual: '{veiculo.status.value}')."
        )

    # Navega pelo relationship Veiculo -> Categoria para pegar o valor da diária
    valor_diaria = veiculo.categoria.valor_diaria
    diarias = calcular_diarias(dados.data_retirada, dados.data_devolucao_prevista)

    locacao = Locacao(
        cliente=cliente,  # o relationship preenche cliente_id automaticamente
        veiculo=veiculo,  # o relationship preenche veiculo_id automaticamente
        data_retirada=dados.data_retirada,
        data_devolucao_prevista=dados.data_devolucao_prevista,
        quilometragem_inicial=veiculo.quilometragem,
        valor_diaria=valor_diaria,
        valor_previsto=valor_diaria * diarias,
        status=StatusLocacao.ATIVA,
        observacoes=dados.observacoes,
    )
    veiculo.status = StatusVeiculo.ALUGADO

    db.add(locacao)
    db.commit()
    db.refresh(locacao)
    return locacao


def atualizar(db: Session, locacao_id: int, dados: LocacaoUpdate) -> Locacao:
    locacao = buscar_por_id(db, locacao_id)
    _garantir_ativa(locacao, "alterar a locação")
    alteracoes = dados.model_dump(exclude_unset=True)

    if "data_devolucao_prevista" in alteracoes:
        nova_data = alteracoes["data_devolucao_prevista"]
        if nova_data <= locacao.data_retirada:
            raise RegraDeNegocioViolada(
                f"A data de devolução prevista deve ser posterior à data de retirada ({locacao.data_retirada.isoformat()})."
            )
        diarias = calcular_diarias(locacao.data_retirada, nova_data)
        locacao.data_devolucao_prevista = nova_data
        locacao.valor_previsto = locacao.valor_diaria * diarias

    if "observacoes" in alteracoes:
        locacao.observacoes = alteracoes["observacoes"]

    db.commit()
    db.refresh(locacao)
    return locacao


def registrar_devolucao(db: Session, locacao_id: int, dados: LocacaoDevolucao) -> Locacao:
    locacao = buscar_por_id(db, locacao_id)
    _garantir_ativa(locacao, "registrar a devolução")

    if dados.data_devolucao_real < locacao.data_retirada:
        raise RegraDeNegocioViolada(
            f"A data de devolução não pode ser anterior à data de retirada ({locacao.data_retirada.isoformat()})."
        )
    if dados.quilometragem_final < locacao.quilometragem_inicial:
        raise RegraDeNegocioViolada(
            f"A quilometragem final ({dados.quilometragem_final} km) não pode ser menor que a "
            f"inicial ({locacao.quilometragem_inicial} km)."
        )

    # Cobra as diárias realmente usadas (se atrasar, paga os dias a mais)
    diarias = calcular_diarias(locacao.data_retirada, dados.data_devolucao_real)
    locacao.data_devolucao_real = dados.data_devolucao_real
    locacao.quilometragem_final = dados.quilometragem_final
    locacao.valor_total = locacao.valor_diaria * diarias
    locacao.status = StatusLocacao.FINALIZADA
    if dados.observacoes:
        locacao.observacoes = dados.observacoes

    # Libera o veículo e atualiza o hodômetro (navegando pelo relationship Locacao -> Veiculo)
    locacao.veiculo.status = StatusVeiculo.DISPONIVEL
    locacao.veiculo.quilometragem = dados.quilometragem_final

    db.commit()
    db.refresh(locacao)
    return locacao


def cancelar(db: Session, locacao_id: int) -> Locacao:
    locacao = buscar_por_id(db, locacao_id)
    _garantir_ativa(locacao, "cancelar a locação")

    locacao.status = StatusLocacao.CANCELADA
    locacao.valor_total = 0
    locacao.veiculo.status = StatusVeiculo.DISPONIVEL

    db.commit()
    db.refresh(locacao)
    return locacao


def remover(db: Session, locacao_id: int) -> None:
    locacao = buscar_por_id(db, locacao_id)
    if locacao.status == StatusLocacao.ATIVA:
        raise ConflitoDeDados(
            "Não é possível remover uma locação ativa. Registre a devolução ou cancele a locação antes."
        )
    db.delete(locacao)
    db.commit()
