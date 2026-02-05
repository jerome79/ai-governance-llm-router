import json
from pathlib import Path
import pandas as pd

RESULTS_PATH = Path("eval/results.jsonl")

def main():
    if not RESULTS_PATH.exists():
        raise FileNotFoundError("No results found. Run python eval/run_eval.py first.")

    rows = []
    for line in RESULTS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        payload = rec.get("task_payload", {})
        resp = rec.get("response", {})
        dec = resp.get("decision", {})

        rows.append({
            "task_type_hint": payload.get("task_type_hint"),
            "has_hint": payload.get("task_type_hint") is not None,
            "risk_level": (payload.get("constraints") or {}).get("risk_level"),
            "chosen_tier": dec.get("chosen_tier"),
            "chosen_model": dec.get("chosen_model_name"),
            "task_type": dec.get("task_type"),
            "latency_ms_total": resp.get("latency_ms"),
            "elapsed_ms_client": rec.get("elapsed_ms_client"),
            "reason_codes": ",".join(dec.get("reason_codes") or []),
            "task_len": len(payload.get("task") or ""),
        })

    df = pd.DataFrame(rows)

    print("\n== Run size ==")
    print(len(df))

    print("\n== Hint coverage ==")
    print(df["has_hint"].value_counts().to_string())

    print("\n== Routing distribution ==")
    print(df["chosen_tier"].value_counts().to_string())

    print("\n== Routing by task_type ==")
    print(pd.crosstab(df["task_type"], df["chosen_tier"]).to_string())

    print("\n== Avg latency by tier (ms) ==")
    print(df.groupby("chosen_tier")["latency_ms_total"].mean().round(1).to_string())

    print("\n== Avg latency by task_type (ms) ==")
    print(df.groupby("task_type")["latency_ms_total"].mean().round(1).to_string())

    print("\n== Top reason codes ==")
    exploded = df["reason_codes"].fillna("").str.split(",", expand=True).stack()
    print(exploded.value_counts().head(12).to_string())

    print("\n== Hint vs inferred routing (counts) ==")
    print(pd.crosstab(df["has_hint"], df["chosen_tier"]).to_string())

if __name__ == "__main__":
    main()
