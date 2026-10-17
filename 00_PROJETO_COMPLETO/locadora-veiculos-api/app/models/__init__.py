"""Modelos do SQLAlchemy (tabelas do banco).

Todos os modelos são importados aqui para que o SQLAlchemy e o Alembic
conheçam todas as tabelas ao ler `Base.metadata`.
"""
from app.models.base import Base
from app.models.categoria import Categoria
from app.models.cliente import Cliente
from app.models.locacao import Locacao
from app.models.veiculo import Veiculo

__all__ = ["Base", "Categoria", "Cliente", "Locacao", "Veiculo"]
