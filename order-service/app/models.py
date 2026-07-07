from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .database import Base
from pydantic import BaseModel, EmailStr


# SQLAlchemy Model
class OrderDB(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    customer_email = Column(String, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic Models
class OrderCreate(BaseModel):
    product_id: int
    quantity: int
    customer_email: EmailStr


class OrderResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    customer_email: str
    total_price: float
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True