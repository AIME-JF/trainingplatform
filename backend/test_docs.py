import requests

try:
    response = requests.get("http://127.0.0.1:8001/docs", timeout=5, allow_redirects=False)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Swagger UI available")
    elif response.status_code == 302:
        print(f"Redirect to: {response.headers.get('Location')}")
except Exception as e:
    print(f"Error: {e}")