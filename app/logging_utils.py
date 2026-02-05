import json
import os
import time
from typing import Any, Dict


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_jsonl(filepath: str, record: Dict[str, Any]) -> None:
    ensure_dir(os.path.dirname(filepath))
    record = dict(record)
    record["ts"] = record.get("ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
