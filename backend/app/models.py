from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
	__tablename__ = "users"
	id = Column(Integer, primary_key=True, index=True)
	username = Column(String, unique=True)
	password = Column(String)
	role = Column(String) # admin / manager
	full_name = Column(String)

class Product(Base):
	__tablename__ = "products"
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String)
	category = Column(Integer) # 0, 1, 2 как в твоем XGBoost
	current_stock = Column(Integer)
	price = Column(Float)
	expiry_date = Column(DateTime)
	# Отношение для аналитики
	sales_history = relationship("SalesHistory", back_populates="product")

class SalesHistory(Base):
	__tablename__ = "sales_history"
	id = Column(Integer, primary_key=True, index=True)
	product_id = Column(Integer, ForeignKey("products.id"))
	sale_date = Column(DateTime, default=datetime.datetime.utcnow)
	quantity = Column(Integer)
	product = relationship("Product", back_populates="sales_history")