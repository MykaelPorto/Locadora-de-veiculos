"""Ponto de entrada da aplicação — Locadora de Veículos API.

Iniciar:  uvicorn app.main:app --reload
Swagger:  http://127.0.0.1:8000/docs
"""
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.routers import categorias, clientes, locacoes, veiculos

DESCRICAO = """
API de uma **locadora de veículos**: cadastro de categorias, veículos e clientes
e controle das locações (retirada, devolução e cancelamento).

**Fluxo sugerido para testar:**
1. `POST /categorias` → cadastre uma categoria (define o valor da diária)
2. `POST /veiculos` → cadastre um veículo nessa categoria
3. `POST /clientes` → cadastre um cliente
4. `POST /locacoes` → registre a locação (o veículo passa a ficar **alugado**)
5. `POST /locacoes/{id}/devolucao` → registre a devolução (o valor total é calculado)
"""

TAGS = [
    {"name": "Início", "description": "Informações gerais da API."},
    {"name": "Categorias", "description": "Categorias de veículos e o valor da diária de cada uma."},
    {"name": "Veículos", "description": "Frota da locadora. Cada veículo pertence a uma categoria."},
    {"name": "Clientes", "description": "Clientes que podem alugar veículos."},
    {"name": "Locações", "description": "Aluguel de um veículo por um cliente: retirada, devolução e cancelamento."},
]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=DESCRICAO,
    openapi_tags=TAGS,
)

# As tabelas NÃO são criadas aqui (não há Base.metadata.create_all neste projeto).
# O banco é criado exclusivamente pelas migrações do Alembic: `alembic upgrade head`.

app.include_router(categorias.router)
app.include_router(veiculos.router)
app.include_router(clientes.router)
app.include_router(locacoes.router)


@app.exception_handler(IntegrityError)
async def tratar_erro_de_integridade(request: Request, exc: IntegrityError) -> JSONResponse:
    """Rede de segurança: se o próprio banco recusar a operação (registro duplicado ou
    chave estrangeira inválida), a API responde 409 em vez de um erro 500."""
    return JSONResponse(
        status_code=HTTPStatus.CONFLICT,
        content={"detail": "A operação viola uma regra de integridade do banco de dados."},
    )


@app.get("/", tags=["Início"], summary="Informações da API")
def raiz() -> dict[str, str]:
    return {
        "api": settings.APP_NAME,
        "versao": settings.APP_VERSION,
        "documentacao": "/docs",
    }
