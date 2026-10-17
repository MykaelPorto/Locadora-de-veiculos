"""Modelo (tabela) `categorias`."""
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.veiculo import Veiculo


class Categoria(TimestampMixin, Base):
    """Categoria de veículos (ex.: Econômico, SUV). Define o valor da diária."""

    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    valor_diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Relacionamento 1:N — uma categoria possui vários veículos.
    veiculos: Mapped[list["Veiculo"]] = relationship(back_populates="categoria", order_by="Veiculo.id")

    def __repr__(self) -> str:
        return f"<Categoria id={self.id} nome={self.nome!r}>"
