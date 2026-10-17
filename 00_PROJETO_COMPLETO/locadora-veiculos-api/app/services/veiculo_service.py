"""Regras de negócio de Veículos."""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflitoDeDados, RecursoNaoEncontrado, RegraDeNegocioViolada
from app.models import Veiculo
from app.models.enums import StatusVeiculo
from app.schemas.veiculo import VeiculoCreate, VeiculoUpdate
from app.services import categoria_service


def listar(
    db: Session,
    status: StatusVeiculo | None = None,
    categoria_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Veiculo]:
    # joinedload: já traz a categoria na mesma consulta (evita uma consulta extra por veículo)
    consulta = select(Veiculo).options(joinedload(Veiculo.categoria)).order_by(Veiculo.id)
    if status is not None:
        consulta = consulta.where(Veiculo.status == status)
    if categoria_id is not None:
        consulta = consulta.where(Veiculo.categoria_id == categoria_id)
    return list(db.scalars(consulta.offset(skip).limit(limit)))


def buscar_por_id(db: Session, veiculo_id: int) -> Veiculo:
    veiculo = db.get(Veiculo, veiculo_id)
    if veiculo is None:
        raise RecursoNaoEncontrado("Veículo", veiculo_id)
    return veiculo


def _garantir_placa_unica(db: Session, placa: str, ignorar_id: int | None = None) -> None:
    consulta = select(Veiculo.id).where(Veiculo.placa == placa)
    if ignorar_id is not None:
        consulta = consulta.where(Veiculo.id != ignorar_id)
    if db.scalar(consulta) is not None:
        raise ConflitoDeDados(f"Já existe um veículo com a placa {placa}.")


def criar(db: Session, dados: VeiculoCreate) -> Veiculo:
    # Validação de integridade: a categoria informada precisa existir (senão 404)
    categoria_service.buscar_por_id(db, dados.categoria_id)
    _garantir_placa_unica(db, dados.placa)

    veiculo = Veiculo(**dados.model_dump(), status=StatusVeiculo.DISPONIVEL)
    db.add(veiculo)
    db.commit()
    db.refresh(veiculo)
    return veiculo


def atualizar(db: Session, veiculo_id: int, dados: VeiculoUpdate) -> Veiculo:
    veiculo = buscar_por_id(db, veiculo_id)
    alteracoes = dados.model_dump(exclude_unset=True)

    if "categoria_id" in alteracoes:
        # Validação de integridade também na atualização
        categoria_service.buscar_por_id(db, alteracoes["categoria_id"])

    if "placa" in alteracoes:
        _garantir_placa_unica(db, alteracoes["placa"], ignorar_id=veiculo_id)

    if "quilometragem" in alteracoes and alteracoes["quilometragem"] < veiculo.quilometragem:
        raise RegraDeNegocioViolada(
            f"A quilometragem não pode diminuir (atual: {veiculo.quilometragem} km, enviada: {alteracoes['quilometragem']} km)."
        )

    if "status" in alteracoes:
        novo_status = alteracoes["status"]
        if novo_status == StatusVeiculo.ALUGADO:
            raise RegraDeNegocioViolada(
                "O status 'alugado' é definido automaticamente ao registrar uma locação; não pode ser alterado manualmente."
            )
        if veiculo.status == StatusVeiculo.ALUGADO:
            raise ConflitoDeDados(
                "O veículo está alugado. Registre a devolução ou cancele a locação antes de alterar o status."
            )

    for campo, valor in alteracoes.items():
        setattr(veiculo, campo, valor)
    db.commit()
    db.refresh(veiculo)
    return veiculo


def remover(db: Session, veiculo_id: int) -> None:
    veiculo = buscar_por_id(db, veiculo_id)
    # Navega pelo relationship Veiculo.locacoes
    if veiculo.locacoes:
        raise ConflitoDeDados(
            f"O veículo {veiculo.placa} possui histórico de locações e não pode ser removido."
        )
    db.delete(veiculo)
    db.commit()
