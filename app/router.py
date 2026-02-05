from typing import Any, Dict, Tuple, List
from .schemas import TaskType, RouteRequest, RouteDecision

HARD_REASONING_KEYWORDS = [
    "compare", "trade-off", "recommend", "decide", "why", "pros and cons",
    "strategy", "prioritize", "diagnose", "root cause"
]

INTENT_VERBS = {
    TaskType.reasoning_decision: [
        "should we",
        "what should",
        "decide",
        "recommend",
        "trade-off",
        "pros and cons",
        "is it worth",
        "which option",
        "next step",
        "best next"
    ],
    TaskType.planning_checklist: [
        "plan",
        "roadmap",
        "steps",
        "how would you",
        "approach",
        "rollout",
        "ship",
        "milestones",
    ],
    TaskType.rewrite_formatting: [
        "rewrite",
        "rephrase",
        "clean this",
        "fix this",
        "make this",
        "polish",
        "professional",
    ],
    TaskType.extraction_structuring: [
        "extract",
        "pull out",
        "key info",
        "structure",
        "turn this into",
        "convert to",
        "json",
        "table",
    ],
}


def _contains_any(text: str, keywords: List[str]) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in keywords)

def _infer_from_intent_verbs(task: str) -> Tuple[TaskType | None, str | None]:
    task_l = task.lower()
    for task_type, phrases in INTENT_VERBS.items():
        for phrase in phrases:
            if phrase in task_l:
                return task_type, f"intent:{phrase}"
    return None, None

def _infer_task_type(task: str, rules: Dict[str, Any]) -> Tuple[TaskType, str]:
    # 1) Intent verbs (NEW)
    intent_task, intent_reason = _infer_from_intent_verbs(task)
    if intent_task is not None:
        return intent_task, intent_reason

    # 2) Keyword-based inference (existing behavior)
    task_l = task.lower()
    task_types = rules.get("task_types", {})
    for tt_name, tt_cfg in task_types.items():
        for kw in tt_cfg.get("keywords", []):
            if kw.lower() in task_l:
                return TaskType(tt_name), f"keyword:{kw}"

    # 3) Fallback
    return TaskType.summarization, "no_intent_or_keyword_match"



def decide_route(req: RouteRequest, rules: Dict[str, Any]) -> RouteDecision:
    reason_codes: List[str] = []
    task_text = req.task

    # 1) Task type
    if req.task_type_hint is not None:
        task_type = req.task_type_hint
        reason_codes.append("RULE_TASK_TYPE_DEFAULT")
        routing_reason = f"Used task_type_hint={task_type.value}"
    else:
        task_type, match_reason = _infer_task_type(task_text, rules)
        if match_reason.startswith("intent:"):
            reason_codes.append("RULE_INTENT_MATCH")
        elif match_reason.startswith("keyword:"):
            reason_codes.append("RULE_KEYWORD_MATCH")
        else:
            reason_codes.append("FALLBACK_DEFAULT")

        routing_reason = f"Inferred task_type={task_type.value} ({match_reason})"

    # 2) Default tier by task type
    tt_cfg = rules.get("task_types", {}).get(task_type.value, {})
    chosen_tier = tt_cfg.get("default_tier", rules.get("default_model_tier", "cheap"))

    # 3) Escalate if "hard reasoning" keywords are present (generic)
    if _contains_any(task_text, HARD_REASONING_KEYWORDS) and chosen_tier != "strong":
        chosen_tier = "strong"
        reason_codes.append("RULE_KEYWORD_MATCH")
        routing_reason += " | Escalated due to HARD_REASONING_KEYWORDS"

    # 4) Escalate if task-type-specific escalation keywords match
    esc_keywords = tt_cfg.get("escalate_if_keywords", [])
    if esc_keywords and _contains_any(task_text, esc_keywords) and chosen_tier != "strong":
        chosen_tier = "strong"
        reason_codes.append("RULE_KEYWORD_MATCH")
        routing_reason += f" | Escalated due to task_type escalation keywords"

    # 5) Long text heuristic
    heur = rules.get("heuristics", {})
    threshold = int(heur.get("long_text_chars_threshold", 2500))
    if len(task_text) >= threshold and chosen_tier != "strong":
        chosen_tier = heur.get("long_text_escalate_to", "strong")
        reason_codes.append("HEURISTIC_LONG_TEXT")
        routing_reason += f" | Escalated due to long_text_chars>={threshold}"

    # 6) Risk-level escalation (simple v1)
    if req.constraints.risk_level in ("high",) and chosen_tier != "strong":
        chosen_tier = "strong"
        reason_codes.append("RULE_TASK_TYPE_DEFAULT")
        routing_reason += " | Escalated due to risk_level=high"

    # 7) Map tier -> model name
    models = rules.get("models", {})
    chosen_model_name = models.get(chosen_tier, {}).get("name", "UNKNOWN_MODEL")

    return RouteDecision(
        chosen_tier=chosen_tier,
        chosen_model_name=chosen_model_name,
        task_type=task_type,
        reason_codes=reason_codes,
        routing_reason=routing_reason,
    )
