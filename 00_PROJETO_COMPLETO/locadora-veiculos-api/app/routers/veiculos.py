"""Endpoints de Veículos — /veiculos"""
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.core.database import SessionDep
from app.models.enums import StatusVeiculo
from app.schemas.common import MensagemErro
from app.schemas.locacao import LocacaoResponse
from app.schemas.veiculo import VeiculoCreate, VeiculoResponse, VeiculoUpdate
from app.services import veiculo_service

router = APIRouter(prefix="/veiculos", tags=["Veículos"])

VeiculoId = Annotated[int, Path(gt=0, description="ID do veículo")]

ERRO_404 = {404: {"model": MensagemErro, "description": "Veículo (ou categoria informada) não encontrado"}}
ERRO_409 = {409: {"model": MensagemErro, "description": "Placa já cadastrada ou veículo alugado"}}


@router.post(
    "",
    response_model=VeiculoResponse,
    status_code=HTTPStatus.CREATED,
    summary="Cadastrar veículo",
    responses={**ERRO_404, **ERRO_409},
)
def criar_veiculo(dados: VeiculoCreate, db: SessionDep):
    """Cadastra um veículo. A `categoria_id` precisa existir (senão retorna 404)."""
    return veiculo_service.criar(db, dados)


@router.get("", response_model=list[VeiculoResponse], summary="Listar veículos")
def listar_veiculos(
    db: SessionDep,
    status: Annotated[StatusVeiculo | None, Query(description="Filtrar pelo status")] = None,
    categoria_id: Annotated[int | None, Query(gt=0, description="Filtrar pela categoria")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    """Lista os veículos. Use `status=disponivel` para ver só os que podem ser alugados."""
    return veiculo_service.listar(db, status=status, categoria_id=categoria_id, skip=skip, limit=limit)


@router.get("/{veiculo_id}", response_model=VeiculoResponse, summary="Buscar veículo", responses=ERRO_404)
def buscar_veiculo(veiculo_id: VeiculoId, db: SessionDep):
    return veiculo_service.buscar_por_id(db, veiculo_id)


@router.get(
    "/{veiculo_id}/locacoes",
    response_model=list[LocacaoResponse],
    summary="Histórico de locações do veículo",
    responses=ERRO_404,
)
def listar_locacoes_do_veiculo(veiculo_id: VeiculoId, db: SessionDep):
    """Navega pelo relacionamento `Veiculo.locacoes` (relationship do SQLAlchemy)."""
    veiculo = veiculo_service.buscar_por_id(db, veiculo_id)
    return veiculo.locacoes


@router.patch(
    "/{veiculo_id}",
    response_model=VeiculoResponse,
    summary="Atualizar veículo",
    responses={**ERRO_404, **ERRO_409},
)
def atualizar_veiculo(veiculo_id: VeiculoId, dados: VeiculoUpdate, db: SessionDep):
    """Atualiza apenas os campos enviados (ex.: colocar o veículo em manutenção)."""
    return veiculo_service.atualizar(db, veiculo_id, dados)


@router.delete(
    "/{veiculo_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Remover veículo",
    responses={**ERRO_404, 409: {"model": MensagemErro, "description": "O veículo possui locações"}},
)
def remover_veiculo(veiculo_id: VeiculoId, db: SessionDep) -> None:
    """Remove o veículo. Não é permitido se ele tiver histórico de locações."""
    veiculo_service.remover(db, veiculo_id)
