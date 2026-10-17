"""Schemas de Veículo: VeiculoCreate, VeiculoUpdate e VeiculoResponse."""
from datetime import datetime

from pydantic import ConfigDict, Field

from app.models.enums import StatusVeiculo
from app.schemas.categoria import CategoriaResumo
from app.schemas.common import AnoVeiculo, Placa, SchemaAtualizacao, SchemaEntrada, SchemaResposta


class VeiculoCreate(SchemaEntrada):
    """Dados para cadastrar um veículo. Todo veículo novo começa com status `disponivel`."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "placa": "QRS1A23",
                    "marca": "Jeep",
                    "modelo": "Compass",
                    "ano": 2024,
                    "cor": "Prata",
                    "quilometragem": 15000,
                    "categoria_id": 1,
                }
            ]
        }
    )

    placa: Placa
    marca: str = Field(min_length=2, max_length=50)
    modelo: str = Field(min_length=1, max_length=50)
    ano: AnoVeiculo
    cor: str = Field(min_length=3, max_length=30)
    quilometragem: int = Field(default=0, ge=0)
    categoria_id: int = Field(gt=0, description="ID de uma categoria já cadastrada")


class VeiculoUpdate(SchemaAtualizacao):
    """Dados para atualizar um veículo. Envie só os campos que quer alterar.

    O status pode ser alterado manualmente apenas para `disponivel` ou `manutencao`;
    o status `alugado` é controlado pelas locações.
    """

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "manutencao"}]})

    placa: Placa | None = None
    marca: str | None = Field(default=None, min_length=2, max_length=50)
    modelo: str | None = Field(default=None, min_length=1, max_length=50)
    ano: AnoVeiculo | None = None
    cor: str | None = Field(default=None, min_length=3, max_length=30)
    quilometragem: int | None = Field(default=None, ge=0)
    status: StatusVeiculo | None = None
    categoria_id: int | None = Field(default=None, gt=0)


class VeiculoResponse(SchemaResposta):
    """Veículo devolvido pela API, já com os dados da categoria (via relationship)."""

    id: int
    placa: str
    marca: str
    modelo: str
    ano: int
    cor: str
    quilometragem: int
    status: StatusVeiculo
    categoria_id: int
    categoria: CategoriaResumo
    criado_em: datetime
    atualizado_em: datetime


class VeiculoResumo(SchemaResposta):
    """Versão resumida, usada dentro da resposta de Locação."""

    id: int
    placa: str
    marca: str
    modelo: str
