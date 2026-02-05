import requests
import json

BASE_URL = "http://localhost:8000"

def post(payload):
    r = requests.post(f"{BASE_URL}/route", json=payload, timeout=300)
    r.raise_for_status()
    return r.json()

print("== Health ==")
print(requests.get(f"{BASE_URL}/health").json())

print("\n== Decision only ==")
print(json.dumps(post({
    "task": "Rewrite this email to be more professional.",
    "execute": False
}), indent=2))

print("\n== Strong model ==")
print(json.dumps(post({
    "task": "Compare two LLM routing strategies and recommend one for production, explaining trade-offs.",
    "constraints": { "risk_level": "medium" },
    "execute": False
}), indent=2))

print("\n== Cheap model ==")
print(json.dumps(post({
    "task": "Summarize this text in 3 bullets: AI adoption is accelerating across industries...",
    "constraints": { "risk_level": "low" }
}), indent=2))

print("\n== Strong model ==")
print(json.dumps(post({
    "task": "Compare two LLM routing strategies and recommend one for production, explaining trade-offs.",
    "constraints": { "risk_level": "medium" }
}), indent=2))
