"""Classes base, tipos e validações reutilizados pelos schemas."""
import re
from datetime import date
from decimal import Decimal
from typing import Annotated, ClassVar

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, PlainSerializer, model_validator


class SchemaEntrada(BaseModel):
    """Base dos schemas que recebem dados (Create/Update).

    - remove espaços extras no início e no fim dos textos;
    - recusa campos que não existem no schema (evita erros de digitação no JSON).
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class SchemaAtualizacao(SchemaEntrada):
    """Base dos schemas de atualização (PATCH).

    Todos os campos são opcionais (só é alterado o que for enviado), mas campos
    obrigatórios no banco não podem ser enviados como `null`.
    """

    campos_que_aceitam_nulo: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _bloquear_nulo_em_campo_obrigatorio(self):
        for campo in self.model_fields_set:
            if getattr(self, campo) is None and campo not in self.campos_que_aceitam_nulo:
                raise ValueError(f"O campo '{campo}' não pode ser nulo.")
        return self


class SchemaResposta(BaseModel):
    """Base dos schemas de resposta: permite criar o schema direto do objeto do SQLAlchemy."""

    model_config = ConfigDict(from_attributes=True)


class MensagemErro(BaseModel):
    """Formato das respostas de erro (aparece na documentação do Swagger)."""

    detail: str


# ---------------------------------------------------------------------------
# Tipos reutilizáveis
# ---------------------------------------------------------------------------

# Dinheiro: Decimal internamente (sem erro de arredondamento), número no JSON de resposta.
Dinheiro = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


def _so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor)


def validar_cpf(valor: str) -> str:
    """Aceita CPF com ou sem pontuação, confere os dígitos verificadores e devolve só os números."""
    cpf = _so_digitos(valor)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValueError("CPF inválido: informe 11 dígitos.")
    for posicao in (9, 10):
        soma = sum(int(cpf[i]) * (posicao + 1 - i) for i in range(posicao))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[posicao]):
            raise ValueError("CPF inválido: dígitos verificadores não conferem.")
    return cpf


def validar_cnh(valor: str) -> str:
    cnh = _so_digitos(valor)
    if len(cnh) != 11:
        raise ValueError("CNH inválida: informe os 11 dígitos do número de registro.")
    return cnh


def validar_telefone(valor: str) -> str:
    telefone = _so_digitos(valor)
    if len(telefone) not in (10, 11):
        raise ValueError("Telefone inválido: informe DDD + número (10 ou 11 dígitos).")
    return telefone


_PADRAO_PLACA = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")


def validar_placa(valor: str) -> str:
    """Aceita o padrão antigo (ABC1234) e o Mercosul (ABC1D23), com ou sem hífen."""
    placa = valor.upper().replace("-", "").replace(" ", "")
    if not _PADRAO_PLACA.match(placa):
        raise ValueError("Placa inválida: use o padrão ABC1234 ou o Mercosul ABC1D23.")
    return placa


def validar_ano_veiculo(ano: int) -> int:
    ano_maximo = date.today().year + 1
    if not 1980 <= ano <= ano_maximo:
        raise ValueError(f"Ano inválido: informe um ano entre 1980 e {ano_maximo}.")
    return ano


def validar_maioridade(nascimento: date) -> date:
    hoje = date.today()
    if nascimento > hoje:
        raise ValueError("A data de nascimento não pode estar no futuro.")
    idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
    if idade < 18:
        raise ValueError("O cliente precisa ter pelo menos 18 anos.")
    return nascimento


CPF = Annotated[str, AfterValidator(validar_cpf)]
CNH = Annotated[str, AfterValidator(validar_cnh)]
Telefone = Annotated[str, AfterValidator(validar_telefone)]
Placa = Annotated[str, AfterValidator(validar_placa)]
AnoVeiculo = Annotated[int, AfterValidator(validar_ano_veiculo)]
DataNascimento = Annotated[date, AfterValidator(validar_maioridade)]
Email = Annotated[EmailStr, AfterValidator(str.lower)]
