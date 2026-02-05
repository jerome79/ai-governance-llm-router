import json
import time
import requests
from pathlib import Path
from tqdm import tqdm

BASE_URL = "http://localhost:8000"
TASKS_PATH = Path("eval/tasks.jsonl")
RESULTS_PATH = Path("eval/results.jsonl")

def post(payload):
    r = requests.post(f"{BASE_URL}/route", json=payload, timeout=600)
    r.raise_for_status()
    return r.json()

def warmup():
    # warmup cheap
    post({"task": "Say 'warmup ok' in 2 words.", "execute": True, "constraints": {"risk_level": "low"}})
    # warmup strong (force by decision language)
    post({"task": "Compare A vs B briefly and decide.", "execute": True, "constraints": {"risk_level": "high"}})

def main():
    assert TASKS_PATH.exists(), f"Missing {TASKS_PATH}"
    tasks = [json.loads(line) for line in TASKS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

    print(f"Warmup...")
    warmup()

    print(f"Running {len(tasks)} tasks against {BASE_URL}/route ...")
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if RESULTS_PATH.exists():
        RESULTS_PATH.unlink()

    for payload in tqdm(tasks, total=len(tasks)):
        payload.setdefault("execute", True)
        t0 = time.perf_counter()
        data = post(payload)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        record = {
            "task_payload": payload,
            "response": data,
            "elapsed_ms_client": elapsed_ms,
        }
        with RESULTS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Done. Results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    main()
