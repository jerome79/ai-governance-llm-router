import json
from pathlib import Path
import pandas as pd

RESULTS_PATH = Path("eval/quality_results.jsonl")

def main():
    rows = []
    for line in RESULTS_PATH.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        payload = rec.get("task_payload", {})
        resp = rec.get("response", {})
        dec = resp.get("decision", {})

        rows.append({
            "task_type": dec.get("task_type"),
            "chosen_tier": dec.get("chosen_tier"),
            "final_model": resp.get("final_model_name"),
            "escalated": resp.get("escalated"),
            "escalation_reason": resp.get("escalation_reason"),
            "latency_ms": resp.get("latency_ms"),
            "elapsed_ms_client": rec.get("elapsed_ms_client"),
        })

    df = pd.DataFrame(rows)

    print("\n== Run size ==")
    print(len(df))

    print("\n== Escalation rate ==")
    print(df["escalated"].value_counts(dropna=False).to_string())

    print("\n== Escalation by task_type ==")
    print(pd.crosstab(df["task_type"], df["escalated"]).to_string())

    print("\n== Top escalation reasons ==")
    print(df["escalation_reason"].value_counts(dropna=False).head(10).to_string())

    print("\n== Avg latency by final model ==")
    print(df.groupby("final_model")["latency_ms"].mean().round(1).to_string())

if __name__ == "__main__":
    main()
