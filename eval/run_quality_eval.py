import json
import time
import requests
from pathlib import Path
from tqdm import tqdm

BASE_URL = "http://localhost:8000"
TASKS_PATH = Path("eval/quality_tasks.jsonl")
OUT_PATH = Path("eval/quality_results.jsonl")

def main():
    tasks = [json.loads(l) for l in TASKS_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUT_PATH.exists():
        OUT_PATH.unlink()

    for payload in tqdm(tasks, total=len(tasks)):
        payload.setdefault("execute", True)
        t0 = time.perf_counter()
        r = requests.post(f"{BASE_URL}/route", json=payload, timeout=600)
        r.raise_for_status()
        resp = r.json()
        dt = int((time.perf_counter() - t0) * 1000)

        rec = {
            "task_payload": payload,
            "response": resp,
            "elapsed_ms_client": dt,
        }
        with OUT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Saved {len(tasks)} results to {OUT_PATH}")

if __name__ == "__main__":
    main()
