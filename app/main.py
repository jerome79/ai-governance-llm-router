from fastapi import FastAPI
from .schemas import RouteRequest, RouteResponse, UsageStats
from .config import load_rules
from .router import decide_route
from .llm_clients import OllamaChatClient
from .logging_utils import write_jsonl
import uuid
import time
from .validators import validate_output
from fastapi import FastAPI, HTTPException
from .cache import TTLCache


CACHE = TTLCache(ttl_seconds=3600, max_items=500)
app = FastAPI(title="LLM Router", version="0.1.0")

# Load rules once at startup (Day 1). Later you can add reload endpoint or file watcher.
RULES = load_rules("rules.yaml")
LLM = OllamaChatClient()
LOG_PATH = "logs/router.jsonl"


@app.get("/health")
def health():
    return {"status": "ok", "service": "llm-router", "version": app.version}

@app.get("/models")
def models():
    try:
        return LLM.list_models()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ollama_list_models_failed: {e}")

@app.post("/route", response_model=RouteResponse)
def route(req: RouteRequest):
    request_id = str(uuid.uuid4())
    t0 = time.perf_counter()

    decision = decide_route(req, RULES)

    # --- Decision-only mode ---
    if not req.execute:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        write_jsonl(LOG_PATH, {
            "request_id": request_id,
            "mode": "decision_only",
            "task_len_chars": len(req.task),
            "task_type_hint": req.task_type_hint.value if req.task_type_hint else None,
            "risk_level": req.constraints.risk_level,
            "decision": decision.model_dump(),
            "latency_ms_total": latency_ms,
        })
        return RouteResponse(
            request_id=request_id,
            decision=decision,
            answer=None,
            latency_ms=latency_ms,
            usage=None,
            escalated=False,
            escalation_reason=None,
            final_model_name=None,
        )

    # --- Shared variables ---
    system_text = (
        "You are a reliable assistant. Follow instructions carefully. "
        "If the user asks for structured output, comply strictly."
    )

    escalated = False
    escalation_reason = None
    cache_hit_first = False
    cache_hit_escalation = False

    # Helper: call model with cache
    def call_with_cache(model_name: str):
        nonlocal cache_hit_first, cache_hit_escalation
        cache_key = TTLCache.make_key(model=model_name, system_text=system_text, user_text=req.task)
        cached = CACHE.get(cache_key)
        if cached is not None:
            answer_ = cached.get("answer", "")
            usage_ = cached.get("usage") or {"input_tokens": None, "output_tokens": None, "total_tokens": None}
            llm_latency_ms_ = 0
            hit = True
        else:
            answer_, llm_latency_ms_, usage_ = LLM.chat(
                model=model_name,
                user_text=req.task,
                system_text=system_text
            )
            CACHE.set(cache_key, {"answer": answer_, "usage": usage_})
            hit = False
        return answer_, llm_latency_ms_, usage_, hit

    # --- Decide initial model (mode-aware) ---
    initial_model = decision.chosen_model_name

    if req.execution_mode == "cheap_first_verify":
        cheap_first_types = {"summarization", "extraction_structuring", "rewrite_formatting"}
        if decision.task_type.value in cheap_first_types:
            initial_model = RULES["models"]["cheap"]["name"]

    # --- First call (ALWAYS executed) ---
    answer, llm_latency_ms, usage, cache_hit_first = call_with_cache(initial_model)
    final_model = initial_model

    # --- Validate + optional escalation (only in cheap_first_verify) ---
    if req.execution_mode == "cheap_first_verify":
        ok, reason = validate_output(
            answer=answer,
            output_format=req.output_spec.output_format,
            required_json_keys=req.output_spec.required_json_keys,
            max_words=req.output_spec.max_words,
        )

        if not ok and final_model != RULES["models"]["strong"]["name"]:
            escalated = True
            escalation_reason = reason

            strong_model = RULES["models"]["strong"]["name"]
            answer, llm_latency_ms_strong, usage, cache_hit_escalation = call_with_cache(strong_model)

            # If escalation happened and we actually called strong (non-cache), keep its latency
            # If it was cached, llm_latency_ms_strong == 0
            llm_latency_ms = llm_latency_ms_strong
            final_model = strong_model

    total_latency_ms = max(1, round((time.perf_counter() - t0) * 1000))

    # --- Log ---
    write_jsonl(LOG_PATH, {
        "request_id": request_id,
        "mode": "execute",
        "execution_mode": req.execution_mode,
        "task_len_chars": len(req.task),
        "task_type_hint": req.task_type_hint.value if req.task_type_hint else None,
        "risk_level": req.constraints.risk_level,
        "decision": decision.model_dump(),
        "final_model_name": final_model,
        "escalated": escalated,
        "escalation_reason": escalation_reason,
        "cache_hit_first": cache_hit_first,
        "cache_hit_escalation": cache_hit_escalation,
        "latency_ms_llm": llm_latency_ms,
        "latency_ms_total": total_latency_ms,
        "usage": usage,
        "answer_len_chars": len(answer or ""),
    })

    return RouteResponse(
        request_id=request_id,
        decision=decision,
        answer=answer,
        latency_ms=total_latency_ms,
        usage=UsageStats(**usage) if usage else None,
        escalated=escalated,
        escalation_reason=escalation_reason,
        final_model_name=final_model,
    )


@app.post("/warmup")
def warmup():
    try:
        # Warm cheap
        cheap = RULES["models"]["cheap"]["name"]
        strong = RULES["models"]["strong"]["name"]
        system_text = "Reply with exactly two words: warmup ok."
        a1, _, _ = LLM.chat(model=cheap, user_text="warmup", system_text=system_text)
        a2, _, _ = LLM.chat(model=strong, user_text="warmup", system_text=system_text)
        return {"status": "ok", "cheap_model": cheap, "strong_model": strong, "cheap_reply": a1, "strong_reply": a2}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"warmup_failed: {e}")

