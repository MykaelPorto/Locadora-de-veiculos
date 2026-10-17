"""Schemas de Cliente: ClienteCreate, ClienteUpdate e ClienteResponse."""
from datetime import date, datetime

from pydantic import ConfigDict, Field

from app.schemas.common import CNH, CPF, DataNascimento, Email, SchemaAtualizacao, SchemaEntrada, SchemaResposta, Telefone


class ClienteCreate(SchemaEntrada):
    """Dados para cadastrar um cliente. CPF, CNH e telefone podem ser enviados com ou sem pontuação."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nome": "Maria Souza",
                    "cpf": "529.982.247-25",
                    "email": "maria.souza@email.com",
                    "telefone": "(86) 99999-0000",
                    "cnh": "12345678900",
                    "data_nascimento": "1995-04-12",
                }
            ]
        }
    )

    nome: str = Field(min_length=3, max_length=120)
    cpf: CPF
    email: Email
    telefone: Telefone | None = None
    cnh: CNH
    data_nascimento: DataNascimento


class ClienteUpdate(SchemaAtualizacao):
    """Dados para atualizar um cliente. Envie só os campos que quer alterar.

    O CPF não pode ser alterado (é a identificação do cliente).
    """

    model_config = ConfigDict(json_schema_extra={"examples": [{"telefone": "(86) 98888-1111"}]})
    campos_que_aceitam_nulo = frozenset({"telefone"})

    nome: str | None = Field(default=None, min_length=3, max_length=120)
    email: Email | None = None
    telefone: Telefone | None = None
    cnh: CNH | None = None
    data_nascimento: DataNascimento | None = None


class ClienteResponse(SchemaResposta):
    """Cliente devolvido pela API."""

    id: int
    nome: str
    cpf: str
    email: str
    telefone: str | None
    cnh: str
    data_nascimento: date
    criado_em: datetime
    atualizado_em: datetime


class ClienteResumo(SchemaResposta):
    """Versão resumida, usada dentro da resposta de Locação."""

    id: int
    nome: str
    cpf: str
