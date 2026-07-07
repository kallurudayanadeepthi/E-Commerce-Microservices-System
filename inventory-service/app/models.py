from sqlalchemy import Column, Integer
from .database import Base
from pydantic import BaseModel


# SQLAlchemy Model
class InventoryDB(Base):
    __tablename__ = "inventory"
    
    product_id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False, default=0)


# Pydantic Models
class InventoryResponse(BaseModel):
    product_id: int
    quantity: int
    
    class Config:
        from_attributes = True


class ReserveRequest(BaseModel):
    product_id: int
    quantity: int


class ReleaseRequest(BaseModel):
    product_id: int
    quantity: int