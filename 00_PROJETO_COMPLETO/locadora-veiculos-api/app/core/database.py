"""Conexão com o banco de dados e sessão do SQLAlchemy.

Importante: as tabelas NÃO são criadas aqui. Quem cria e altera o banco
são as migrações do Alembic (`alembic upgrade head`).
"""
import warnings
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# O SQLite não tem tipo DECIMAL nativo; o SQLAlchemy converte e emite um aviso.
# Para valores com 2 casas decimais (dinheiro) a conversão é segura, então o aviso é silenciado.
warnings.filterwarnings("ignore", message=r".*does \*not\* support Decimal objects natively", category=SAWarning)

_eh_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_engine(
    settings.DATABASE_URL,
    # O FastAPI atende requisições em várias threads; o SQLite precisa desta opção para aceitar isso.
    connect_args={"check_same_thread": False} if _eh_sqlite else {},
)

if _eh_sqlite:

    @event.listens_for(engine, "connect")
    def _ativar_chaves_estrangeiras(conexao_dbapi, _registro_conexao) -> None:
        """O SQLite vem com a checagem de FOREIGN KEY desligada. Aqui ela é ligada em toda conexão."""
        cursor = conexao_dbapi.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependência do FastAPI: abre uma sessão por requisição e fecha ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Atalho usado nos routers: `db: SessionDep`
SessionDep = Annotated[Session, Depends(get_db)]
