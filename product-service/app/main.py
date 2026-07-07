from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .database import get_db, init_db
from .models import ProductDB, ProductCreate, ProductResponse

app = FastAPI(title="Product Service", version="1.0.0")


@app.on_event("startup")
def startup_event():
    init_db()


class ProductService:
    @staticmethod
    def get_all(db: Session) -> List[ProductDB]:
        return db.query(ProductDB).all()
    
    @staticmethod
    def get_by_id(db: Session, product_id: int) -> ProductDB:
        product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    
    @staticmethod
    def create(db: Session, product: ProductCreate) -> ProductDB:
        db_product = ProductDB(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    
    @staticmethod
    def update(db: Session, product_id: int, product: ProductCreate) -> ProductDB:
        db_product = ProductService.get_by_id(db, product_id)
        for key, value in product.model_dump().items():
            setattr(db_product, key, value)
        db.commit()
        db.refresh(db_product)
        return db_product
    
    @staticmethod
    def delete(db: Session, product_id: int) -> bool:
        db_product = ProductService.get_by_id(db, product_id)
        db.delete(db_product)
        db.commit()
        return True


@app.get("/products", response_model=List[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return ProductService.get_all(db)


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return ProductService.get_by_id(db, product_id)


@app.post("/products", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    return ProductService.create(db, product)


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    return ProductService.update(db, product_id, product)


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    ProductService.delete(db, product_id)
    return {"message": "Product deleted successfully"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "product-service"}