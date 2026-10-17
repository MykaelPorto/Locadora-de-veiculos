"""Endpoints de Locações — /locacoes"""
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.core.database import SessionDep
from app.models.enums import StatusLocacao
from app.schemas.common import MensagemErro
from app.schemas.locacao import LocacaoCreate, LocacaoDevolucao, LocacaoResponse, LocacaoUpdate
from app.services import locacao_service

router = APIRouter(prefix="/locacoes", tags=["Locações"])

LocacaoId = Annotated[int, Path(gt=0, description="ID da locação")]

ERRO_404 = {404: {"model": MensagemErro, "description": "Locação não encontrada"}}
ERRO_409_ATIVA = {409: {"model": MensagemErro, "description": "A locação não está ativa"}}
ERRO_422_REGRA = {422: {"description": "Dados inválidos ou regra de negócio violada"}}


@router.post(
    "",
    response_model=LocacaoResponse,
    status_code=HTTPStatus.CREATED,
    summary="Registrar locação (retirada)",
    responses={
        404: {"model": MensagemErro, "description": "Cliente ou veículo não encontrado"},
        409: {"model": MensagemErro, "description": "Veículo indisponível (alugado ou em manutenção)"},
    },
)
def criar_locacao(dados: LocacaoCreate, db: SessionDep):
    """Registra a retirada de um veículo por um cliente.

    - Verifica se o **cliente** e o **veículo** existem (404 se não existirem);
    - Verifica se o veículo está **disponível** (409 se não estiver);
    - Calcula o **valor previsto** = diária da categoria × número de diárias;
    - Muda o status do veículo para **alugado**.
    """
    return locacao_service.criar(db, dados)


@router.get("", response_model=list[LocacaoResponse], summary="Listar locações")
def listar_locacoes(
    db: SessionDep,
    status: Annotated[StatusLocacao | None, Query(description="Filtrar pelo status")] = None,
    cliente_id: Annotated[int | None, Query(gt=0, description="Filtrar pelo cliente")] = None,
    veiculo_id: Annotated[int | None, Query(gt=0, description="Filtrar pelo veículo")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return locacao_service.listar(
        db, status=status, cliente_id=cliente_id, veiculo_id=veiculo_id, skip=skip, limit=limit
    )


@router.get("/{locacao_id}", response_model=LocacaoResponse, summary="Buscar locação", responses=ERRO_404)
def buscar_locacao(locacao_id: LocacaoId, db: SessionDep):
    return locacao_service.buscar_por_id(db, locacao_id)


@router.patch(
    "/{locacao_id}",
    response_model=LocacaoResponse,
    summary="Alterar locação ativa (prorrogar)",
    responses={**ERRO_404, **ERRO_409_ATIVA, **ERRO_422_REGRA},
)
def atualizar_locacao(locacao_id: LocacaoId, dados: LocacaoUpdate, db: SessionDep):
    """Altera a data de devolução prevista (o valor previsto é recalculado) ou as observações."""
    return locacao_service.atualizar(db, locacao_id, dados)


@router.post(
    "/{locacao_id}/devolucao",
    response_model=LocacaoResponse,
    summary="Registrar devolução",
    responses={**ERRO_404, **ERRO_409_ATIVA, **ERRO_422_REGRA},
)
def registrar_devolucao(locacao_id: LocacaoId, dados: LocacaoDevolucao, db: SessionDep):
    """Finaliza a locação: calcula o **valor total** pelas diárias realmente usadas,
    libera o veículo (status **disponivel**) e atualiza a quilometragem dele."""
    return locacao_service.registrar_devolucao(db, locacao_id, dados)


@router.post(
    "/{locacao_id}/cancelamento",
    response_model=LocacaoResponse,
    summary="Cancelar locação",
    responses={**ERRO_404, **ERRO_409_ATIVA},
)
def cancelar_locacao(locacao_id: LocacaoId, db: SessionDep):
    """Cancela uma locação ativa e libera o veículo."""
    return locacao_service.cancelar(db, locacao_id)


@router.delete(
    "/{locacao_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Remover locação",
    responses={**ERRO_404, 409: {"model": MensagemErro, "description": "A locação ainda está ativa"}},
)
def remover_locacao(locacao_id: LocacaoId, db: SessionDep) -> None:
    """Remove uma locação finalizada ou cancelada. Locações ativas não podem ser removidas."""
    locacao_service.remover(db, locacao_id)
