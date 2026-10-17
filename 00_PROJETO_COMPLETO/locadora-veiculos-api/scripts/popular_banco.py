"""Popula o banco com dados de exemplo (OPCIONAL — útil para explorar as listagens e filtros).

Uso, na raiz do projeto e DEPOIS de `alembic upgrade head`:

    python -m scripts.popular_banco

Os dados passam pelos mesmos schemas e services da API, então seguem todas as validações.
"""
from decimal import Decimal

from sqlalchemy import inspect, select

from app.core.database import SessionLocal, engine
from app.models import Categoria
from app.schemas.categoria import CategoriaCreate
from app.schemas.cliente import ClienteCreate
from app.schemas.veiculo import VeiculoCreate
from app.services import categoria_service, cliente_service, veiculo_service


def main() -> None:
    if not inspect(engine).has_table("categorias"):
        print("As tabelas ainda não existem. Rode primeiro:  alembic upgrade head")
        return

    with SessionLocal() as db:
        if db.scalar(select(Categoria.id).limit(1)) is not None:
            print("O banco já possui dados; nada foi inserido.")
            return

        economico = categoria_service.criar(
            db, CategoriaCreate(nome="Econômico", descricao="Compactos e econômicos.", valor_diaria=Decimal("110.00"))
        )
        intermediario = categoria_service.criar(
            db, CategoriaCreate(nome="Intermediário", descricao="Sedãs e hatches médios.", valor_diaria=Decimal("160.00"))
        )
        executivo = categoria_service.criar(
            db, CategoriaCreate(nome="Executivo", descricao="Sedãs completos e confortáveis.", valor_diaria=Decimal("290.00"))
        )

        veiculos = [
            ("BRA2E19", "Fiat", "Mobi", 2023, "Branco", 22000, economico.id),
            ("KLM4F56", "Renault", "Kwid", 2024, "Vermelho", 8000, economico.id),
            ("RST7H89", "Hyundai", "HB20S", 2023, "Prata", 31000, intermediario.id),
            ("JKL5M67", "Chevrolet", "Onix Plus", 2024, "Cinza", 12000, intermediario.id),
            ("XYZ1234", "Toyota", "Corolla", 2025, "Preto", 5000, executivo.id),
        ]
        for placa, marca, modelo, ano, cor, km, categoria_id in veiculos:
            veiculo_service.criar(
                db,
                VeiculoCreate(
                    placa=placa, marca=marca, modelo=modelo, ano=ano, cor=cor, quilometragem=km, categoria_id=categoria_id
                ),
            )

        cliente_service.criar(
            db,
            ClienteCreate(
                nome="João Pereira",
                cpf="111.444.777-35",
                email="joao.pereira@email.com",
                telefone="(86) 98765-4321",
                cnh="11122233344",
                data_nascimento="1988-09-03",
            ),
        )
        cliente_service.criar(
            db,
            ClienteCreate(
                nome="Ana Beatriz Lima",
                cpf="123.456.789-09",
                email="ana.lima@email.com",
                telefone="(86) 99123-4567",
                cnh="55566677788",
                data_nascimento="1999-02-20",
            ),
        )

    print("Dados de exemplo inseridos: 3 categorias, 5 veículos e 2 clientes.")


if __name__ == "__main__":
    main()
