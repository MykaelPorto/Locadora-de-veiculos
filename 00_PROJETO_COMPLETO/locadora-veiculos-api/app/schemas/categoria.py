"""Schemas de Categoria: CategoriaCreate, CategoriaUpdate e CategoriaResponse."""
from datetime import datetime
from decimal import Decimal

from pydantic import ConfigDict, Field

from app.schemas.common import Dinheiro, SchemaAtualizacao, SchemaEntrada, SchemaResposta


class CategoriaCreate(SchemaEntrada):
    """Dados para cadastrar uma categoria."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"nome": "SUV", "descricao": "Utilitários esportivos com mais espaço e conforto.", "valor_diaria": 220.00}
            ]
        }
    )

    nome: str = Field(min_length=2, max_length=50)
    descricao: str | None = Field(default=None, max_length=500)
    valor_diaria: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class CategoriaUpdate(SchemaAtualizacao):
    """Dados para atualizar uma categoria. Envie só os campos que quer alterar."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"valor_diaria": 240.00}]})
    campos_que_aceitam_nulo = frozenset({"descricao"})

    nome: str | None = Field(default=None, min_length=2, max_length=50)
    descricao: str | None = Field(default=None, max_length=500)
    valor_diaria: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)


class CategoriaResponse(SchemaResposta):
    """Categoria devolvida pela API."""

    id: int
    nome: str
    descricao: str | None
    valor_diaria: Dinheiro
    criado_em: datetime
    atualizado_em: datetime


class CategoriaResumo(SchemaResposta):
    """Versão resumida, usada dentro da resposta de Veículo."""

    id: int
    nome: str
    valor_diaria: Dinheiro
