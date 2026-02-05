import json
from pathlib import Path
import statistics as stats

BASELINE = Path("eval/baseline_day6_with_cache.jsonl")
CURRENT = Path("eval/results_day8_with_cache_duplicates.jsonl")

def load(path):
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

def avg(xs):
    xs = [x for x in xs if x is not None]
    return round(stats.mean(xs), 2) if xs else None

def main():
    base = load(BASELINE)
    cur = load(CURRENT)

    def metrics(rows):
        cheap_lat, strong_lat, esc = [], [], 0
        for r in rows:
            if r["final_model_name"]:
                if "strong" in r["final_model_name"] or "llama" in r["final_model_name"]:
                    strong_lat.append(r["latency_ms_llm"])
                else:
                    cheap_lat.append(r["latency_ms_llm"])
            if r.get("escalated"):
                esc += 1
        return {
            "avg_cheap_latency": avg(cheap_lat),
            "avg_strong_latency": avg(strong_lat),
            "escalation_rate": round(esc / max(1, len(rows)), 3),
        }

    m_base = metrics(base)
    m_cur = metrics(cur)

    print("== BASELINE ==")
    print(m_base)
    print("== CURRENT ==")
    print(m_cur)

    # Guardrails (tune later)
    if m_cur["escalation_rate"] > m_base["escalation_rate"] + 0.05:
        raise SystemExit("FAIL: escalation rate regression")

    if m_cur["avg_cheap_latency"] > m_base["avg_cheap_latency"] * 1.2:
        raise SystemExit("FAIL: cheap latency regression")

    print("PASS: regression checks OK")

if __name__ == "__main__":
    main()
