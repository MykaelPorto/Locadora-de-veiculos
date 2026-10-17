"""Enumerações do domínio (valores fixos), usadas nos modelos e nos schemas."""
import enum


class StatusVeiculo(str, enum.Enum):
    DISPONIVEL = "disponivel"
    ALUGADO = "alugado"
    MANUTENCAO = "manutencao"


class StatusLocacao(str, enum.Enum):
    ATIVA = "ativa"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"


def valores_do_enum(classe_enum: type[enum.Enum]) -> list[str]:
    """Faz o SQLAlchemy gravar o *valor* ("disponivel") no banco, e não o nome ("DISPONIVEL")."""
    return [membro.value for membro in classe_enum]
