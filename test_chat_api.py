import requests
import json

url = "http://127.0.0.1:8000/chat"
payload = {
    "message": "你好，测试一下",
    "history": [],
    "summary": "",
    "auto_save": False
}

print(f"Sending request to {url}...")
try:
    with requests.post(url, json=payload, stream=True) as response:
        print(f"Status Code: {response.status_code}")
        for line in response.iter_lines():
            if line:
                print(f"Response: {line.decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
