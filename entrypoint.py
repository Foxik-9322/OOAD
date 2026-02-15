import multiprocessing
import uvicorn
import asyncio
import os
import sys

# Добавляем путь к папке backend/app, чтобы импорты внутри main.py не сломались
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.app.main import app
from backend.app.utils.telegram_bot import bot, dp

def run_api():
	print("--- [WEB] Запуск FastAPI сервера ---")
	# Render сам назначит порт через переменную PORT, локально будет 8000
	port = int(os.environ.get("PORT", 8000))
	uvicorn.run(app, host="0.0.0.0", port=port)

async def start_bot():
	print("--- [BOT] Запуск Telegram бота ---")
	try:
		await dp.start_polling(bot)
	finally:
		await bot.session.close()

def run_bot_process():
	asyncio.run(start_bot())

if __name__ == "__main__":
	# 1. Запуск сайта
	p1 = multiprocessing.Process(target=run_api)
	# 2. Запуск бота
	p2 = multiprocessing.Process(target=run_bot_process)

	p1.start()
	p2.start()

	p1.join()
	p2.join()