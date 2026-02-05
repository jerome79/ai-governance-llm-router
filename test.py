import requests

url = "http://localhost:8000/route"
payload = {
    "task": "Say exactly: warmup ok",
    "constraints": { "risk_level": "low" }
  }

response = requests.post(url, json=payload)
print(response.status_code)
print(response.json())