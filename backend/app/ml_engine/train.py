#!/usr/bin/env python
# Скрипт для обучения модели XGBoost на синтетических данных
# Запустить один раз: python -m app.ml_engine.train

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import joblib
import os

# Параметры генерации
np.random.seed(42)
n_samples = 10000

# Признаки
data = {
	'sales_7d_avg': np.random.uniform(10, 200, n_samples),
	'sales_14d_avg': np.random.uniform(10, 200, n_samples),
	'temperature': np.random.uniform(-5, 35, n_samples),
	'humidity': np.random.uniform(30, 90, n_samples),
	'is_weekend': np.random.choice([0, 1], n_samples),
	'is_holiday': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
	'category': np.random.choice([0, 1, 2], n_samples),
	'days_to_expiry': np.random.randint(1, 30, n_samples)
}

df = pd.DataFrame(data)

# Целевая переменная: процент списания (0..1). Сделаем зависимость от признаков
df['waste_rate'] = (
	0.3 * (1 / (df['days_to_expiry'] + 1)) +
	0.2 * (df['temperature'] > 25) * 0.2 +
	0.1 * (df['humidity'] > 70) * 0.1 +
	0.1 * (df['is_weekend'] == 1) * 0.05 +
	0.1 * (df['is_holiday'] == 1) * 0.1 +
	0.2 * (df['category'] == 0) * 0.15 +
	np.random.normal(0, 0.05, n_samples)
).clip(0, 1)

# Разделение
X = df.drop('waste_rate', axis=1)
y = df['waste_rate']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Модель
model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

# Оценка
train_score = model.score(X_train, y_train)
test_score = model.score(X_test, y_test)
print(f"Train R^2: {train_score:.4f}")
print(f"Test R^2: {test_score:.4f}")

# Сохраняем модель и список фичей (порядок)
model_dir = os.path.dirname(__file__)
joblib.dump(model, os.path.join(model_dir, 'model.pkl'))
print(f"Модель сохранена в {os.path.join(model_dir, 'model.pkl')}")