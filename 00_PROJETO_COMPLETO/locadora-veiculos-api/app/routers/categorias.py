"""Endpoints de Categorias — /categorias"""
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.core.database import SessionDep
from app.schemas.categoria import CategoriaCreate, CategoriaResponse, CategoriaUpdate
from app.schemas.common import MensagemErro
from app.schemas.veiculo import VeiculoResponse
from app.services import categoria_service

router = APIRouter(prefix="/categorias", tags=["Categorias"])

CategoriaId = Annotated[int, Path(gt=0, description="ID da categoria")]

ERRO_404 = {404: {"model": MensagemErro, "description": "Categoria não encontrada"}}
ERRO_409_NOME = {409: {"model": MensagemErro, "description": "Já existe uma categoria com esse nome"}}


@router.post(
    "",
    response_model=CategoriaResponse,
    status_code=HTTPStatus.CREATED,
    summary="Cadastrar categoria",
    responses=ERRO_409_NOME,
)
def criar_categoria(dados: CategoriaCreate, db: SessionDep):
    """Cadastra uma nova categoria de veículos com o valor da diária."""
    return categoria_service.criar(db, dados)


@router.get("", response_model=list[CategoriaResponse], summary="Listar categorias")
def listar_categorias(
    db: SessionDep,
    skip: Annotated[int, Query(ge=0, description="Quantos registros pular")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Máximo de registros")] = 100,
):
    return categoria_service.listar(db, skip=skip, limit=limit)


@router.get("/{categoria_id}", response_model=CategoriaResponse, summary="Buscar categoria", responses=ERRO_404)
def buscar_categoria(categoria_id: CategoriaId, db: SessionDep):
    return categoria_service.buscar_por_id(db, categoria_id)


@router.get(
    "/{categoria_id}/veiculos",
    response_model=list[VeiculoResponse],
    summary="Listar veículos da categoria",
    responses=ERRO_404,
)
def listar_veiculos_da_categoria(categoria_id: CategoriaId, db: SessionDep):
    """Navega pelo relacionamento `Categoria.veiculos` (relationship do SQLAlchemy)."""
    categoria = categoria_service.buscar_por_id(db, categoria_id)
    return categoria.veiculos


@router.patch(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Atualizar categoria",
    responses={**ERRO_404, **ERRO_409_NOME},
)
def atualizar_categoria(categoria_id: CategoriaId, dados: CategoriaUpdate, db: SessionDep):
    """Atualiza apenas os campos enviados."""
    return categoria_service.atualizar(db, categoria_id, dados)


@router.delete(
    "/{categoria_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Remover categoria",
    responses={**ERRO_404, 409: {"model": MensagemErro, "description": "A categoria possui veículos"}},
)
def remover_categoria(categoria_id: CategoriaId, db: SessionDep) -> None:
    """Remove a categoria. Não é permitido se houver veículos nela."""
    categoria_service.remover(db, categoria_id)
