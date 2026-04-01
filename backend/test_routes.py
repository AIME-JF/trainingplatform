import requests

try:
    response = requests.get("http://127.0.0.1:8001/api/v1/", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

try:
    response = requests.get("http://127.0.0.1:8001/openapi.json", timeout=5)
    print(f"OpenAPI Status: {response.status_code}")
    paths = response.json().get("paths", {})
    print("Available paths:")
    for p in sorted(paths.keys()):
        print(f"  {p}")
except Exception as e:
    print(f"Error: {e}")