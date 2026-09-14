import asyncio
import io
import os
import ccxt
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


def _gerar_grafico_completo_buffer(df: pd.DataFrame) -> io.BytesIO:
    """Gera o gráfico estilizado com tag de preço e médias móveis diretamente em memória RAM."""
    if len(df) < 21:
        return None

    df_plot = df.tail(60).copy()
    df_plot["DataHora"] = pd.to_datetime(df_plot["DataHora"])
    df_plot = df_plot.reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=130)

    # Fundo estilo escuro profundo / preto
    cor_fundo = "#121212"
    ax.set_facecolor(cor_fundo)
    fig.patch.set_facecolor(cor_fundo)

    # Cores: Alta = Branco | Baixa = Vermelho
    up = df_plot[df_plot["Close"] >= df_plot["Open"]]
    down = df_plot[df_plot["Close"] < df_plot["Open"]]

    cor_alta = "#FFFFFF"
    cor_baixa = "#E53935"

    # Plot dos Pavios
    ax.vlines(
        up.index, up["Low"], up["High"], color=cor_alta, linewidth=1.2, zorder=1
    )
    ax.vlines(
        down.index,
        down["Low"],
        down["High"],
        color=cor_baixa,
        linewidth=1.2,
        zorder=1,
    )

    # Plot dos Corpos das Velas
    largura = 0.6
    ax.bar(
        up.index,
        up["Close"] - up["Open"],
        largura,
        bottom=up["Open"],
        color=cor_alta,
        edgecolor=cor_alta,
        zorder=2,
    )
    ax.bar(
        down.index,
        down["Open"] - down["Close"],
        largura,
        bottom=down["Close"],
        color=cor_baixa,
        edgecolor=cor_baixa,
        zorder=2,
    )

    # Médias Móveis (se calculadas no DataFrame)
    if "SMA_9" in df_plot.columns and "SMA_21" in df_plot.columns:
        ax.plot(
            df_plot.index,
            df_plot["SMA_9"],
            color="#2962FF",
            linewidth=1.2,
            alpha=0.7,
            label="SMA 9",
        )
        ax.plot(
            df_plot.index,
            df_plot["SMA_21"],
            color="#FF6D00",
            linewidth=1.2,
            alpha=0.7,
            label="SMA 21",
        )

    # Linha do Preço Atual (Último Fechamento)
    ultimo_preco = df_plot["Close"].iloc[-1]
    ax.axhline(y=ultimo_preco, color="#E53935", linestyle=":", linewidth=1.2)

    # Tag de preço no eixo Y
    ax.text(
        len(df_plot) - 0.5,
        ultimo_preco,
        f"  {ultimo_preco:,.2f}",
        color="white",
        backgroundcolor="#E53935",
        fontsize=8,
        verticalalignment="center",
        fontweight="bold",
    )

    # Configuração dos Eixos (Preços à Direita)
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.tick_params(axis="both", colors="#888888", labelsize=8.5, length=0)

    # Formatação do Eixo X (Datas)
    passo = max(1, len(df_plot) // 6)
    ticks_x = range(0, len(df_plot), passo)
    labels_x = [df_plot["DataHora"].iloc[i].strftime("%H:%M") for i in ticks_x]
    ax.set_xticks(ticks_x)
    ax.set_xticklabels(labels_x)
    ax.set_xlim(-1, len(df_plot))

    # Grade minimalista
    ax.grid(True, linestyle=":", alpha=0.15, color="white")

    # Bordas invisíveis
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()

    # Salva diretamente na RAM e limpa o estado global do Pyplot
    buf = io.BytesIO()
    plt.savefig(
        buf,
        format="png",
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
        dpi=130,
    )
    buf.seek(0)

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
        # 1. Puxa os dados OHLCV na thread separada (80 velas de 15 minutos)
        ohlcv = await asyncio.to_thread(
            exchange.fetch_ohlcv, simbolo, timeframe="15m", limit=80
        )

        # 2. Prepara o DataFrame adequando as colunas exigidas pela sua função
        df = pd.DataFrame(
            ohlcv,
            columns=["DataHora", "Open", "High", "Low", "Close", "Volume"],
        )
        df["DataHora"] = pd.to_datetime(df["DataHora"], unit="ms")

        # 3. Calcula as Médias Móveis (opcional)
        df["SMA_9"] = df["Close"].rolling(window=9).mean()
        df["SMA_21"] = df["Close"].rolling(window=21).mean()

        # 4. Renderiza a imagem em thread separada
        buf = await asyncio.to_thread(_gerar_grafico_completo_buffer, df)

        if buf is None:
            await update.message.reply_text("❌ Dados insuficientes.")
            return

        # 5. Envia ao Telegram e remove a mensagem temporária
        await update.message.reply_photo(
            photo=buf,
            caption=f"📈 Gráfico *{simbolo}* (15m) gerado com sucesso.",
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