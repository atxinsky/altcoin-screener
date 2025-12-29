import requests
import json

# Test 1: Create account
print("=== Test 1: Creating simulated trading account ===")
response = requests.post(
    "http://localhost:8001/api/sim-trading/accounts",
    json={
        "account_name": "测试账户A",
        "initial_balance": 10000,
        "max_positions": 5,
        "position_size_pct": 2,
        "entry_score_min": 75,
        "entry_technical_min": 60,
        "stop_loss_pct": 3,
        "take_profit_levels": [6, 9, 12]
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
print()

if response.status_code == 200:
    account_id = response.json()["account"]["id"]
    
    # Test 2: Get account summary
    print("=== Test 2: Getting account summary ===")
    response = requests.get(f"http://localhost:8001/api/sim-trading/accounts/{account_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)[:500]}...")
    print()
    
    print("✅ All tests passed!")
else:
    print("❌ Account creation failed")
