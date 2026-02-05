from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any


class TaskType(str, Enum):
    summarization = "summarization"
    extraction_structuring = "extraction_structuring"
    rewrite_formatting = "rewrite_formatting"
    planning_checklist = "planning_checklist"
    reasoning_decision = "reasoning_decision"


ModelTier = Literal["cheap", "strong"]

ExecutionMode = Literal["direct", "cheap_first_verify"]

class OutputSpec(BaseModel):
    """
    Optional spec to validate output quality.
    Use this mainly for extraction_structuring tasks.
    """
    output_format: Literal["text", "json"] = "text"
    required_json_keys: List[str] = Field(default_factory=list)
    max_words: Optional[int] = None  # helpful for summaries


class RouteConstraints(BaseModel):
    max_cost: Optional[float] = Field(default=None, description="Optional max cost in USD (best-effort)")
    max_latency_ms: Optional[int] = Field(default=None, description="Optional max latency in ms (best-effort)")
    risk_level: Literal["low", "medium", "high"] = Field(default="low")


class RouteRequest(BaseModel):
    task: str = Field(..., min_length=1)
    task_type_hint: Optional[TaskType] = None
    constraints: RouteConstraints = Field(default_factory=RouteConstraints)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execute: bool = Field(default=True)
    execution_mode: ExecutionMode = Field(default="direct")
    output_spec: OutputSpec = Field(default_factory=OutputSpec)


class RouteDecision(BaseModel):
    chosen_tier: ModelTier
    chosen_model_name: str
    task_type: TaskType
    reason_codes: List[str]
    routing_reason: str

class UsageStats(BaseModel):
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

class RouteResponse(BaseModel):
    request_id: str
    decision: RouteDecision
    answer: Optional[str] = None
    latency_ms: Optional[int] = None
    usage: Optional[UsageStats] = None
    escalated: bool = False
    escalation_reason: Optional[str] = None
    final_model_name: Optional[str] = None