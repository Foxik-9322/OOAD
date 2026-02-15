from pydantic import BaseModel
from datetime import datetime

class RiskItem(BaseModel):
	product_name: str
	current_stock: int
	expiry_date: datetime
	waste_rate: float
	suggested_discount: float

class PurchaseRecommendation(BaseModel):
	product_name: str
	current_stock: int
	min_stock: int
	recommended_order: int

from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
	username: str
	password: str

class UserResponse(BaseModel):
	username: str
	role: str
	full_name: str