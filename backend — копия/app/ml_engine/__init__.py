import joblib
import pandas as pd
import os

# Загружаем модель при импорте модуля
model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
if os.path.exists(model_path):
	model = joblib.load(model_path)
else:
	model = None
	print("Модель не найдена. Сначала запустите train.py для обучения модели.")

def predict_waste_rate(features: dict) -> float:
	"""
	features: словарь с ключами:
		sales_7d_avg, sales_14d_avg, temperature, humidity,
		is_weekend, is_holiday, category, days_to_expiry
	Возвращает предсказанную долю списания (0..1).
	"""
	if model is None:
		# Если модели нет, возвращаем случайное значение (для демо)
		return 0.5
	df = pd.DataFrame([features])
	# Убедимся, что порядок колонок совпадает с тренировочным
	# (здесь порядок: sales_7d_avg, sales_14d_avg, temperature, humidity, is_weekend, is_holiday, category, days_to_expiry)
	# Если порядок другой, модель может выдать некорректный результат
	# Можно сохранить список фичей при обучении
	return float(model.predict(df)[0])