from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.3-70b-versatile")

    email_address: str = Field(default="")
    email_app_password: str = Field(default="")
    imap_server: str = Field(default="imap.gmail.com")
    imap_port: int = Field(default=993)
    smtp_server: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)

    def require_groq(self) -> None:
        if not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY não configurada. Copie .env.example para .env "
                "e preencha a chave (https://console.groq.com)."
            )

    def require_email(self) -> None:
        faltando = [
            nome
            for nome, valor in (
                ("EMAIL_ADDRESS", self.email_address),
                ("EMAIL_APP_PASSWORD", self.email_app_password),
            )
            if not valor
        ]
        if faltando:
            raise ValueError(
                f"Credenciais de e-mail ausentes: {', '.join(faltando)}. "
                "Configure no .env usando uma App Password (não a senha real)."
            )


def load_settings() -> Settings:
    return Settings()
