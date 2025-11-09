import asyncio
from telegram import Bot

bot_token = "8557072251:AAF4yh98efgZrRLmSreSVNzIFzl3gfygbjQ"
chat_id = "-4880653038"

async def test_send():
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text="✅ Prueba de conexión desde el bot")

asyncio.run(test_send())