"""Modelo (tabela) `locacoes` — liga um cliente a um veículo."""
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import StatusLocacao, valores_do_enum

if TYPE_CHECKING:
    from app.models.cliente import Cliente
    from app.models.veiculo import Veiculo


class Locacao(TimestampMixin, Base):
    """Aluguel de um veículo por um cliente."""

    __tablename__ = "locacoes"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Chaves estrangeiras: a locação sempre aponta para um cliente e um veículo existentes.
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id", ondelete="RESTRICT"), index=True)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id", ondelete="RESTRICT"), index=True)

    data_retirada: Mapped[date] = mapped_column(Date)
    data_devolucao_prevista: Mapped[date] = mapped_column(Date)
    data_devolucao_real: Mapped[date | None] = mapped_column(Date)

    quilometragem_inicial: Mapped[int]
    quilometragem_final: Mapped[int | None]

    # A diária é copiada da categoria no momento da locação: se o preço da
    # categoria mudar depois, as locações antigas não são afetadas.
    valor_diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    valor_previsto: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    valor_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    status: Mapped[StatusLocacao] = mapped_column(
        Enum(StatusLocacao, name="status_locacao", native_enum=False, length=20, values_callable=valores_do_enum),
        default=StatusLocacao.ATIVA,
        server_default=StatusLocacao.ATIVA.value,
        index=True,
    )
    observacoes: Mapped[str | None] = mapped_column(Text)

    # Relacionamentos (N:1) — de uma locação chegamos ao cliente e ao veículo.
    cliente: Mapped["Cliente"] = relationship(back_populates="locacoes")
    veiculo: Mapped["Veiculo"] = relationship(back_populates="locacoes")

    def __repr__(self) -> str:
        return f"<Locacao id={self.id} cliente_id={self.cliente_id} veiculo_id={self.veiculo_id}>"
