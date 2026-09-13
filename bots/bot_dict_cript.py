import time
import requests

# Lista de pares de criptomoedas que você deseja monitorar
# O formato segue o padrão da API da Binance (ex: BTCUSDT, ETHUSDT, SOLUSDT)
CRIPTOS_PARA_MONITORAR = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT"]

# Intervalo de tempo entre as verificações (em segundos)
INTERVALO_SEGUNDOS = 60

def obter_precos(simbolos):
    """Busca o preço atual de múltiplos símbolos na API pública da Binance."""
    url = "https://api.binance.com/api/v3/ticker/price"
    
    try:
        # A Binance permite buscar todos os preços de uma vez ou por símbolo
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        dados = resposta.json()
        
        # Filtra apenas os preços dos ativos que estão na nossa lista
        precos = {item['symbol']: float(item['price']) for item in dados if item['symbol'] in simbolos}
        return precos
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com a API: {e}")
        return None

def monitorar_mercado():
    print("Iniciando monitoramento de criptomoedas...\n")
    
    # Dicionário opcional para registrar o último preço e calcular variações simples
    precos_anteriores = {}

    while True:
        print(f"--- Verificação: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        precos_atuais = obter_precos(CRIPTOS_PARA_MONITORAR)
        
        if precos_atuais:
            for simbolo, preco in precos_atuais.items():
                # Exemplo simples de lógica por ativo
                variacao_texto = ""
                if simbolo in precos_anteriores:
                    anterior = precos_anteriores[simbolo]
                    dif = preco - anterior
                    if dif > 0:
                        variacao_texto = f"( subiram +{dif:.2f} )"
                    elif dif < 0:
                        variacao_texto = f"( caíram {dif:.2f} )"
                
                print(f"{simbolo}: ${preco:,.2f} {variacao_texto}")
                precos_anteriores[simbolo] = preco
        
        print(f"\nAguardando {INTERVALO_SEGUNDOS} segundos para a próxima verificação...\n")
        time.sleep(INTERVALO_SEGUNDOS)

if __name__ == "__main__":
    monitorar_mercado()