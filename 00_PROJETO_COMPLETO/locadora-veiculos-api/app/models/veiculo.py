"""Modelo (tabela) `veiculos`."""
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import StatusVeiculo, valores_do_enum

if TYPE_CHECKING:
    from app.models.categoria import Categoria
    from app.models.locacao import Locacao


class Veiculo(TimestampMixin, Base):
    """Veículo da frota. Pertence a uma categoria."""

    __tablename__ = "veiculos"

    id: Mapped[int] = mapped_column(primary_key=True)
    placa: Mapped[str] = mapped_column(String(7), unique=True, index=True)
    marca: Mapped[str] = mapped_column(String(50))
    modelo: Mapped[str] = mapped_column(String(50))
    ano: Mapped[int]
    cor: Mapped[str] = mapped_column(String(30))
    quilometragem: Mapped[int] = mapped_column(default=0)
    status: Mapped[StatusVeiculo] = mapped_column(
        Enum(StatusVeiculo, name="status_veiculo", native_enum=False, length=20, values_callable=valores_do_enum),
        default=StatusVeiculo.DISPONIVEL,
        server_default=StatusVeiculo.DISPONIVEL.value,
        index=True,
    )

    # Chave estrangeira: todo veículo pertence a uma categoria existente.
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id", ondelete="RESTRICT"), index=True)

    # Relacionamentos (navegação entre os modelos)
    categoria: Mapped["Categoria"] = relationship(back_populates="veiculos")
    locacoes: Mapped[list["Locacao"]] = relationship(back_populates="veiculo", order_by="desc(Locacao.id)")

    def __repr__(self) -> str:
        return f"<Veiculo id={self.id} placa={self.placa!r} status={self.status.value!r}>"
