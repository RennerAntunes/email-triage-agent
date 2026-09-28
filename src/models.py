from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Categoria(str, Enum):
    SUPORTE = "suporte"
    VENDAS = "vendas"
    FINANCEIRO = "financeiro"
    SPAM = "spam"
    PESSOAL = "pessoal"
    OUTRO = "outro"


class Prioridade(str, Enum):
    URGENTE = "urgente"
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


class Sentimento(str, Enum):
    POSITIVO = "positivo"
    NEUTRO = "neutro"
    NEGATIVO = "negativo"


class Acao(str, Enum):
    RESPONDER = "responder"
    ENCAMINHAR = "encaminhar"
    ARQUIVAR = "arquivar"
    IGNORAR = "ignorar"


class EmailTriage(BaseModel):
    categoria: Categoria = Field(description="Categoria do e-mail")
    prioridade: Prioridade = Field(description="Nível de prioridade")
    sentimento: Sentimento = Field(description="Sentimento geral do remetente")
    resumo: str = Field(description="Resumo do e-mail em 1-2 frases")
    acao_sugerida: Acao = Field(description="Ação recomendada")
    rascunho_resposta: str | None = Field(
        default=None,
        description="Rascunho de resposta, se a ação for responder; senão null",
    )


class EmailMessage(BaseModel):
    uid: str
    remetente: str
    assunto: str
    corpo: str
    data: str = ""

    def to_text(self) -> str:
        return (
            f"De: {self.remetente}\n"
            f"Assunto: {self.assunto}\n"
            f"Data: {self.data}\n\n"
            f"{self.corpo}"
        )
