import requests
import json

url = "http://localhost:8000/route"
payload = {
    "task": "Summarize in 3 bullets: AI adoption is accelerating across industries...",
    "constraints": {"risk_level": "low"}
}
headers = {"Content-Type": "application/json"}

resp = requests.post(url, headers=headers, json=payload)
print(f"Status: {resp.status_code}")
try:
    print(json.dumps(resp.json(), indent=2))
except ValueError:
    print(resp.text)