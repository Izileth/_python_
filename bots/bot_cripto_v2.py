import io
import os
import ccxt
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# 1. Carrega variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Inicializa a exchange via CCXT (Binance)
exchange = ccxt.binance(
    {
        "enableRateLimit": True,
    }
)

# Lista padrão de criptomoedas suportadas/monitoradas
CRIPTOS_DISPONIVEIS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "ADA/USDT",
    "XRP/USDT",
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de boas-vindas personalizado com o nome do usuário"""
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
    """Lista as criptomoedas configuradas"""
    texto = "📋 *Pares disponíveis para consulta:*\n" + "\n".join(
        [f"• `{c}`" for c in CRIPTOS_DISPONIVEIS]
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def obter_preco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Consulta o preço atual de uma criptomoeda passada como argumento"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Por favor, informe o par. Exemplo: `/preco BTC/USDT`",
            parse_mode="Markdown",
        )
        return

    simbolo = context.args[0].upper()

    try:
        ticker = exchange.fetch_ticker(simbolo)
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
            f"❌ Erro ao buscar o ativo `{simbolo}`. Verifique se o par está correto (ex: BTC/USDT).",
            parse_mode="Markdown",
        )


async def gerar_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gera um gráfico estilo Candlestick Dark usando exclusivamente Matplotlib"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Por favor, informe o par. Exemplo: `/grafico ETH/USDT`",
            parse_mode="Markdown",
        )
        return

    simbolo = context.args[0].upper()

    await update.message.reply_text(
        f"⏳ Processando dados e gerando gráfico para `{simbolo}`...",
        parse_mode="Markdown",
    )

    try:
        # 1. Puxa histórico de velas (ex: 80 velas de 1h para dar volume similar à foto)
        ohlcv = exchange.fetch_ohlcv(simbolo, timeframe="1h", limit=80)

        # 2. Converte os dados recebidos em um DataFrame
        df = pd.DataFrame(
            ohlcv,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )

        # 3. Separa as velas de alta (close >= open) e velas de baixa (close < open)
        up = df[df["close"] >= df["open"]]
        down = df[df["close"] < df["open"]]

        # 4. Configura a janela com tema escuro (#0e0e0e)
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#0e0e0e")
        ax.set_facecolor("#0e0e0e")

        width = 0.6  # Largura do corpo do candle

        # Desenha velas de Alta (Brancas)
        ax.vlines(
            up.index,
            up["low"],
            up["high"],
            color="#ffffff",
            linewidth=1,
            zorder=1,
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

        # Desenha velas de Baixa (Vermelho vivo)
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

        # 5. Formatação do Eixo e Grade conforme a imagem
        ax.yaxis.tick_right()  # Move escala de preços para a direita
        ax.yaxis.set_label_position("right")
        ax.tick_params(colors="#888888", labelsize=9)

        # Linhas pontilhadas bem suaves para a grade
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.15, color="#ffffff")

        # Oculta bordas da moldura do gráfico
        for spine in ["top", "left", "bottom", "right"]:
            ax.spines[spine].set_visible(False)

        # Oculta marcadores do eixo X para manter visual limpo
        ax.set_xticks([])
        ax.set_xlim(-1, len(df))

        plt.tight_layout()

        # 6. Salva a imagem gerada no Buffer de Memória RAM
        buf = io.BytesIO()
        plt.savefig(
            buf,
            format="png",
            dpi=120,
            bbox_inches="tight",
            facecolor=fig.get_facecolor(),
        )
        buf.seek(0)
        plt.close(fig)

        # 7. Envia a imagem gerada de volta ao usuário do Telegram
        await update.message.reply_photo(
            photo=buf,
            caption=f"📈 Gráfico *{simbolo}* gerado com sucesso.",
            parse_mode="Markdown",
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Não foi possível gerar o gráfico para `{simbolo}`. Erro: {str(e)}",
            parse_mode="Markdown",
        )


def main():
    """Inicializa o Bot"""
    if not TELEGRAM_TOKEN:
        print("Erro: TELEGRAM_TOKEN não configurado no arquivo .env")
        return

    # Constrói a aplicação do bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Registra os manipuladores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("lista", listar_criptos))
    application.add_handler(CommandHandler("preco", obter_preco))
    application.add_handler(CommandHandler("grafico", gerar_grafico))

    print(
        "🤖 Bot multi-ativo iniciado com sucesso! Pressione Ctrl+C para parar."
    )
    # Inicia o loop de escuta do bot (Polling)
    application.run_polling()


if __name__ == "__main__":
    main()