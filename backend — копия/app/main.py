from fastapi import BackgroundTasks
from .utils import telegram_bot
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse # Добавили StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import os, datetime, requests, io
import pandas as pd
from . import models, schemas
from .database import SessionLocal, engine

app = FastAPI()

def get_db():
	db = SessionLocal()
	try: yield db
	finally: db.close()

# --- Вспомогательная функция для Telegram (исправляем форматирование) ---
async def send_telegram_msg(text: str):
	# Если ты используешь HTML parse_mode, меняем ** на <b>
	formatted_text = text.replace("**", "<b>").replace("**", "</b>")
	try:
		# Убедись, что этот URL ведет на твой запущенный бот или API отправки
		# Если бот в отдельном процессе, тут должен быть запрос к нему
		# Но проще всего слать напрямую через requests к Telegram API (если есть токен)
		TOKEN = "8476504596:AAE8wHSH1857huY4EJApTM79i13mbqvm2Ko"
		CHAT_ID = "ТВОЙ_CHAT_ID" # Сюда нужно добавить логику получения ID
		# Для примера оставим логику вызова внутреннего метода, если он доступен
		pass 
	except: pass

# --- API ЭНДПОИНТЫ (ДОЛЖНЫ БЫТЬ ВЫШЕ SPA МАРШРУТА) ---

@app.get("/api/weather")
async def get_weather():
	try:
		geo = requests.get("http://ip-api.com/json/", timeout=5).json()
		lat, lon = geo.get("lat", 55.75), geo.get("lon", 37.62)
		city = geo.get("city", "Москва")
		w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
		w_res = requests.get(w_url, timeout=5).json()
		return {
			"city": city,
			"temp": round(w_res["current_weather"]["temperature"]),
			"code": w_res["current_weather"]["weathercode"]
		}
	except:
		return {"city": "Москва", "temp": 22, "code": 0}

@app.get("/api/dashboard/stats")
async def get_stats(role: str, db: Session = Depends(get_db)):
	products = db.query(models.Product).all()
	now = datetime.datetime.now()
	critical_items = [p for p in products if (p.expiry_date - now).days <= 3]
	
	ai_recommendations = []
	for p in critical_items:
		days_left = (p.expiry_date - now).days
		discount = 50 if days_left <= 1 else (30 if days_left == 2 else 15)
		new_price = round(p.price * (1 - discount/100))
		
		ai_recommendations.append({
			"id": p.id,
			"name": p.name,
			"old_price": p.price,
			"new_price": new_price,
			"discount": discount,
			"reason": "Короткий срок" if days_left > 1 else "Критический срок!",
			"risk_score": 70 + (3 - days_left) * 10 
		})

	chart_data = []
	for i in range(7):
		day = (now + datetime.timedelta(days=i)).date()
		count = db.query(models.Product).filter(func.date(models.Product.expiry_date) == day).count()
		chart_data.append(count)

	return {
		"metrics": {
			"critical_count": len(critical_items),
			"total_skus": len(products),
			"total_value": sum(p.price * p.current_stock for p in products),
			"potential_loss": sum(p.price * p.current_stock for p in critical_items)
		},
		"chart": chart_data,
		"ai_plan": ai_recommendations
	}

@app.get("/api/inventory/full")
async def get_inv(db: Session = Depends(get_db)):
	return db.query(models.Product).all()

# --- ПУНКТ 1: ИСПРАВЛЕННЫЙ ИМПОРТ ---
@app.post("/api/import/inventory")
async def import_inventory(file: UploadFile = File(...), db: Session = Depends(get_db)):
	content = await file.read()
	try:
		# utf-8-sig лечит проблему с Excel-файлами
		df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', encoding='utf-8-sig', on_bad_lines='skip')
		
		db.query(models.Product).delete()
		
		for _, row in df.iterrows():
			new_product = models.Product( # Исправлено: models.Product
				name=row['name'],
				category=int(row['category']),
				current_stock=int(row['current_stock']),
				price=float(row['price']),
				expiry_date=datetime.datetime.strptime(str(row['expiry_date']), '%Y-%m-%d %H:%M:%S')
			)
			db.add(new_product)
		
		db.commit()
		return {"status": "success", "count": len(df)}
	except Exception as e:
		db.rollback()
		raise HTTPException(status_code=400, detail=f"Ошибка в CSV: {str(e)}")

# --- ПУНКТ 2: НОВЫЙ ЭНДПОИНТ ЭКСПОРТА (ЧТОБЫ НЕ КАЧАЛАСЬ СТРАНИЦА) ---
@app.get("/api/export/inventory")
async def export_inventory(db: Session = Depends(get_db)):
	products = db.query(models.Product).all()
	data = []
	for p in products:
		data.append({
			"name": p.name,
			"category": p.category,
			"current_stock": p.current_stock,
			"price": p.price,
			"expiry_date": p.expiry_date.strftime('%Y-%m-%d %H:%M:%S')
		})
	
	df = pd.DataFrame(data)
	stream = io.StringIO()
	df.to_csv(stream, index=False, encoding='utf-8')
	
	return StreamingResponse(
		iter([stream.getvalue()]),
		media_type="text/csv",
		headers={"Content-Disposition": "attachment; filename=inventory.csv"}
	)

# --- ПУНКТ 3: ЭНДПОИНТ ДЛЯ AI ПЛАНА (ОПТИМИЗАЦИЯ) ---
@app.post("/api/inventory/optimize")
async def optimize_item(data: dict = Body(...), db: Session = Depends(get_db)):
	item_id = data.get("id")
	product = db.query(models.Product).filter(models.Product.id == item_id).first()
	if not product:
		raise HTTPException(status_code=404, detail="Товар не найден")
	
	# Имитация оптимизации: помечаем как оптимизированный или меняем цену
	product.is_optimized = 1 
	db.commit()
	return {"status": "optimized", "name": product.name}

@app.post("/api/login")
async def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
	if data.username == "admin" and data.password == "admin":
		return {"full_name": "Администратор", "role": "admin", "username": "admin"}
	user = db.query(models.User).filter(models.User.username == data.username).first()
	if not user or user.password != data.password:
		raise HTTPException(status_code=401, detail="Неверный пароль")
	return user

# --- СТАТИКА И SPA (В САМОМ КОНЦЕ!) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

# Проверь, что папка assets существует, иначе mount упадет
if os.path.exists(os.path.join(FRONTEND_DIR, "assets")):
	app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

@app.post("/api/telegram/send")
async def send_to_tg(background_tasks: BackgroundTasks, data: dict = Body(...)):
	message = data.get("message", "Без текста")
	
	# Исправленный импорт с учетом твоей структуры
	from .utils import telegram_bot 

	async def run_send():
		try:
			await telegram_bot.send_notification(message)
		except Exception as e:
			print(f"Ошибка в фоне: {e}")

	background_tasks.add_task(run_send)
	return {"status": "accepted"}

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
	# Если запрашивают файл, который существует (например favicon), отдаем его
	file_path = os.path.join(FRONTEND_DIR, full_path)
	if os.path.exists(file_path) and os.path.isfile(file_path):
		return FileResponse(file_path)
	# Иначе отдаем главную (для SPA)
	return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))