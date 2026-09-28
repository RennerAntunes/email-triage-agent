import json

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from src.chain import build_triage_chain, triage_email
from src.models import Acao, Categoria, EmailTriage, Prioridade, Sentimento


def _fake_llm(payload: dict) -> FakeListChatModel:
    return FakeListChatModel(responses=[json.dumps(payload)])


def test_triage_chain_parseia_json_valido():
    payload = {
        "categoria": "suporte",
        "prioridade": "urgente",
        "sentimento": "negativo",
        "resumo": "Sistema fora do ar.",
        "acao_sugerida": "responder",
        "rascunho_resposta": "Estamos verificando agora.",
    }
    llm = _fake_llm(payload)
    chain = build_triage_chain(llm, use_fixing_parser=False)

    resultado = triage_email(chain, "e-mail qualquer")

    assert isinstance(resultado, EmailTriage)
    assert resultado.categoria is Categoria.SUPORTE
    assert resultado.prioridade is Prioridade.URGENTE
    assert resultado.sentimento is Sentimento.NEGATIVO
    assert resultado.acao_sugerida is Acao.RESPONDER
    assert resultado.rascunho_resposta == "Estamos verificando agora."


def test_triage_chain_spam_sem_rascunho():
    payload = {
        "categoria": "spam",
        "prioridade": "baixa",
        "sentimento": "neutro",
        "resumo": "Promoção não solicitada.",
        "acao_sugerida": "ignorar",
        "rascunho_resposta": None,
    }
    llm = _fake_llm(payload)
    chain = build_triage_chain(llm, use_fixing_parser=False)

    resultado = triage_email(chain, "ganhe um iphone")

    assert resultado.categoria is Categoria.SPAM
    assert resultado.acao_sugerida is Acao.IGNORAR
    assert resultado.rascunho_resposta is None
