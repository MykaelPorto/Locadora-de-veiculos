"""Modelo (tabela) `clientes`."""
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.locacao import Locacao


class Cliente(TimestampMixin, Base):
    """Cliente da locadora."""

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), index=True)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    telefone: Mapped[str | None] = mapped_column(String(11))
    cnh: Mapped[str] = mapped_column(String(11), unique=True, index=True)
    data_nascimento: Mapped[date] = mapped_column(Date)

    # Relacionamento 1:N — um cliente pode ter várias locações (histórico).
    locacoes: Mapped[list["Locacao"]] = relationship(back_populates="cliente", order_by="desc(Locacao.id)")

    def __repr__(self) -> str:
        return f"<Cliente id={self.id} nome={self.nome!r}>"
