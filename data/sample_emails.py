from src.models import EmailMessage

SAMPLE_EMAILS = [
    EmailMessage(
        uid="1",
        remetente="cliente.raiva@empresa.com",
        assunto="URGENTE: sistema fora do ar em produção",
        data="Mon, 28 Sep 2026 09:12:00 -0300",
        corpo=(
            "Bom dia, nosso sistema parou completamente há 30 minutos e "
            "estamos perdendo vendas. Isso é inaceitável, preciso de uma "
            "solução AGORA. Já é a segunda vez este mês."
        ),
    ),
    EmailMessage(
        uid="2",
        remetente="lead@startupnova.com",
        assunto="Interesse no plano Enterprise",
        data="Mon, 28 Sep 2026 10:03:00 -0300",
        corpo=(
            "Olá, vi a demonstração de vocês e gostaria de entender melhor "
            "os preços do plano Enterprise para uma equipe de 50 pessoas. "
            "Podem me enviar uma proposta?"
        ),
    ),
    EmailMessage(
        uid="3",
        remetente="promo@ofertasimperdiveis.biz",
        assunto="🔥 VOCÊ GANHOU um iPhone 15! Clique AGORA",
        data="Mon, 28 Sep 2026 03:44:00 -0300",
        corpo=(
            "Parabéns!!! Você foi selecionado para receber um prêmio "
            "exclusivo. Basta clicar no link e informar seus dados bancários "
            "para liberar o resgate. Oferta expira em 1 hora!"
        ),
    ),
    EmailMessage(
        uid="4",
        remetente="financeiro@fornecedor.com",
        assunto="Fatura #4471 - vencimento em 5 dias",
        data="Mon, 28 Sep 2026 08:00:00 -0300",
        corpo=(
            "Prezados, segue em anexo a fatura referente aos serviços de "
            "setembro, no valor de R$ 3.200,00, com vencimento em 03/10. "
            "Qualquer dúvida estamos à disposição."
        ),
    ),
    EmailMessage(
        uid="5",
        remetente="amigo.antigo@gmail.com",
        assunto="Faz tempo! Bora tomar um café?",
        data="Sun, 27 Sep 2026 19:30:00 -0300",
        corpo=(
            "E aí, sumido! Vi que você mudou de emprego. Que tal marcarmos "
            "um café no fim de semana pra colocar o papo em dia?"
        ),
    ),
]
