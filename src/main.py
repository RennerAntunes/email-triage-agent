from __future__ import annotations

import argparse
import sys
import time

from .chain import build_llm, build_triage_chain, triage_email
from .config import load_settings
from .models import EmailMessage, EmailTriage


def _format_triage(msg: EmailMessage, triage: EmailTriage) -> str:
    linhas = [
        "=" * 70,
        f"De:        {msg.remetente}",
        f"Assunto:   {msg.assunto}",
        "-" * 70,
        f"Categoria:  {triage.categoria.value}",
        f"Prioridade: {triage.prioridade.value}",
        f"Sentimento: {triage.sentimento.value}",
        f"Ação:       {triage.acao_sugerida.value}",
        f"Resumo:     {triage.resumo}",
    ]
    if triage.rascunho_resposta:
        linhas.append("-" * 70)
        linhas.append("Rascunho de resposta:")
        linhas.append(triage.rascunho_resposta)
    linhas.append("=" * 70)
    return "\n".join(linhas)


def _build_chain_or_exit(settings):
    try:
        settings.require_groq()
    except ValueError as exc:
        print(f"[erro] {exc}", file=sys.stderr)
        sys.exit(1)
    llm = build_llm(settings.groq_api_key, settings.groq_model)
    return build_triage_chain(llm)


def run_demo(settings) -> None:
    from data.sample_emails import SAMPLE_EMAILS

    chain = _build_chain_or_exit(settings)
    for msg in SAMPLE_EMAILS:
        triage = triage_email(chain, msg.to_text())
        print(_format_triage(msg, triage))
        time.sleep(1)


def run_fetch(settings, limit: int, interactive: bool, dry_run: bool) -> None:
    from .email_client import EmailClient

    try:
        settings.require_email()
    except ValueError as exc:
        print(f"[erro] {exc}", file=sys.stderr)
        sys.exit(1)

    chain = _build_chain_or_exit(settings)

    with EmailClient(settings) as client:
        mensagens = client.fetch_unread(limit=limit)
        if not mensagens:
            print("Nenhum e-mail não lido encontrado.")
            return

        for msg in mensagens:
            triage = triage_email(chain, msg.to_text())
            print(_format_triage(msg, triage))

            if not interactive:
                time.sleep(1)
                continue

            if triage.acao_sugerida.value != "responder" or not triage.rascunho_resposta:
                time.sleep(1)
                continue

            if dry_run:
                print("[dry-run] envio desativado; rascunho não enviado.")
                time.sleep(1)
                continue

            resposta = input("Enviar este rascunho? [s/N] ").strip().lower()
            if resposta == "s":
                assunto = msg.assunto if msg.assunto.lower().startswith("re:") else f"Re: {msg.assunto}"
                client.send_reply(msg.remetente, assunto, triage.rascunho_resposta)
                print("Resposta enviada.")
            else:
                print("Envio cancelado.")
            time.sleep(1)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="email-triage-agent",
        description="Agente de triagem de e-mail com Groq + LangChain.",
    )
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--demo", action="store_true", help="Roda sobre e-mails de exemplo (offline).")
    modo.add_argument("--fetch", type=int, metavar="N", help="Busca e tria N e-mails não lidos via IMAP.")
    parser.add_argument("--interactive", action="store_true", help="Oferece enviar rascunhos (com confirmação).")
    parser.add_argument("--dry-run", action="store_true", help="Nunca envia e-mails; apenas mostra rascunhos.")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    settings = load_settings()

    if args.demo:
        run_demo(settings)
    elif args.fetch is not None:
        run_fetch(
            settings,
            limit=args.fetch,
            interactive=args.interactive,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
