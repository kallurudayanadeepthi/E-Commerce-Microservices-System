from locust import HttpUser, task, between
import random


class EcommerceUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8002"
    
    def on_start(self):
        """Setup - create test products and inventory"""
        # This runs once per user when they start
        pass
    
    @task(3)
    def create_order(self):
        """Simulate creating an order"""
        product_id = random.randint(1, 10)
        payload = {
            "product_id": product_id,
            "quantity": random.randint(1, 3),
            "customer_email": f"user{random.randint(1, 1000)}@example.com"
        }
        with self.client.post("/orders", json=payload, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 400:
                # Insufficient stock is expected, mark as success
                response.success()
            else:
                response.failure(f"Got unexpected status code: {response.status_code}")
    
    @task(1)
    def get_order(self):
        """Simulate checking order status"""
        order_id = random.randint(1, 100)
        with self.client.get(f"/orders/{order_id}", catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Got unexpected status code: {response.status_code}")


class ProductUser(HttpUser):
    wait_time = between(1, 2)
    host = "http://localhost:8001"
    
    @task(5)
    def list_products(self):
        """Simulate browsing products"""
        self.client.get("/products")
    
    @task(2)
    def get_product(self):
        """Simulate viewing product details"""
        product_id = random.randint(1, 10)
        self.client.get(f"/products/{product_id}")


class InventoryUser(HttpUser):
    wait_time = between(2, 4)
    host = "http://localhost:8003"
    
    @task
    def check_inventory(self):
        """Simulate checking inventory"""
        product_id = random.randint(1, 10)
        self.client.get(f"/inventory/{product_id}")