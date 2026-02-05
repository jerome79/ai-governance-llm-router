import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Paths (adjust if your filenames differ)
ROUTING_PATH = Path(__file__).parent /"results_withcache.jsonl" # nested structure
INFERENCE_PATH = Path(__file__).parent /"inference_results.jsonl"                # routing-only, decision nested
OUT_DIR = Path(__file__).parent /"plots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def flatten_routing_records(records):
    """
    Input record example:
    {
      "task_payload": {...},
      "response": {
         "decision": {...},
         "latency_ms": ...,
         "final_model_name": ...,
         ...
      },
      "elapsed_ms_client": ...
    }
    """
    rows = []
    for r in records:
        payload = r.get("task_payload", {}) or {}
        resp = r.get("response", {}) or {}
        dec = resp.get("decision", {}) or {}

        rows.append({
            # payload
            "has_hint": payload.get("task_type_hint") is not None,
            "task_type_hint": payload.get("task_type_hint"),
            "risk_level": (payload.get("constraints") or {}).get("risk_level"),
            "task_len_chars": len(payload.get("task") or ""),

            # decision
            "task_type": dec.get("task_type"),
            "chosen_tier": dec.get("chosen_tier"),
            "chosen_model": dec.get("chosen_model_name"),
            "reason_codes": ",".join(dec.get("reason_codes") or []),

            # response / metrics
            "latency_ms_total": resp.get("latency_ms"),
            "final_model_name": resp.get("final_model_name"),
            "escalated": resp.get("escalated"),
            "escalation_reason": resp.get("escalation_reason"),

            # client-side measure
            "elapsed_ms_client": r.get("elapsed_ms_client"),
        })
    return pd.DataFrame(rows)

def flatten_inference_records(records):
    """
    Inference record created by run_inference_eval.py typically like:
    { "task": "...", "risk_level": "...", "decision": {...} }
    """
    rows = []
    for r in records:
        dec = r.get("decision", {}) or {}
        rows.append({
            "task": r.get("task"),
            "risk_level": r.get("risk_level"),
            "task_type": dec.get("task_type"),
            "chosen_tier": dec.get("chosen_tier"),
            "reason_codes": ",".join(dec.get("reason_codes") or []),
        })
    return pd.DataFrame(rows)

# -------- Load + flatten --------
routing_raw = load_jsonl(ROUTING_PATH)
df_r = flatten_routing_records(routing_raw)

inference_raw = load_jsonl(INFERENCE_PATH) if INFERENCE_PATH.exists() else []
df_i = flatten_inference_records(inference_raw) if inference_raw else pd.DataFrame()

# -------- Chart A: Routing by task type (stacked) --------
ct = pd.crosstab(df_r["task_type"], df_r["chosen_tier"])
ct = ct.reindex(["summarization", "extraction_structuring", "rewrite_formatting", "planning_checklist", "reasoning_decision"], fill_value=0)
ct.plot(kind="bar", stacked=True)
plt.title("Routing by task type")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig(OUT_DIR / "routing_by_task_type.png")
plt.close()

# -------- Chart B: Avg latency by tier --------
lat = df_r.groupby("chosen_tier")["latency_ms_total"].mean().sort_index()
lat.plot(kind="bar")
plt.title("Average latency by tier (ms)")
plt.ylabel("Latency (ms)")
plt.tight_layout()
plt.savefig(OUT_DIR / "latency_by_tier.png")
plt.close()

# -------- Chart C: Inference task type distribution (no hints) --------
if not df_i.empty:
    df_i["task_type"].value_counts().plot(kind="bar")
    plt.title("Inferred task types (no hints)")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "inference_task_type_distribution.png")
    plt.close()

    # -------- Chart D: Tier by risk (inference only) --------
    pd.crosstab(df_i["risk_level"], df_i["chosen_tier"]).plot(kind="bar", stacked=True)
    plt.title("Tier by risk level (inference only)")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "tier_by_risk.png")
    plt.close()

print(f"Saved plots to: {OUT_DIR.resolve()}")
