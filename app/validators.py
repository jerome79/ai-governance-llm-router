import json
import re
from typing import Tuple, Optional, List
from jsonschema import Draft7Validator

UNCERTAINTY_PATTERNS = [
    r"\b(i think|maybe|not sure|cannot confirm|unknown)\b",
]

def detect_uncertainty(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in UNCERTAINTY_PATTERNS)

def extract_json_block(text: str) -> Optional[dict]:
    """
    Tries to parse the entire text as JSON first.
    If that fails, tries to find the first {...} block.
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    # naive bracket extraction (good enough for Day 5)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            return None
    return None

def validate_required_keys(obj: dict, required_keys: List[str]) -> Tuple[bool, str]:
    missing = [k for k in required_keys if k not in obj]
    if missing:
        return False, f"missing_keys:{missing}"
    return True, "ok"

def validate_output(answer: str, output_format: str, required_json_keys: List[str], max_words: Optional[int]) -> Tuple[bool, str]:
    """
    Returns (pass, reason).
    """
    if not answer or not answer.strip():
        return False, "empty_answer"

    if max_words is not None:
        words = answer.strip().split()
        if len(words) > max_words:
            return False, f"too_long:{len(words)}>{max_words}"

    # Heuristic: avoid uncertain answers for high-stakes formatting/extraction
    if detect_uncertainty(answer):
        return False, "uncertainty_language"

    if output_format == "json":
        obj = extract_json_block(answer)
        if obj is None or not isinstance(obj, dict):
            return False, "invalid_json"
        ok, reason = validate_required_keys(obj, required_json_keys)
        if not ok:
            return False, reason

    return True, "ok"
