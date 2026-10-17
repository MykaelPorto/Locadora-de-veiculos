"""Configurações da aplicação.

Os valores podem ser sobrescritos por variáveis de ambiente ou por um arquivo `.env`
na raiz do projeto (veja `.env.example`).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Locadora de Veículos API"
    APP_VERSION: str = "1.0.0"

    # SQLite por padrão (não precisa instalar nada). Para PostgreSQL, por exemplo:
    # DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/locadora
    DATABASE_URL: str = "sqlite:///./locadora.db"


settings = Settings()
