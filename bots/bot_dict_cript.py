import os
import io
import time
import ccxt
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from telegram import Bot
import asyncio

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Inicializa a exchange via CCXT (ex: Binance)
exchange = ccxt.binance({
    'enableRateLimit': True,
})

async def enviar_grafico_telegram(simbolo):
    # 1. Puxa dados históricos (últimas 24 horas em velas de 1 hora)
    ohlcv = exchange.fetch_ohlcv(simbolo, timeframe='1h', limit=24)
    
    # 2. Transforma em DataFrame do Pandas
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Calcula uma Média Móvel Simples (SMA) de 6 períodos
    df['SMA6'] = df['close'].rolling(window=6).mean()

    # 3. Gera o gráfico com Matplotlib
    plt.figure(figsize=(10, 5))
    plt.plot(df['timestamp'], df['close'], label=f'Preço {simbolo}', color='blue', marker='o')
    plt.plot(df['timestamp'], df['SMA6'], label='SMA 6h', color='orange', linestyle='--')
    plt.title(f'Monitoramento Técnico - {simbolo}')
    plt.xlabel('Horário (UTC)')
    plt.ylabel('Preço (USDT)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Salva o gráfico em um buffer de memória (sem precisar salvar arquivo no disco)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # 4. Envia a imagem pelo Telegram
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=buf, caption=f"Relatório gráfico gerado para {simbolo}")

if __name__ == "__main__":
    # Exemplo de execução assíncrona para o par BTC/USDT
    asyncio.run(enviar_grafico_telegram("BTC/USDT"))