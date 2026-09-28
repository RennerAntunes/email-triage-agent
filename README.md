# Agente de Triagem de E-mail (Groq + LangChain)

Agente de IA em Python que analisa e-mails e produz uma **triagem estruturada e
validada**: categoria, prioridade, sentimento, resumo, ação sugerida e um
rascunho de resposta opcional. Usa um modelo de LLM **gratuito** da Groq através
do **LangChain**, com `PydanticOutputParser` para garantir que a saída venha
sempre como JSON validado — nunca texto solto.

O agente pode rodar totalmente offline (sobre e-mails de exemplo) ou conectado à
sua conta de e-mail real via IMAP/SMTP, com guardrails de segurança que impedem
o envio automático de qualquer mensagem.

---

## Índice

- [Como funciona](#como-funciona)
- [Arquitetura](#arquitetura)
- [O contrato de saída (EmailTriage)](#o-contrato-de-saída-emailtriage)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração (.env)](#configuração-env)
- [Como obter as credenciais](#como-obter-as-credenciais)
- [Uso](#uso)
- [Modos de operação](#modos-de-operação)
- [Segurança](#segurança)
- [Testes](#testes)
- [Solução de problemas](#solução-de-problemas)
- [Estrutura de arquivos](#estrutura-de-arquivos)
- [Limitações e próximos passos](#limitações-e-próximos-passos)

---

## Como funciona

1. Um e-mail (de exemplo ou lido do servidor) é convertido em texto simples.
2. Esse texto é injetado num prompt junto com as instruções de formato geradas
   pelo `PydanticOutputParser`.
3. O modelo da Groq processa e devolve um JSON.
4. O `PydanticOutputParser` valida esse JSON contra o schema `EmailTriage`. Se o
   JSON vier malformado, o `OutputFixingParser` faz uma segunda chamada ao modelo
   para corrigi-lo automaticamente.
5. O resultado tipado é exibido de forma legível; opcionalmente, um rascunho de
   resposta pode ser enviado após confirmação humana.

O fluxo completo:

```
e-mail --> texto --> prompt (+ format_instructions) --> Groq LLM --> JSON
       --> PydanticOutputParser (+ OutputFixingParser) --> EmailTriage validado
```

---

## Arquitetura

O projeto segue uma arquitetura em camadas com responsabilidades desacopladas:

```
src/main.py            CLI e orquestração dos modos de operação
   │
   ├── src/chain.py        pipeline LCEL: prompt | llm(Groq) | parser
   ├── src/email_client.py I/O de e-mail: IMAP (ler) + SMTP (enviar)
   ├── src/models.py       schemas Pydantic: EmailTriage + EmailMessage
   ├── src/prompts.py      template de prompt da triagem
   └── src/config.py       carga/validação de configuração (.env)

data/sample_emails.py  e-mails de exemplo para o modo offline
tests/                 suíte pytest (sem chamadas de rede reais)
```

Princípio de design: **o `email_client` não conhece nada de IA e a `chain` não
conhece nada de IMAP**. Eles se comunicam apenas por meio de texto puro,
orquestrados pelo `main`. Isso mantém o núcleo de IA testável de forma isolada e
permite trocar a camada de e-mail (ou o modelo) sem tocar no resto.

O `llm` é passado à chain por **injeção de dependência** (`build_triage_chain(llm)`),
o que permite injetar um modelo fake nos testes e não depender da API real.

---

## O contrato de saída (EmailTriage)

Toda triagem produz um objeto validado com os campos abaixo. Os campos com
valores fixos usam **Enums**, o que força o modelo a escolher de um conjunto
fechado e reduz drasticamente saídas inválidas.

| Campo | Tipo | Valores possíveis |
|-------|------|-------------------|
| `categoria` | Enum | `suporte`, `vendas`, `financeiro`, `spam`, `pessoal`, `outro` |
| `prioridade` | Enum | `urgente`, `alta`, `media`, `baixa` |
| `sentimento` | Enum | `positivo`, `neutro`, `negativo` |
| `resumo` | texto | Resumo em 1-2 frases |
| `acao_sugerida` | Enum | `responder`, `encaminhar`, `arquivar`, `ignorar` |
| `rascunho_resposta` | texto ou `null` | Preenchido apenas quando a ação é `responder` |

Exemplo de saída (JSON produzido pelo modelo, já validado):

```json
{
  "categoria": "suporte",
  "prioridade": "urgente",
  "sentimento": "negativo",
  "resumo": "Cliente relata que o sistema está fora do ar em produção.",
  "acao_sugerida": "responder",
  "rascunho_resposta": "Olá, obrigado por avisar. Já estamos investigando..."
}
```

---

## Requisitos

- Python 3.10 ou superior (desenvolvido e testado em 3.12)
- Uma chave gratuita da Groq — https://console.groq.com
- Para a Fase 2: uma conta de e-mail com IMAP/SMTP habilitados e uma App Password

---

## Instalação

```bash
cd email-triage-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Nota sobre ambientes Debian/Ubuntu

Se o comando `python3 -m venv` falhar com `ensurepip is not available`, o pacote
do venv não está instalado. Você tem duas opções:

Opção A (recomendada), instalar o pacote do venv:

```bash
sudo apt install python3-venv    # ou python3.12-venv conforme sua versão
```

Opção B, sem privilégios de administrador, criar o venv sem pip e instalar o pip
manualmente:

```bash
python3 -m venv --without-pip .venv
curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
.venv/bin/python /tmp/get-pip.py
.venv/bin/pip install -r requirements.txt
```

---

## Configuração (.env)

Copie o template e preencha os valores:

```bash
cp .env.example .env
```

Variáveis disponíveis:

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `GROQ_API_KEY` | Sim (para triagem) | — | Chave da API Groq |
| `GROQ_MODEL` | Não | `llama-3.3-70b-versatile` | Modelo da Groq a usar |
| `EMAIL_ADDRESS` | Sim (Fase 2) | — | Seu endereço de e-mail |
| `EMAIL_APP_PASSWORD` | Sim (Fase 2) | — | App Password (não a senha real) |
| `IMAP_SERVER` | Não | `imap.gmail.com` | Servidor IMAP de leitura |
| `IMAP_PORT` | Não | `993` | Porta IMAP (SSL) |
| `SMTP_SERVER` | Não | `smtp.gmail.com` | Servidor SMTP de envio |
| `SMTP_PORT` | Não | `587` | Porta SMTP (STARTTLS) |

As credenciais de e-mail são opcionais para a Fase 1: o modo `--demo` roda apenas
com a `GROQ_API_KEY`. A validação das credenciais de e-mail só acontece quando
você usa os modos que conectam ao servidor.

Servidores comuns para outros provedores:

| Provedor | IMAP | SMTP |
|----------|------|------|
| Gmail | `imap.gmail.com:993` | `smtp.gmail.com:587` |
| Outlook / Office 365 | `outlook.office365.com:993` | `smtp.office365.com:587` |
| Yahoo | `imap.mail.yahoo.com:993` | `smtp.mail.yahoo.com:587` |

---

## Como obter as credenciais

### Chave da Groq (gratuita)

1. Acesse https://console.groq.com e crie uma conta.
2. Gere uma API key no painel.
3. Cole em `GROQ_API_KEY` no `.env`.

### App Password do e-mail

Provedores modernos bloqueiam login IMAP/SMTP com a senha normal. Use sempre uma
App Password (senha de aplicativo).

Para Gmail:

1. Ative a verificação em 2 etapas: https://myaccount.google.com/security
2. Gere uma senha de app: https://myaccount.google.com/apppasswords
3. Copie a senha de 16 caracteres (formato `abcd efgh ijkl mnop`).
4. Coloque em `EMAIL_APP_PASSWORD` e seu e-mail em `EMAIL_ADDRESS`.

---

## Uso

Sempre ative o ambiente virtual antes de rodar:

```bash
source .venv/bin/activate
```

Progressão recomendada, do mais seguro ao mais poderoso:

```bash
# 1. Triagem offline sobre e-mails de exemplo (só precisa da GROQ_API_KEY)
python -m src.main --demo

# 2. Ler e triar seus e-mails reais não lidos (somente leitura, não envia nada)
python -m src.main --fetch 5

# 3. Interativo com dry-run: mostra os rascunhos que geraria, sem enviar
python -m src.main --fetch 5 --interactive --dry-run

# 4. Interativo com envio real: pede confirmação (s/N) antes de cada envio
python -m src.main --fetch 5 --interactive
```

Para ver a ajuda completa:

```bash
python -m src.main --help
```

---

## Modos de operação

| Flag | O que faz | Conecta ao e-mail? | Pode enviar? |
|------|-----------|--------------------|--------------|
| `--demo` | Tria os e-mails de exemplo | Não | Não |
| `--fetch N` | Lê e tria N e-mails não lidos | Sim (leitura) | Não |
| `--fetch N --interactive` | Tria e oferece enviar rascunhos | Sim | Sim (com confirmação) |
| `--fetch N --interactive --dry-run` | Tria e mostra rascunhos | Sim | Não |

`--demo` e `--fetch` são mutuamente exclusivos (você usa um ou outro). O envio só
acontece no modo `--interactive` sem `--dry-run`, e ainda assim exige que você
responda `s` a cada e-mail.

---

## Segurança

- **App Password, nunca a senha real.** Documentado acima; a senha real não deve
  ser usada.
- **`.env` está no `.gitignore`** — as credenciais nunca vão para o controle de
  versão.
- **Somente leitura por padrão.** Nenhum modo envia e-mail sem que você habilite
  `--interactive` explicitamente.
- **Confirmação humana obrigatória.** Mesmo em modo interativo, o agente pergunta
  antes de cada envio. Ele nunca envia sozinho.
- **`--dry-run`** permite revisar todos os rascunhos com zero risco de envio.
- **Rate limits da Groq.** O tier gratuito tem limite de requisições por minuto.
  Há uma pausa de 1 segundo entre e-mails; ao processar muitos de uma vez, você
  pode atingir o limite (use um `N` menor em `--fetch`).

---

## Testes

```bash
python -m pytest
```

A suíte tem 13 testes e **não faz chamadas reais** — não gasta cota da Groq nem
conecta a servidores de e-mail:

| Arquivo | O que cobre | Estratégia |
|---------|-------------|------------|
| `tests/test_models.py` | Validação dos schemas e Enums, `to_text()` | Instanciação direta + casos inválidos |
| `tests/test_chain.py` | Pipeline de triagem e parsing | `FakeListChatModel` (LLM fake) |
| `tests/test_email_client.py` | Leitura IMAP, parsing MIME, envio SMTP, logout | Mock de `imaplib` e `smtplib` |

---

## Solução de problemas

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| `GROQ_API_KEY não configurada` | `.env` ausente ou vazio | Copie `.env.example` para `.env` e preencha a chave |
| `Credenciais de e-mail ausentes` | Usou `--fetch` sem configurar e-mail | Preencha `EMAIL_ADDRESS` e `EMAIL_APP_PASSWORD` |
| Erro de autenticação IMAP | Usou a senha normal em vez de App Password | Gere e use uma App Password |
| `ensurepip is not available` | Pacote do venv não instalado | Veja a seção de instalação (Opção A ou B) |
| Respostas lentas ou erro de limite | Rate limit da Groq atingido | Reduza o `N` em `--fetch` |

---

## Estrutura de arquivos

```
email-triage-agent/
├── .env.example          # template das variáveis de ambiente
├── .gitignore            # ignora .env, .venv, caches
├── requirements.txt      # dependências (LangChain pinado na série 0.3)
├── pytest.ini            # configuração do pytest
├── README.md
├── src/
│   ├── __init__.py
│   ├── config.py         # Settings (pydantic-settings) + validações
│   ├── models.py         # EmailTriage (Enums) + EmailMessage
│   ├── prompts.py        # SYSTEM_PROMPT + build_prompt()
│   ├── chain.py          # build_llm, build_triage_chain, triage_email
│   ├── email_client.py   # EmailClient: fetch_unread, send_reply
│   └── main.py           # CLI e orquestração
├── data/
│   ├── __init__.py
│   └── sample_emails.py  # 5 e-mails de exemplo
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_chain.py
    └── test_email_client.py
```

---

## Limitações e próximos passos

Estado atual e limitações conhecidas:

- Os testes usam mocks; **um teste ponta-a-ponta com credenciais reais ainda não
  foi executado** (requer chave Groq e App Password do usuário).
- O parsing de corpo extrai apenas a primeira parte `text/plain`; e-mails só em
  HTML podem vir vazios ou reduzidos.
- Anexos não são processados.
- Marca os e-mails como lidos ao buscá-los? Não: usa `BODY.PEEK`, que preserva o
  status de não lido no servidor.

Ideias de evolução:

- Extrair texto de e-mails HTML (ex.: com `beautifulsoup4`).
- Processar um arquivo CSV/mbox em lote e exportar os resultados.
- Adicionar few-shot examples ao prompt para melhorar a consistência.
- Cache de resultados e tratamento explícito de rate limit com backoff.
- Métricas de avaliação comparando a triagem com rótulos manuais.

---

## Dependências principais

- `langchain` / `langchain-core` (série 0.3) — orquestração e parsers
- `langchain-groq` — integração com os modelos da Groq
- `pydantic` / `pydantic-settings` — schemas e configuração
- `pytest` / `pytest-mock` — testes

A série 0.3 do LangChain é fixada de propósito: a 1.x moveu o
`OutputFixingParser` para outro pacote, e o pinning garante uma API estável e
alinhada com a maioria dos tutoriais.
