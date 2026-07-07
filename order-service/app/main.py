from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
import os
from .database import get_db, init_db
from .models import OrderDB, OrderCreate, OrderResponse

app = FastAPI(title="Order Service", version="1.0.0")

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8003")


@app.on_event("startup")
def startup_event():
    init_db()


class ExternalServiceClient:
    @staticmethod
    async def get_product(product_id: int):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                raise HTTPException(status_code=404, detail="Product not found")
    
    @staticmethod
    async def reserve_inventory(product_id: int, quantity: int):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{INVENTORY_SERVICE_URL}/reserve",
                    json={"product_id": product_id, "quantity": quantity}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(status_code=400, detail=f"Inventory reservation failed: {str(e)}")


class OrderService:
    @staticmethod
    def get_by_id(db: Session, order_id: int) -> OrderDB:
        order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    
    @staticmethod
    async def create(db: Session, order: OrderCreate) -> OrderDB:
        # Validate product exists
        product = await ExternalServiceClient.get_product(order.product_id)
        
        # Reserve inventory
        await ExternalServiceClient.reserve_inventory(order.product_id, order.quantity)
        
        # Calculate total
        total_price = product["price"] * order.quantity
        
        # Create order
        db_order = OrderDB(
            product_id=order.product_id,
            quantity=order.quantity,
            customer_email=order.customer_email,
            total_price=total_price,
            status="confirmed"
        )
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        return db_order


@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    return await OrderService.create(db, order)


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    return OrderService.get_by_id(db, order_id)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "order-service"}