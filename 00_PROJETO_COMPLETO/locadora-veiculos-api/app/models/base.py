"""Base declarativa do SQLAlchemy, compartilhada por todos os modelos."""
from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Padrão de nomes para índices e constraints. Deixa as migrações do Alembic
# previsíveis (o mesmo nome em qualquer banco) e permite alterá-las depois.
CONVENCAO_DE_NOMES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCAO_DE_NOMES)


class TimestampMixin:
    """Adiciona as colunas `criado_em` e `atualizado_em` (preenchidas pelo próprio banco)."""

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), sort_order=100)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), sort_order=101
    )
