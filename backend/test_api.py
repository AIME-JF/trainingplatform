import requests

try:
    response = requests.post(
        "http://127.0.0.1:8001/api/v1/auth/login",
        json={"username": "test", "password": "test"},
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")