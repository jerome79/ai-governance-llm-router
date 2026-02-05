import json
import requests
from pathlib import Path
from tqdm import tqdm

BASE_URL = "http://localhost:8000"
TASKS_PATH = Path("eval/inference_tasks.jsonl")
OUT_PATH = Path("eval/inference_results.jsonl")

def main():
    tasks = [json.loads(l) for l in TASKS_PATH.read_text().splitlines() if l.strip()]
    OUT_PATH.parent.mkdir(exist_ok=True)

    if OUT_PATH.exists():
        OUT_PATH.unlink()

    for payload in tqdm(tasks, total=len(tasks)):
        payload["execute"] = False  # routing only
        r = requests.post(f"{BASE_URL}/route", json=payload, timeout=60)
        r.raise_for_status()
        resp = r.json()

        with OUT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "task": payload["task"],
                "risk_level": payload["constraints"]["risk_level"],
                "decision": resp["decision"]
            }) + "\n")

    print("Inference eval done:", OUT_PATH)

if __name__ == "__main__":
    main()
