"""Regras de negócio de Clientes."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflitoDeDados, RecursoNaoEncontrado
from app.models import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate

# Campos que não podem se repetir entre clientes e o nome usado na mensagem de erro
_CAMPOS_UNICOS = {"cpf": "CPF", "email": "e-mail", "cnh": "CNH"}


def listar(db: Session, nome: str | None = None, skip: int = 0, limit: int = 100) -> list[Cliente]:
    consulta = select(Cliente).order_by(Cliente.nome)
    if nome:
        consulta = consulta.where(Cliente.nome.ilike(f"%{nome}%"))
    return list(db.scalars(consulta.offset(skip).limit(limit)))


def buscar_por_id(db: Session, cliente_id: int) -> Cliente:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise RecursoNaoEncontrado("Cliente", cliente_id)
    return cliente


def _garantir_campos_unicos(db: Session, valores: dict, ignorar_id: int | None = None) -> None:
    for campo, rotulo in _CAMPOS_UNICOS.items():
        if campo not in valores:
            continue
        coluna = getattr(Cliente, campo)
        consulta = select(Cliente.id).where(coluna == valores[campo])
        if ignorar_id is not None:
            consulta = consulta.where(Cliente.id != ignorar_id)
        if db.scalar(consulta) is not None:
            raise ConflitoDeDados(f"Já existe um cliente cadastrado com este {rotulo}.")


def criar(db: Session, dados: ClienteCreate) -> Cliente:
    valores = dados.model_dump()
    _garantir_campos_unicos(db, valores)
    cliente = Cliente(**valores)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def atualizar(db: Session, cliente_id: int, dados: ClienteUpdate) -> Cliente:
    cliente = buscar_por_id(db, cliente_id)
    alteracoes = dados.model_dump(exclude_unset=True)
    _garantir_campos_unicos(db, alteracoes, ignorar_id=cliente_id)

    for campo, valor in alteracoes.items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente


def remover(db: Session, cliente_id: int) -> None:
    cliente = buscar_por_id(db, cliente_id)
    # Navega pelo relationship Cliente.locacoes
    if cliente.locacoes:
        raise ConflitoDeDados(
            f"O cliente {cliente.nome} possui histórico de locações e não pode ser removido."
        )
    db.delete(cliente)
    db.commit()
