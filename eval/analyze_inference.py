import json
import pandas as pd
from pathlib import Path

PATH = Path("eval/inference_results.jsonl")

rows = []
for l in PATH.read_text().splitlines():
    r = json.loads(l)
    d = r["decision"]
    rows.append({
        "task": r["task"],
        "risk": r["risk_level"],
        "task_type": d["task_type"],
        "tier": d["chosen_tier"],
        "reason": ",".join(d["reason_codes"])
    })

df = pd.DataFrame(rows)

print("\n== Inferred task_type distribution ==")
print(df["task_type"].value_counts().to_string())

print("\n== Inferred tier distribution ==")
print(df["tier"].value_counts().to_string())

print("\n== Tier by risk_level ==")
print(pd.crosstab(df["risk"], df["tier"]).to_string())

print("\n== Sample ambiguous cases ==")
print(df.sample(5)[["task","task_type","tier","reason"]].to_string(index=False))
