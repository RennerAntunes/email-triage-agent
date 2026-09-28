from __future__ import annotations

import email
import imaplib
import smtplib
from email.header import decode_header, make_header
from email.message import EmailMessage as MimeMessage
from email.utils import parseaddr
from types import TracebackType

from .config import Settings
from .models import EmailMessage


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition") or "")
            if content_type == "text/plain" and "attachment" not in disposition:
                payload = part.get_payload(decode=True)
                if payload is not None:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace").strip()
        return ""
    payload = msg.get_payload(decode=True)
    if payload is None:
        return ""
    charset = msg.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace").strip()


class EmailClient:
    def __init__(self, settings: Settings) -> None:
        settings.require_email()
        self.settings = settings
        self._imap: imaplib.IMAP4_SSL | None = None

    def __enter__(self) -> "EmailClient":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.logout()

    def connect(self) -> None:
        self._imap = imaplib.IMAP4_SSL(
            self.settings.imap_server, self.settings.imap_port
        )
        self._imap.login(
            self.settings.email_address, self.settings.email_app_password
        )

    def logout(self) -> None:
        if self._imap is not None:
            try:
                self._imap.close()
            except Exception:
                pass
            try:
                self._imap.logout()
            finally:
                self._imap = None

    def fetch_unread(self, limit: int = 10, mailbox: str = "INBOX") -> list[EmailMessage]:
        if self._imap is None:
            raise RuntimeError("Cliente IMAP não conectado. Use connect() ou 'with'.")

        self._imap.select(mailbox)
        status, data = self._imap.search(None, "UNSEEN")
        if status != "OK":
            return []

        uids = data[0].split()
        uids = uids[-limit:] if limit else uids

        messages: list[EmailMessage] = []
        for raw_uid in uids:
            uid = raw_uid.decode()
            status, msg_data = self._imap.fetch(raw_uid, "(BODY.PEEK[])")
            if status != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            remetente = parseaddr(_decode(msg.get("From")))[1] or _decode(msg.get("From"))
            messages.append(
                EmailMessage(
                    uid=uid,
                    remetente=remetente,
                    assunto=_decode(msg.get("Subject")),
                    corpo=_extract_body(msg),
                    data=_decode(msg.get("Date")),
                )
            )
        return messages

    def send_reply(self, to: str, subject: str, body: str) -> None:
        mime = MimeMessage()
        mime["From"] = self.settings.email_address
        mime["To"] = to
        mime["Subject"] = subject
        mime.set_content(body)

        with smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port) as server:
            server.starttls()
            server.login(
                self.settings.email_address, self.settings.email_app_password
            )
            server.send_message(mime)
