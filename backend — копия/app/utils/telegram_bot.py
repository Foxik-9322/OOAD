import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import asyncio
import logging
import os
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Настройки
API_TOKEN = '8476504596:AAE8wHSH1857huY4EJApTM79i13mbqvm2Ko'
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "neuro_password_2026"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FILE = os.path.join(BASE_DIR, "authorized_users.txt")

# Инициализация
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- РАБОТА С ПАМЯТЬЮ (ФАЙЛ) ---

def load_authorized_users():
	if os.path.exists(DB_FILE):
		with open(DB_FILE, "r") as f:
			return set(int(line.strip()) for line in f if line.strip())
	return set()

def save_user_id(user_id):
	authorized_users.add(user_id)
	with open(DB_FILE, "a") as f:
		f.write(f"{user_id}\n")

authorized_users = load_authorized_users()

class AuthStates(StatesGroup):
	waiting_for_login = State()
	waiting_for_password = State()

# --- ЛОГИКА БОТА (ПОРЯДОК ВАЖЕН!) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
	if message.from_user.id in authorized_users:
		await message.answer("✅ Вы уже авторизованы в системе NeuroStock.")
	else:
		# Принудительно очищаем состояние, если пользователь застрял
		await state.clear()
		await message.answer("🔐 <b>Вход в систему</b>\nВведите ваш логин:", parse_mode="HTML")
		await state.set_state(AuthStates.waiting_for_login)

@dp.message(AuthStates.waiting_for_login)
async def process_login(message: types.Message, state: FSMContext):
	if message.text == ADMIN_LOGIN:
		await state.update_data(login=message.text)
		await message.answer("Отлично. Теперь введите пароль:")
		await state.set_state(AuthStates.waiting_for_password)
	else:
		await message.answer("❌ Неверный логин. Попробуйте еще раз /start")
		await state.clear()

@dp.message(AuthStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
	if message.text == ADMIN_PASSWORD:
		if message.from_user.id not in authorized_users:
			save_user_id(message.from_user.id)
		
		await message.answer("🎉 <b>Доступ разрешен!</b>\nТеперь вы будете получать уведомления.", parse_mode="HTML")
		await state.clear()
	else:
		await message.answer("❌ Неверный пароль. /start")
		await state.clear()

# Этот хендлер должен быть САМЫМ ПОСЛЕДНИМ
@dp.message()
async def echo_handler(message: types.Message):
	await message.answer("Я получил ваше сообщение, но не знаю, что с ним делать. Используйте /start")

# --- ФУНКЦИИ УВЕДОМЛЕНИЙ ---

async def send_notification(text: str):
	# Используем контекстный менеджер, чтобы сессия бота всегда была активна при отправке
	async with bot.context(): 
		formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
		current_users = load_authorized_users()
		
		for user_id in current_users:
			try:
				await bot.send_message(user_id, formatted_text, parse_mode="HTML")
			except Exception as e:
				print(f"Ошибка отправки пользователю {user_id}: {e}")

async def main():
	logging.info("Бот запущен...")
	await dp.start_polling(bot)

if __name__ == '__main__':
	try:
		asyncio.run(main())
	except (KeyboardInterrupt, SystemExit):
		logging.info("Бот остановлен")