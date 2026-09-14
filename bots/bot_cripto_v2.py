import os
import io
import ccxt
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 1. Carrega variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Inicializa a exchange via CCXT (Binance)
exchange = ccxt.binance({
    'enableRateLimit': True,
})

# Lista padrão de criptomoedas suportadas/monitoradas
CRIPTOS_DISPONIVEIS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT", "XRP/USDT"]
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de boas-vindas personalizado com o nome do usuário"""
    # Pega os dados do usuário que enviou a mensagem
    usuario = update.effective_user
    nome = usuario.first_name if usuario.first_name else "Investidor"
    
    mensagem = (
        f"🤖 *Olá, {nome}! Eu sou seu Bot de Criptomoedas multi-ativo.*\n\n"
        "Comandos disponíveis:\n"
        "• /lista - Mostra os pares padrão monitorados\n"
        "• `/preco PAR` - Vê o preço atual (Ex: `/preco BTC/USDT`)\n"
        "• `/grafico PAR` - Gera o gráfico de 24h com SMA (Ex: `/grafico ETH/USDT`)"
    )
    await update.message.reply_text(mensagem, parse_mode="Markdown")
async def listar_criptos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista as criptomoedas configuradas"""
    texto = "📋 *Pares disponíveis para consulta:*\n" + "\n".join([f"• `{c}`" for c in CRIPTOS_DISPONIVEIS])
    await update.message.reply_text(texto, parse_mode="Markdown")

async def obter_preco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Consulta o preço atual de uma criptomoeda passada como argumento"""
    # Verifica se o usuário enviou um argumento (ex: /preco BTC/USDT)
    if not context.args:
        await update.message.reply_text("⚠️ Por favor, informe o par. Exemplo: `/preco BTC/USDT`", parse_mode="Markdown")
        return
    
    simbolo = context.args[0].upper()
    
    try:
        # Busca o ticker atual via CCXT
        ticker = exchange.fetch_ticker(simbolo)
        preco = ticker['last']
        variacao = ticker['percentage']
        
        emoji_var = "🟢" if variacao and variacao >= 0 else "🔴"
        
        resposta = (
            f"📊 *Ativo:* `{simbolo}`\n"
            f"💰 *Preço Atual:* `${preco:,.2f}`\n"
            f"📈 *Variação 24h:* {emoji_var} {variacao}%"
        )
        await update.message.reply_text(resposta, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao buscar o ativo `{simbolo}`. Verifique se o par está correto (ex: BTC/USDT).", parse_mode="Markdown")

async def gerar_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gera um gráfico técnico usando Pandas + Matplotlib e envia ao Telegram"""
    if not context.args:
        await update.message.reply_text("⚠️ Por favor, informe o par. Exemplo: `/grafico ETH/USDT`", parse_mode="Markdown")
        return
    
    simbolo = context.args[0].upper()
    
    await update.message.reply_text(f"⏳ Processando dados e gerando gráfico para `{simbolo}`...", parse_mode="Markdown")
    
    try:
        # 1. Puxa dados históricos (últimas 24 horas em velas de 1h)
        ohlcv = exchange.fetch_ohlcv(simbolo, timeframe='1h', limit=24)
        
        # 2. Manipula os dados com Pandas
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['SMA6'] = df['close'].rolling(window=6).mean() # Média móvel simples

        # 3. Desenha o gráfico com Matplotlib
        plt.figure(figsize=(10, 5))
        plt.plot(df['timestamp'], df['close'], label=f'Preço {simbolo}', color='#1f77b4', marker='o', linewidth=2)
        plt.plot(df['timestamp'], df['SMA6'], label='SMA 6h', color='#ff7f0e', linestyle='--', linewidth=2)
        
        plt.title(f'Análise Técnica 24h - {simbolo}', fontsize=14, fontweight='bold')
        plt.xlabel('Horário (UTC)', fontsize=10)
        plt.ylabel('Preço (USDT)', fontsize=10)
        plt.legend()
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Salva o gráfico em memória RAM (Buffer) sem criar lixo no disco
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close()

        # 4. Envia a foto gerada pelo Telegram
        await update.message.reply_photo(
            photo=buf, 
            caption=f"📈 Gráfico gerado com sucesso para *{simbolo}*.", 
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Não foi possível gerar o gráfico para `{simbolo}`. Erro: {str(e)}", parse_mode="Markdown")

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

    print("🤖 Bot multi-ativo iniciado com sucesso! Pressione Ctrl+C para parar.")
    # Inicia o loop de escuta do bot (Polling)
    application.run_polling()

if __name__ == "__main__":
    main()