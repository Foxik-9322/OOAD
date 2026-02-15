from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import SessionLocal

router = APIRouter()

def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

# ----- Products -----
@router.get("/products", response_model=List[schemas.Product])
def get_products(db: Session = Depends(get_db)):
	return db.query(models.Product).all()

@router.post("/products", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
	db_product = models.Product(**product.dict())
	db.add(db_product)
	db.commit()
	db.refresh(db_product)
	return db_product

@router.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
	product = db.query(models.Product).filter(models.Product.id == product_id).first()
	if not product:
		raise HTTPException(status_code=404, detail="Product not found")
	return product

@router.put("/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product_update: schemas.ProductCreate, db: Session = Depends(get_db)):
	product = db.query(models.Product).filter(models.Product.id == product_id).first()
	if not product:
		raise HTTPException(status_code=404, detail="Product not found")
	for key, value in product_update.dict().items():
		setattr(product, key, value)
	db.commit()
	db.refresh(product)
	return product

@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
	product = db.query(models.Product).filter(models.Product.id == product_id).first()
	if not product:
		raise HTTPException(status_code=404, detail="Product not found")
	db.delete(product)
	db.commit()
	return {"ok": True}

# ----- Inventory -----
@router.get("/inventory", response_model=List[schemas.Inventory])
def get_inventory(db: Session = Depends(get_db)):
	return db.query(models.Inventory).all()

@router.post("/inventory", response_model=schemas.Inventory)
def create_inventory(item: schemas.InventoryCreate, db: Session = Depends(get_db)):
	db_item = models.Inventory(**item.dict())
	db.add(db_item)
	db.commit()
	db.refresh(db_item)
	return db_item

@router.put("/inventory/{item_id}", response_model=schemas.Inventory)
def update_inventory(item_id: int, item_update: schemas.InventoryCreate, db: Session = Depends(get_db)):
	item = db.query(models.Inventory).filter(models.Inventory.id == item_id).first()
	if not item:
		raise HTTPException(status_code=404, detail="Inventory item not found")
	for key, value in item_update.dict().items():
		setattr(item, key, value)
	db.commit()
	db.refresh(item)
	return item

@router.delete("/inventory/{item_id}")
def delete_inventory(item_id: int, db: Session = Depends(get_db)):
	item = db.query(models.Inventory).filter(models.Inventory.id == item_id).first()
	if not item:
		raise HTTPException(status_code=404, detail="Inventory item not found")
	db.delete(item)
	db.commit()
	return {"ok": True}

# ----- SalesHistory -----
@router.get("/sales", response_model=List[schemas.SalesHistory])
def get_sales(db: Session = Depends(get_db)):
	return db.query(models.SalesHistory).all()

@router.post("/sales", response_model=schemas.SalesHistory)
def create_sale(sale: schemas.SalesHistoryCreate, db: Session = Depends(get_db)):
	db_sale = models.SalesHistory(**sale.dict())
	db.add(db_sale)
	db.commit()
	db.refresh(db_sale)
	return db_sale

# ----- Применить скидку (для акции) -----
@router.post("/apply_discount/{product_id}")
def apply_discount(product_id: int, discount: float):
	# Здесь может быть интеграция с цифровыми ценниками
	# Пока просто логируем
	return {"message": f"Discount {discount*100}% applied to product {product_id}"}