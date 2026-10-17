"""Schemas de Locação: LocacaoCreate, LocacaoUpdate, LocacaoDevolucao e LocacaoResponse."""
from datetime import date, datetime

from pydantic import ConfigDict, Field, model_validator

from app.models.enums import StatusLocacao
from app.schemas.cliente import ClienteResumo
from app.schemas.common import Dinheiro, SchemaAtualizacao, SchemaEntrada, SchemaResposta
from app.schemas.veiculo import VeiculoResumo


class LocacaoCreate(SchemaEntrada):
    """Dados para registrar uma locação (retirada do veículo).

    O valor da diária e a quilometragem inicial são preenchidos automaticamente
    a partir da categoria e do veículo. Se `data_retirada` não for enviada, vale a data de hoje.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "cliente_id": 1,
                    "veiculo_id": 1,
                    "data_retirada": "2026-10-20",
                    "data_devolucao_prevista": "2026-10-25",
                    "observacoes": "Cliente solicitou cadeirinha infantil.",
                }
            ]
        }
    )

    cliente_id: int = Field(gt=0, description="ID de um cliente já cadastrado")
    veiculo_id: int = Field(gt=0, description="ID de um veículo já cadastrado e disponível")
    data_retirada: date = Field(default_factory=date.today)
    data_devolucao_prevista: date
    observacoes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _validar_datas(self):
        if self.data_devolucao_prevista <= self.data_retirada:
            raise ValueError("A data de devolução prevista deve ser posterior à data de retirada.")
        return self


class LocacaoUpdate(SchemaAtualizacao):
    """Altera uma locação ATIVA: prorrogar/antecipar a devolução prevista ou mudar as observações."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"data_devolucao_prevista": "2026-10-28"}]})
    campos_que_aceitam_nulo = frozenset({"observacoes"})

    data_devolucao_prevista: date | None = None
    observacoes: str | None = Field(default=None, max_length=500)


class LocacaoDevolucao(SchemaEntrada):
    """Dados da devolução do veículo. Se `data_devolucao_real` não for enviada, vale a data de hoje."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "quilometragem_final": 15840,
                    "data_devolucao_real": "2026-10-26",
                    "observacoes": "Devolvido com tanque cheio.",
                }
            ]
        }
    )

    quilometragem_final: int = Field(ge=0)
    data_devolucao_real: date = Field(default_factory=date.today)
    observacoes: str | None = Field(default=None, max_length=500)


class LocacaoResponse(SchemaResposta):
    """Locação devolvida pela API, com o resumo do cliente e do veículo (via relationship)."""

    id: int
    status: StatusLocacao
    cliente_id: int
    veiculo_id: int
    data_retirada: date
    data_devolucao_prevista: date
    data_devolucao_real: date | None
    quilometragem_inicial: int
    quilometragem_final: int | None
    valor_diaria: Dinheiro
    valor_previsto: Dinheiro
    valor_total: Dinheiro | None
    observacoes: str | None
    cliente: ClienteResumo
    veiculo: VeiculoResumo
    criado_em: datetime
    atualizado_em: datetime
