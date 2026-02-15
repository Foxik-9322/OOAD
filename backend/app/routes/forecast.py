from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List
from .. import models, schemas
from ..database import SessionLocal
import random

router = APIRouter()

def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

@router.get("/risk_radar", response_model=List[schemas.RiskItem])
def risk_radar(db: Session = Depends(get_db)):
	now = datetime.utcnow()
	two_days_later = now + timedelta(days=2)
	
	near_expiry = db.query(models.Inventory).join(models.Product).filter(
		models.Inventory.expiry_date <= two_days_later
	).all()

	result = []
	for inv in near_expiry:
		# Имитация ML-модели (в реальности тут predict_waste_rate)
		waste_rate = random.uniform(0.7, 0.99)
		discount = 0.5 if waste_rate > 0.85 else 0.3
		
		result.append(schemas.RiskItem(
			product_name=inv.product.name,
			current_stock=inv.current_stock,
			expiry_date=inv.expiry_date,
			waste_rate=round(waste_rate, 2),
			suggested_discount=discount
		))
	return result

@router.get("/eco")
def eco_metrics(db: Session = Depends(get_db)):
	risk_items = risk_radar(db)
	prevented_waste_kg = sum(item.current_stock * 0.5 for item in risk_items)
	return {
		"co2_saved": round(prevented_waste_kg * 2.5, 1),
		"water_saved": round(prevented_waste_kg * 50, 0),
		"waste_prevented": round(prevented_waste_kg, 1)
	}

@router.get("/purchase_list", response_model=List[schemas.PurchaseRecommendation])
def purchase_list(db: Session = Depends(get_db)):
	products = db.query(models.Product).all()
	result = []
	for prod in products:
		total_stock = db.query(func.sum(models.Inventory.current_stock)).filter(
			models.Inventory.product_id == prod.id
		).scalar() or 0
		
		if total_stock < prod.min_stock_level:
			result.append(schemas.PurchaseRecommendation(
				product_name=prod.name,
				current_stock=total_stock,
				min_stock=prod.min_stock_level,
				recommended_order=prod.min_stock_level - total_stock
			))
	return result

@router.get("/chart")
def forecast_chart():
	dates = [(datetime.utcnow() + timedelta(days=i)).strftime("%d.%m") for i in range(7)]
	# Корреляция погоды (дождь) и спроса
	return {
		"dates": dates,
		"waste_risk": [12, 15, 45, 60, 20, 10, 5],
		"rain_probability": [10, 20, 80, 90, 30, 10, 0]
	}