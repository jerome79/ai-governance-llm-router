from pathlib import Path
import yaml
from typing import Any, Dict


def load_rules(path: str = "rules.yaml") -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"rules.yaml not found at: {p.resolve()}")
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
