"""Exceções HTTP da aplicação.

Todas herdam de `HTTPException` do FastAPI. Quando uma delas é lançada (em um router
ou em um service), o FastAPI devolve ao cliente o status code e a mensagem definidos aqui.

| Exceção                | Status | Quando é usada                                                        |
|------------------------|--------|-----------------------------------------------------------------------|
| RecursoNaoEncontrado   | 404    | O registro buscado (ou referenciado por chave estrangeira) não existe |
| ConflitoDeDados        | 409    | Duplicidade (placa, CPF...) ou conflito de estado (veículo alugado)   |
| RegraDeNegocioViolada  | 422    | Dados bem formatados, mas que violam uma regra do negócio             |

Os erros 422 de formato (campo faltando, tipo errado, CPF inválido...) são gerados
automaticamente pelo FastAPI a partir dos schemas Pydantic.
"""
from http import HTTPStatus

from fastapi import HTTPException


class RecursoNaoEncontrado(HTTPException):
    """404 Not Found."""

    def __init__(self, recurso: str, recurso_id: int) -> None:
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=f"{recurso} com id {recurso_id} não existe.")


class ConflitoDeDados(HTTPException):
    """409 Conflict."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(status_code=HTTPStatus.CONFLICT, detail=mensagem)


class RegraDeNegocioViolada(HTTPException):
    """422 Unprocessable Entity."""

    def __init__(self, mensagem: str) -> None:
        super().__init__(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=mensagem)
