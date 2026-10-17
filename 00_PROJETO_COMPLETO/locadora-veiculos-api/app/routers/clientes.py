"""Endpoints de Clientes — /clientes"""
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.core.database import SessionDep
from app.schemas.cliente import ClienteCreate, ClienteResponse, ClienteUpdate
from app.schemas.common import MensagemErro
from app.schemas.locacao import LocacaoResponse
from app.services import cliente_service

router = APIRouter(prefix="/clientes", tags=["Clientes"])

ClienteId = Annotated[int, Path(gt=0, description="ID do cliente")]

ERRO_404 = {404: {"model": MensagemErro, "description": "Cliente não encontrado"}}
ERRO_409 = {409: {"model": MensagemErro, "description": "CPF, e-mail ou CNH já cadastrados"}}


@router.post(
    "",
    response_model=ClienteResponse,
    status_code=HTTPStatus.CREATED,
    summary="Cadastrar cliente",
    responses=ERRO_409,
)
def criar_cliente(dados: ClienteCreate, db: SessionDep):
    """Cadastra um cliente. O CPF é validado (dígitos verificadores) e o cliente precisa ter 18 anos ou mais."""
    return cliente_service.criar(db, dados)


@router.get("", response_model=list[ClienteResponse], summary="Listar clientes")
def listar_clientes(
    db: SessionDep,
    nome: Annotated[str | None, Query(min_length=1, description="Busca por parte do nome")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return cliente_service.listar(db, nome=nome, skip=skip, limit=limit)


@router.get("/{cliente_id}", response_model=ClienteResponse, summary="Buscar cliente", responses=ERRO_404)
def buscar_cliente(cliente_id: ClienteId, db: SessionDep):
    return cliente_service.buscar_por_id(db, cliente_id)


@router.get(
    "/{cliente_id}/locacoes",
    response_model=list[LocacaoResponse],
    summary="Histórico de locações do cliente",
    responses=ERRO_404,
)
def listar_locacoes_do_cliente(cliente_id: ClienteId, db: SessionDep):
    """Navega pelo relacionamento `Cliente.locacoes` (relationship do SQLAlchemy)."""
    cliente = cliente_service.buscar_por_id(db, cliente_id)
    return cliente.locacoes


@router.patch(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Atualizar cliente",
    responses={**ERRO_404, **ERRO_409},
)
def atualizar_cliente(cliente_id: ClienteId, dados: ClienteUpdate, db: SessionDep):
    """Atualiza apenas os campos enviados. O CPF não pode ser alterado."""
    return cliente_service.atualizar(db, cliente_id, dados)


@router.delete(
    "/{cliente_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Remover cliente",
    responses={**ERRO_404, 409: {"model": MensagemErro, "description": "O cliente possui locações"}},
)
def remover_cliente(cliente_id: ClienteId, db: SessionDep) -> None:
    """Remove o cliente. Não é permitido se ele tiver histórico de locações."""
    cliente_service.remover(db, cliente_id)
