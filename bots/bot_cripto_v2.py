import asyncio
import io
import os
import ccxt
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 1. Carrega variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Inicializa a exchange via CCXT (Binance)
exchange = ccxt.binance(
    {
        "enableRateLimit": True,
    }
)

CRIPTOS_DISPONIVEIS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "ADA/USDT",
    "XRP/USDT",
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.effective_user
    nome = usuario.first_name if usuario.first_name else "Investidor"

    mensagem = (
        f"🤖 *Olá, {nome}! Eu sou seu Bot de Criptomoedas multi-ativo.*\n\n"
        "Comandos disponíveis:\n"
        "• /lista - Mostra os pares padrão monitorados\n"
        "• `/preco PAR` - Vê o preço atual (Ex: `/preco BTC/USDT`)\n"
        "• `/grafico PAR` - Gera o gráfico no estilo Candlestick Dark (Ex: `/grafico ETH/USDT`)"
    )
    await update.message.reply_text(mensagem, parse_mode="Markdown")


async def listar_criptos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "📋 *Pares disponíveis para consulta:*\n" + "\n".join(
        [f"• `{c}`" for c in CRIPTOS_DISPONIVEIS]
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def obter_preco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Por favor, informe o par. Exemplo: `/preco BTC/USDT`",
            parse_mode="Markdown",
        )
        return

    simbolo = context.args[0].upper()

    try:
        ticker = await asyncio.to_thread(exchange.fetch_ticker, simbolo)
        preco = ticker["last"]
        variacao = ticker["percentage"]

        emoji_var = "🟢" if variacao and variacao >= 0 else "🔴"

        resposta = (
            f"📊 *Ativo:* `{simbolo}`\n"
            f"💰 *Preço Atual:* `${preco:,.2f}`\n"
            f"📈 *Variação 24h:* {emoji_var} {variacao}%"
        )
        await update.message.reply_text(resposta, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(
            f"❌ Erro ao buscar o ativo `{simbolo}`. Verifique o par informado.",
            parse_mode="Markdown",
        )


def _gerar_imagem_candlestick(ohlcv) -> io.BytesIO:
    """Função síncrona isolada para renderização única do gráfico em memória."""
    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    up = df[df["close"] >= df["open"]]
    down = df[df["close"] < df["open"]]

    # Instancia figura de forma isolada sem reaproveitar o estado global do pyplot
    fig = Figure(figsize=(10, 5), facecolor="#0e0e0e")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#0e0e0e")

    width = 0.6

    # Velas de Alta (Brancas)
    ax.vlines(
        up.index, up["low"], up["high"], color="#ffffff", linewidth=1, zorder=1
    )
    ax.bar(
        up.index,
        up["close"] - up["open"],
        width,
        bottom=up["open"],
        color="#ffffff",
        edgecolor="#ffffff",
        zorder=2,
    )

    # Velas de Baixa (Vermelho)
    ax.vlines(
        down.index,
        down["low"],
        down["high"],
        color="#ff334b",
        linewidth=1,
        zorder=1,
    )
    ax.bar(
        down.index,
        down["open"] - down["close"],
        width,
        bottom=down["close"],
        color="#ff334b",
        edgecolor="#ff334b",
        zorder=2,
    )

    # Ajustes estéticos
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.tick_params(colors="#888888", labelsize=9)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.15, color="#ffffff")

    for spine in ["top", "left", "bottom", "right"]:
        ax.spines[spine].set_visible(False)

    ax.set_xticks([])
    ax.set_xlim(-1, len(df))

    fig.tight_layout()

    # Salva no buffer de memória RAM
    buf = io.BytesIO()
    fig.savefig(
        buf, format="png", dpi=100, bbox_inches="tight", facecolor="#0e0e0e"
    )
    buf.seek(0)

    # Limpa explicitamente o pyplot global para zerar o acumulador de memória
    plt.clf()
    plt.close("all")

    return buf


async def gerar_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Por favor, informe o par. Exemplo: `/grafico ETH/USDT`",
            parse_mode="Markdown",
        )
        return

    simbolo = context.args[0].upper()

    status_msg = await update.message.reply_text(
        f"⏳ Processando dados e gerando gráfico para `{simbolo}`...",
        parse_mode="Markdown",
    )

    try:
        # Busca os dados OHLCV na thread pool
        ohlcv = await asyncio.to_thread(
            exchange.fetch_ohlcv, simbolo, timeframe="1h", limit=80
        )

        # Gera o gráfico na thread pool com o isolamento de figura
        buf = await asyncio.to_thread(_gerar_imagem_candlestick, ohlcv)

        # Envia uma única foto
        await update.message.reply_photo(
            photo=buf,
            caption=f"📈 Gráfico *{simbolo}* gerado com sucesso.",
            parse_mode="Markdown",
        )

        await status_msg.delete()

    except Exception as e:
        await update.message.reply_text(
            f"❌ Erro ao gerar o gráfico: {str(e)}", parse_mode="Markdown"
        )


def main():
    if not TELEGRAM_TOKEN:
        print("Erro: TELEGRAM_TOKEN não configurado no arquivo .env")
        return

    # Ajusta os timeouts de leitura/escrita da API do Telegram para evitar duplicatas por retry
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("lista", listar_criptos))
    application.add_handler(CommandHandler("preco", obter_preco))
    application.add_handler(CommandHandler("grafico", gerar_grafico))

    print(
        "🤖 Bot multi-ativo iniciado com sucesso! Pressione Ctrl+C para parar."
    )
    application.run_polling()


if __name__ == "__main__":
    main()