import sqlite3
from datetime import datetime, timedelta
import random

def init_db():
	conn = sqlite3.connect('warehouse.db')
	cursor = conn.cursor()

	# Пересоздаем таблицу
	cursor.execute("DROP TABLE IF EXISTS products")
	cursor.execute("CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category INTEGER, current_stock INTEGER, price REAL, expiry_date DATETIME, is_optimized INTEGER DEFAULT 0)")

	# Списки для генерации
	categories = {
		0: ["Сэндвич", "Боул", "Салат", "Паста", "Омлет", "Ролл", "Суп", "Буррито"],
		1: ["Кофе", "Морс", "Лимонад", "Смузи", "Сок", "Чай", "Вода", "Энергетик"],
		2: ["Йогурт", "Кефир", "Творожок", "Сырок", "Молоко", "Сливки", "Ряженка"],
		3: ["Чизкейк", "Круассан", "Маффин", "Эклер", "Пончик", "Торт"],
		4: ["Чипсы", "Орехи", "Сухарики", "Батончик", "Печенье"]
	}
	
	fillings = ["курица", "лосось", "тунец", "ветчина", "сыр", "ягоды", "шоколад", "овощи", "грибы", "креветки"]
	adjectives = ["Классический", "Домашний", "Острый", "Греческий", "Цезарь", "Фитнес", "Премиум", "Лайт"]

	now = datetime.now()
	all_products = []

	# Генерируем ровно 100 уникальных позиций
	for i in range(100):
		cat_id = random.choice(list(categories.keys()))
		base_name = random.choice(categories[cat_id])
		adj = random.choice(adjectives)
		fill = random.choice(fillings)
		
		# Собираем уникальное название, например: "Классический Сэндвич с курицей"
		full_name = f"{adj} {base_name} ({fill})"
		
		# Чтобы избежать дублей в названиях (хотя это не критично)
		if full_name in [p[0] for p in all_products]:
			full_name += f" #{i}"

		# Генерация сроков годности:
		# 10% товаров уже просрочены (для теста рисков)
		# 20% критические (1-2 дня)
		# Остальные в норме (3-10 дней)
		rand_val = random.random()
		if rand_val < 0.1:
			days_offset = random.randint(-2, -1)
		elif rand_val < 0.3:
			days_offset = random.randint(1, 2)
		else:
			days_offset = random.randint(3, 10)

		expiry = now + timedelta(days=days_offset)
		stock = random.randint(5, 80)
		price = random.randrange(80, 850, 10) # Цена от 80 до 850 с шагом 10

		all_products.append((full_name, cat_id, stock, price, expiry.strftime('%Y-%m-%d %H:%M:%S'), 0))

	cursor.executemany("INSERT INTO products (name, category, current_stock, price, expiry_date, is_optimized) VALUES (?, ?, ?, ?, ?, ?)", all_products)
	
	conn.commit()
	conn.close()
	print("✅ База данных успешно наполнена: 100 уникальных товаров создано!")

if __name__ == "__main__":
	init_db()