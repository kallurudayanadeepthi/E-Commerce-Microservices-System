from sqlalchemy import Column, Integer, String, Float
from .database import Base
from pydantic import BaseModel


# SQLAlchemy Model
class ProductDB(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)


# Pydantic Models
class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    
    class Config:
        from_attributes = True