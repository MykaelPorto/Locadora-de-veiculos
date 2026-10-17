"""Regras de negócio de Categorias."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflitoDeDados, RecursoNaoEncontrado
from app.models import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate


def listar(db: Session, skip: int = 0, limit: int = 100) -> list[Categoria]:
    consulta = select(Categoria).order_by(Categoria.id).offset(skip).limit(limit)
    return list(db.scalars(consulta))


def buscar_por_id(db: Session, categoria_id: int) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise RecursoNaoEncontrado("Categoria", categoria_id)
    return categoria


def _garantir_nome_unico(db: Session, nome: str, ignorar_id: int | None = None) -> None:
    consulta = select(Categoria.id).where(func.lower(Categoria.nome) == nome.lower())
    if ignorar_id is not None:
        consulta = consulta.where(Categoria.id != ignorar_id)
    if db.scalar(consulta) is not None:
        raise ConflitoDeDados(f"Já existe uma categoria com o nome '{nome}'.")


def criar(db: Session, dados: CategoriaCreate) -> Categoria:
    _garantir_nome_unico(db, dados.nome)
    categoria = Categoria(**dados.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def atualizar(db: Session, categoria_id: int, dados: CategoriaUpdate) -> Categoria:
    categoria = buscar_por_id(db, categoria_id)
    alteracoes = dados.model_dump(exclude_unset=True)

    if "nome" in alteracoes:
        _garantir_nome_unico(db, alteracoes["nome"], ignorar_id=categoria_id)

    for campo, valor in alteracoes.items():
        setattr(categoria, campo, valor)
    db.commit()
    db.refresh(categoria)
    return categoria


def remover(db: Session, categoria_id: int) -> None:
    categoria = buscar_por_id(db, categoria_id)
    # Navega pelo relationship Categoria.veiculos
    if categoria.veiculos:
        raise ConflitoDeDados(
            f"A categoria '{categoria.nome}' possui {len(categoria.veiculos)} veículo(s) e não pode ser removida. "
            "Remova ou mude os veículos de categoria antes."
        )
    db.delete(categoria)
    db.commit()
