import asyncio
import io
import os
from datetime import datetime
import ccxt
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 1. Configurações Iniciais
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

exchange = ccxt.binance({"enableRateLimit": True})

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
        f"Olá, *{nome}*! Bem-vindo ao seu painel de monitoramento de ativos em tempo real.\n\n"
        f"📌 *COMANDOS DISPONÍVEIS*\n\n"
        f"📋 `/lista` \n└ Lista todos os pares configurados\n\n"
        f"💵 `/preco <PAR>` \n└ Cotação atualizada + variação 24h\n"
        f"  _Exemplo:_ `/preco BTC/USDT`\n\n"
        f"📈 `/grafico <PAR>` \n└ Gera o gráfico de velas com SMA 9 e 21\n"
        f"  _Exemplo:_ `/grafico ETH/USDT`\n\n"
        f"💡 _Dica: Digite o par exatamente como listado._"
    )
    await update.message.reply_text(mensagem, parse_mode="Markdown")


async def listar_criptos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lista_formatada = "\n".join([f"💵 `{c}`" for c in CRIPTOS_DISPONIVEIS])

    texto = (
        f"📋 *PARES DISPONÍVEIS*\n\n"
        f"{lista_formatada}\n\n"
        f"💬 Use `/preco PAR` ou `/grafico PAR` para consultar."
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def obter_preco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ *Comando incompleto!*\n\n"
            "Use o formato: `/preco <PAR>`\n"
            "Exemplo: `/preco BTC/USDT`",
            parse_mode="Markdown",
        )
        return

    simbolo = context.args[0].upper()

    try:
        ticker = await asyncio.to_thread(exchange.fetch_ticker, simbolo)
        preco = ticker["last"]
        variacao = ticker.get("percentage", 0.0)
        high = ticker.get("high", 0.0)
        low = ticker.get("low", 0.0)

        # Visual de Variação
        if variacao >= 0:
            emoji_var = "🟢"
            sinal = "+"
            status_cor = "ALTA"
        else:
            emoji_var = "🔴"
            sinal = ""
            status_cor = "BAIXA"

        agora = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

        resposta = (
            f"💎 *{simbolo}*  •  `{status_cor}`\n\n"
            f"💰 *Preço Atual:* `{preco:,.2f} USDT`\n"
            f"{emoji_var} *Variação 24h:* `{sinal}{variacao:.2f}%`\n\n"
            f"📊 *Máxima 24h:* `${high:,.2f}`\n"
            f"📉 *Mínima 24h:* `${low:,.2f}`\n\n"
            f"⏱ _Atualizado em {agora}_"
        )
        await update.message.reply_text(resposta, parse_mode="Markdown")

    except Exception:
        await update.message.reply_text(
            f"❌ *Ativo não encontrado!*\n\n"
            f"Não foi possível buscar dados para `{simbolo}`.\n"
            f"Verifique se o par está correto (Ex: `BTC/USDT`).",
            parse_mode="Markdown",
        )


def _gerar_grafico_completo_buffer(df: pd.DataFrame, simbolo: str) -> io.BytesIO:
    """Gera o gráfico estilizado com velas brancas/vermelhas e fundo escuro."""
    if len(df) < 21:
        return None

    df_plot = df.tail(60).copy()
    df_plot["DataHora"] = pd.to_datetime(df_plot["DataHora"])
    df_plot = df_plot.reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=140)

    # Fundo escuro
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

    # Médias Móveis
    if "SMA_9" in df_plot.columns and "SMA_21" in df_plot.columns:
        ax.plot(
            df_plot.index,
            df_plot["SMA_9"],
            color="#2962FF",
            linewidth=1.2,
            alpha=0.8,
            label="SMA 9",
        )
        ax.plot(
            df_plot.index,
            df_plot["SMA_21"],
            color="#FF6D00",
            linewidth=1.2,
            alpha=0.8,
            label="SMA 21",
        )

    # Linha e Tag de Preço Atual
    ultimo_preco = df_plot["Close"].iloc[-1]
    ax.axhline(y=ultimo_preco, color="#E53935", linestyle=":", linewidth=1.2)

    ax.text(
        len(df_plot) - 0.5,
        ultimo_preco,
        f"  {ultimo_preco:,.2f} ",
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
    ax.set_xlim(-1, len(df_plot) + 2)

    # Título do Gráfico no próprio Canvas
    ax.set_title(
        f"{simbolo} • Timeframe 15m",
        loc="left",
        color="#FFFFFF",
        fontsize=11,
        fontweight="bold",
        pad=12,
    )

    ax.legend(loc="upper left", frameon=False, fontsize=8, labelcolor="#888888")
    ax.grid(True, linestyle=":", alpha=0.15, color="white")

    # Bordas invisíveis
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()

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
            "⚠️ *Comando incompleto!*\n\n"
            "Use o formato: `/grafico <PAR>`\n"
            "Exemplo: `/grafico ETH/USDT`",
            parse_mode="Markdown",
        )
        return

    simbolo = context.args[0].upper()

    status_msg = await update.message.reply_text(
        f"⏳ *Gerando análise visual para `{simbolo}`...*\n"
        f"_Buscando velas de 15m e calculando indicadores..._",
        parse_mode="Markdown",
    )

    try:
        ohlcv = await asyncio.to_thread(
            exchange.fetch_ohlcv, simbolo, timeframe="15m", limit=80
        )

        df = pd.DataFrame(
            ohlcv,
            columns=["DataHora", "Open", "High", "Low", "Close", "Volume"],
        )
        df["DataHora"] = pd.to_datetime(df["DataHora"], unit="ms")

        df["SMA_9"] = df["Close"].rolling(window=9).mean()
        df["SMA_21"] = df["Close"].rolling(window=21).mean()

        buf = await asyncio.to_thread(_gerar_grafico_completo_buffer, df, simbolo)

        if buf is None:
            await update.message.reply_text("❌ *Dados insuficientes para gerar o gráfico.*")
            return

        caption_text = (
            f"📈 *ANÁLISE TÉCNICA* • `{simbolo}`\n\n"
            f"⏱ *Timeframe:* 15 Minutos\n"
            f"🟦 *SMA 9:* Média Curta\n"
            f"🟧 *SMA 21:* Média Longa\n\n"
            f"💡 _Gráfico gerado em tempo real._"
        )

        await update.message.reply_photo(
            photo=buf,
            caption=caption_text,
            parse_mode="Markdown",
        )
        await status_msg.delete()

    except Exception:
        await status_msg.delete()
        await update.message.reply_text(
            f"❌ *Erro ao gerar o gráfico.*\n\n"
            f"Verifique se o par `{simbolo}` é válido na Binance.",
            parse_mode="Markdown",
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

    print("🤖 Bot multi-ativo iniciado com sucesso! Pressione Ctrl+C para parar.")
    application.run_polling()


if __name__ == "__main__":
    main()