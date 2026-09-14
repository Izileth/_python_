import ccxt
import time

# Inicializa a exchange (Binance)
exchange = ccxt.binance({
    'enableRateLimit': True, # Respeita o limite de requisições da API
})

symbol = 'BTC/USDT'

def monitorar_preco():
    print(f"--- Iniciando monitoramento de {symbol} ---")
    while True:
        try:
            ticker = exchange.fetch_ticker(symbol)
            preco_atual = ticker['last']
            variacao_24h = ticker['percentage']
            
            print(f"Preço Atual: ${preco_atual:,.2f} | Variação 24h: {variacao_24h:.2f}%")
            
            # Lógica simples de alerta (Exemplo)
            if variacao_24h > 5:
                print("⚠️ Alerta: Alta significativa em 24h!")
                
            time.sleep(5) # Espera 5 segundos antes de checar novamente
            
        except Exception as e:
            print(f"Erro ao buscar dados: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitorar_preco()