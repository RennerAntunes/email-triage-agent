from email.message import EmailMessage as MimeMessage
from unittest.mock import MagicMock

import pytest

from src.config import Settings
from src.email_client import EmailClient


def _settings() -> Settings:
    return Settings(
        groq_api_key="x",
        email_address="agente@teste.com",
        email_app_password="app pass fake",
    )


def _raw_email(remetente: str, assunto: str, corpo: str) -> bytes:
    mime = MimeMessage()
    mime["From"] = remetente
    mime["Subject"] = assunto
    mime["Date"] = "Mon, 28 Sep 2026 09:00:00 -0300"
    mime.set_content(corpo)
    return mime.as_bytes()


def test_require_email_falha_sem_credenciais():
    settings = Settings(groq_api_key="x")
    with pytest.raises(ValueError):
        EmailClient(settings)


def test_fetch_unread_parseia_mensagens(monkeypatch):
    raw = _raw_email("Fulano <fulano@ex.com>", "Assunto Teste", "Corpo de teste.")

    fake_imap = MagicMock()
    fake_imap.search.return_value = ("OK", [b"1"])
    fake_imap.fetch.return_value = ("OK", [(b"1 (BODY[])", raw)])

    monkeypatch.setattr(
        "src.email_client.imaplib.IMAP4_SSL", lambda *a, **k: fake_imap
    )

    client = EmailClient(_settings())
    client.connect()
    mensagens = client.fetch_unread(limit=5)

    assert len(mensagens) == 1
    msg = mensagens[0]
    assert msg.remetente == "fulano@ex.com"
    assert msg.assunto == "Assunto Teste"
    assert "Corpo de teste." in msg.corpo
    fake_imap.search.assert_called_once_with(None, "UNSEEN")


def test_fetch_unread_sem_mensagens(monkeypatch):
    fake_imap = MagicMock()
    fake_imap.search.return_value = ("OK", [b""])

    monkeypatch.setattr(
        "src.email_client.imaplib.IMAP4_SSL", lambda *a, **k: fake_imap
    )

    client = EmailClient(_settings())
    client.connect()
    assert client.fetch_unread() == []


def test_fetch_unread_sem_conexao_levanta():
    client = EmailClient(_settings())
    with pytest.raises(RuntimeError):
        client.fetch_unread()


def test_send_reply_usa_smtp(monkeypatch):
    fake_smtp = MagicMock()
    fake_context = MagicMock()
    fake_context.__enter__.return_value = fake_smtp
    fake_context.__exit__.return_value = False

    monkeypatch.setattr(
        "src.email_client.smtplib.SMTP", lambda *a, **k: fake_context
    )

    client = EmailClient(_settings())
    client.send_reply("dest@ex.com", "Re: Assunto", "Corpo da resposta.")

    fake_smtp.starttls.assert_called_once()
    fake_smtp.login.assert_called_once_with("agente@teste.com", "app pass fake")
    fake_smtp.send_message.assert_called_once()


def test_context_manager_faz_logout(monkeypatch):
    fake_imap = MagicMock()
    fake_imap.search.return_value = ("OK", [b""])
    monkeypatch.setattr(
        "src.email_client.imaplib.IMAP4_SSL", lambda *a, **k: fake_imap
    )

    with EmailClient(_settings()) as client:
        client.fetch_unread()

    fake_imap.logout.assert_called_once()
