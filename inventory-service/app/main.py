from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from redis import Redis
import time
from .database import get_db, get_redis, init_db
from .models import InventoryDB, InventoryResponse, ReserveRequest, ReleaseRequest

app = FastAPI(title="Inventory Service", version="1.0.0")


@app.on_event("startup")
def startup_event():
    init_db()


class DistributedLock:
    def __init__(self, redis_client: Redis, lock_key: str, timeout: int = 10):
        self.redis = redis_client
        self.lock_key = lock_key
        self.timeout = timeout
        self.identifier = str(time.time())
    
    def acquire(self, retry_times: int = 3, retry_delay: float = 0.1) -> bool:
        for _ in range(retry_times):
            if self.redis.set(self.lock_key, self.identifier, nx=True, ex=self.timeout):
                return True
            time.sleep(retry_delay)
        return False
    
    def release(self):
        # Only release if we still own the lock
        if self.redis.get(self.lock_key) == self.identifier:
            self.redis.delete(self.lock_key)


class InventoryService:
    @staticmethod
    def get_inventory(db: Session, product_id: int) -> InventoryDB:
        inventory = db.query(InventoryDB).filter(InventoryDB.product_id == product_id).first()
        if not inventory:
            # Create default inventory if not exists
            inventory = InventoryDB(product_id=product_id, quantity=0)
            db.add(inventory)
            db.commit()
            db.refresh(inventory)
        return inventory
    
    @staticmethod
    def reserve_stock(db: Session, redis_client: Redis, product_id: int, quantity: int) -> InventoryDB:
        lock_key = f"inventory:lock:{product_id}"
        lock = DistributedLock(redis_client, lock_key)
        
        if not lock.acquire():
            raise HTTPException(status_code=503, detail="Could not acquire lock, please retry")
        
        try:
            inventory = InventoryService.get_inventory(db, product_id)
            
            if inventory.quantity < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock. Available: {inventory.quantity}, Requested: {quantity}"
                )
            
            inventory.quantity -= quantity
            db.commit()
            db.refresh(inventory)
            return inventory
        finally:
            lock.release()
    
    @staticmethod
    def release_stock(db: Session, redis_client: Redis, product_id: int, quantity: int) -> InventoryDB:
        lock_key = f"inventory:lock:{product_id}"
        lock = DistributedLock(redis_client, lock_key)
        
        if not lock.acquire():
            raise HTTPException(status_code=503, detail="Could not acquire lock, please retry")
        
        try:
            inventory = InventoryService.get_inventory(db, product_id)
            inventory.quantity += quantity
            db.commit()
            db.refresh(inventory)
            return inventory
        finally:
            lock.release()


@app.get("/inventory/{product_id}", response_model=InventoryResponse)
def get_inventory(product_id: int, db: Session = Depends(get_db)):
    return InventoryService.get_inventory(db, product_id)


@app.post("/reserve", response_model=InventoryResponse)
def reserve_inventory(request: ReserveRequest, db: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    return InventoryService.reserve_stock(db, redis_client, request.product_id, request.quantity)


@app.post("/release", response_model=InventoryResponse)
def release_inventory(request: ReleaseRequest, db: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    return InventoryService.release_stock(db, redis_client, request.product_id, request.quantity)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "inventory-service"}