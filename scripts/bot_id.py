import asyncio
from telegram import Bot

TELEGRAM_TOKEN = 'SEU_NOVO_TOKEN_AQUI'  # Substitua pelo seu token real do bot do Telegram

async def pegar_chat_id():
    bot = Bot(token=TELEGRAM_TOKEN)
    updates = await bot.get_updates()
    
    if not updates:
        print("⚠️ Nenhuma mensagem encontrada! Abra o bot no Telegram e mande um 'Oi' agora, depois rode o script novamente.")
        return

    for update in updates:
        if update.message:
            print(f"✅ Seu Nome: {update.message.from_user.first_name}")
            print(f"👉 Seu CHAT_ID correto é: {update.message.chat_id}")

if __name__ == "__main__":
    asyncio.run(pegar_chat_id())