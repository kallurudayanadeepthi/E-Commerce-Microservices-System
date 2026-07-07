import asyncio
import httpx
import time


async def create_order(client, product_id, quantity, user_id):
    """Attempt to create an order"""
    try:
        response = await client.post(
            "http://localhost:8002/orders",
            json={
                "product_id": product_id,
                "quantity": quantity,
                "customer_email": f"user{user_id}@example.com"
            }
        )
        return {
            "user_id": user_id,
            "status_code": response.status_code,
            "success": response.status_code == 201,
            "message": response.json().get("detail", "Success") if response.status_code != 201 else "Order created"
        }
    except Exception as e:
        return {
            "user_id": user_id,
            "status_code": 0,
            "success": False,
            "message": str(e)
        }


async def test_concurrent_orders():
    """
    Test scenario: 100 users try to order the last item simultaneously
    Expected: Only 1 should succeed, 99 should fail with insufficient stock
    """
    
    print("🧪 Starting Concurrency Test")
    print("=" * 60)
    
    # Setup: Create a product with only 1 item in stock
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create product
        print("📦 Setting up test product...")
        product_response = await client.post(
            "http://localhost:8001/products",
            json={"name": "Limited Edition Item", "price": 99.99, "description": "Only 1 available"}
        )
        product_id = product_response.json()["id"]
        print(f"✅ Created product ID: {product_id}")
        
        # Set inventory to 1
        print("📊 Setting inventory to 1 item...")
        await client.post(
            "http://localhost:8003/release",
            json={"product_id": product_id, "quantity": 1}
        )
        print("✅ Inventory set")
        
        # Launch 100 concurrent requests
        print("\n🚀 Launching 100 concurrent order requests...")
        print("-" * 60)
        
        start_time = time.time()
        tasks = [create_order(client, product_id, 1, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Analyze results
        successes = [r for r in results if r["success"]]
        failures = [r for r in results if not r["success"]]
        
        print(f"\n📈 Test Results (completed in {end_time - start_time:.2f}s)")
        print("=" * 60)
        print(f"✅ Successful orders: {len(successes)}")
        print(f"❌ Failed orders: {len(failures)}")
        
        if len(successes) == 1:
            print("\n🎉 TEST PASSED: Exactly 1 order succeeded (lock works!)")
            print(f"   Winner: User {successes[0]['user_id']}")
        else:
            print(f"\n⚠️  TEST FAILED: Expected 1 success, got {len(successes)}")
            print("   This indicates a race condition!")
        
        # Check inventory
        inventory_response = await client.get(f"http://localhost:8003/inventory/{product_id}")
        final_inventory = inventory_response.json()["quantity"]
        print(f"\n📊 Final inventory: {final_inventory}")
        
        if final_inventory == 0 and len(successes) == 1:
            print("✅ Inventory correctly depleted")
        else:
            print("⚠️  Inventory mismatch detected")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_concurrent_orders())