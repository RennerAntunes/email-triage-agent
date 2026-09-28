import pytest
from pydantic import ValidationError

from src.models import (
    Acao,
    Categoria,
    EmailMessage,
    EmailTriage,
    Prioridade,
    Sentimento,
)


def test_email_triage_valido():
    triage = EmailTriage(
        categoria="suporte",
        prioridade="urgente",
        sentimento="negativo",
        resumo="Cliente relata sistema fora do ar.",
        acao_sugerida="responder",
        rascunho_resposta="Olá, já estamos verificando.",
    )
    assert triage.categoria is Categoria.SUPORTE
    assert triage.prioridade is Prioridade.URGENTE
    assert triage.sentimento is Sentimento.NEGATIVO
    assert triage.acao_sugerida is Acao.RESPONDER


def test_email_triage_rascunho_opcional():
    triage = EmailTriage(
        categoria="spam",
        prioridade="baixa",
        sentimento="neutro",
        resumo="Promoção não solicitada.",
        acao_sugerida="ignorar",
    )
    assert triage.rascunho_resposta is None


def test_email_triage_categoria_invalida():
    with pytest.raises(ValidationError):
        EmailTriage(
            categoria="inexistente",
            prioridade="alta",
            sentimento="neutro",
            resumo="x",
            acao_sugerida="responder",
        )


def test_email_triage_prioridade_invalida():
    with pytest.raises(ValidationError):
        EmailTriage(
            categoria="vendas",
            prioridade="critica",
            sentimento="neutro",
            resumo="x",
            acao_sugerida="responder",
        )


def test_email_message_to_text():
    msg = EmailMessage(
        uid="10",
        remetente="a@b.com",
        assunto="Teste",
        corpo="Corpo do e-mail.",
        data="Mon, 28 Sep 2026 09:00:00 -0300",
    )
    texto = msg.to_text()
    assert "De: a@b.com" in texto
    assert "Assunto: Teste" in texto
    assert "Corpo do e-mail." in texto
