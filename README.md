# LLM Routing Control Plane

**Deterministic, Cost-Aware Governance for Production AI Systems**

This project implements a quality-aware routing layer for Large Language Models designed as a control plane — not a prompt demo.

## Key Features

- **Deterministic model selection**
- **Cheap-first execution strategy**
- **Automatic output validation**
- **Controlled escalation**
- **Risk-aligned routing**
- **Observability and regression protection**

### The Objective

> Make LLM usage economically scalable and operationally predictable.

## Why This Matters

In production environments, LLM usage directly impacts:

- Infrastructure cost
- Gross margins
- Latency SLAs
- Reliability guarantees

Strong reasoning models are often **~10× slower** than lightweight models.

Without routing, teams either:

- Overpay for unnecessary reasoning capacity
- Or degrade quality unpredictably

**Routing is not an optimization. It is governance.**

## Architecture

```
Client
  |
  v
/route
  |
  v
Decision Layer
  - task hint
  - intent phrases
  - keyword rules
  - risk level
  |
  v
Execution Strategy
  - direct
  - cheap-first + verify
  |
  v
Cheap Model ──► Validators ──► Strong Model (on failure)
      |
      +── Cache
```

## Design Principles

- Separation of decision and execution logic
- Config-driven routing rules
- Explainable reason codes
- Provider-agnostic model execution
- Benchmark-driven validation
- Regression-safe behavior tracking

> The router is not designed to be clever.  
> It is designed to be predictable, measurable, and auditable.

## Model Tiers (Benchmark Setup)

For controlled evaluation, tiers were simulated using Ollama:

### Cheap Tier

- **Model:** `gemma3:1b`
- **Characteristics:** Fast, low memory, limited reasoning

### Strong Tier

- **Model:** `llama3:8b`
- **Characteristics:** Higher latency, stronger reasoning

**Observed difference:** ~5–8 seconds (cheap) vs ~75 seconds (strong)

### Provider Support

The architecture is provider-agnostic and extendable to:

- OpenAI
- Anthropic
- Mistral
- Any API-based LLM provider

## Execution Strategy

For structured tasks:

1. Execute cheap model
2. Validate output
3. Escalate only if validation fails

### Validators Include

- JSON schema enforcement
- Required key checks
- Length constraints
- Uncertainty detection

**On benchmark:** ~96% of tasks succeeded on cheap tier.

## Evaluation & Regression Discipline

The system includes:

- Structured routing benchmark
- Inference-only stress testing
- Latency measurement by tier
- Escalation tracking
- Frozen baselines
- Regression checks

Routing decisions remain stable even after execution optimizations.

## What This Demonstrates

- LLM usage requires governance layers
- Cheap-first + validation scales better than default strong usage
- Intent detection provides meaningful inference signal
- Risk should bias routing decisions
- Observability is essential for production AI
- Complexity should follow evidence — not precede it

## Getting Started

1. Install dependencies
2. Start Ollama with selected models
3. Launch FastAPI server
4. Run evaluation scripts in `/eval`

## Blog Article

Architectural and strategic write-up:

👉 [Read on Medium](https://medium.com/)

---

## Philosophy

This repository reflects an approach to AI system design focused on economic governance, scalability, and production reliability rather than experimentation alone.
