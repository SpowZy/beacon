# Beacon

A privacy first agentic router for hyperlocal community alerts.

Beacon takes a raw local alert, triages it, strips every personal identifier,
routes it by geography to the right residents, and verifies the result before
anything is delivered. It is a small, readable model of the AI brain a
community safety product needs: simple, consistent, and trustworthy.

It runs from a clean clone with no API key, no downloaded model, and no
network. The default language backend is a deterministic mock, so the whole
pipeline is reproducible and free. Flip one environment variable to run the
same code on a local Ollama model or on Claude.

## Why this design

- Agentic orchestration with LangGraph: a typed state graph with a conditional
  trust gate, not a single prompt.
- Privacy as a first class agent: alerts are classified P2 (community level, no
  PII) and scrubbed before they move. A differential privacy helper is included
  for community level aggregates.
- A verification gate carried over from evaluating frontier models: a confident
  wrong message is the real risk in a safety product, so it is blocked.
- Pluggable models: mock, a local small model via Ollama, or Claude. That is
  LLM and SLM orchestration in practice.

## Quickstart

```
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m beacon.demo
```

No key is needed. You will see each synthetic alert flow through triage,
privacy, routing, composition, and verification, with the full trace.

Run the tests:

```
pytest -q
```

Use a real local model (free, after `ollama pull llama3.2`):

```
set BEACON_LLM_BACKEND=ollama
python -m beacon.demo
```

Use Claude:

```
set BEACON_LLM_BACKEND=anthropic
set BEACON_ANTHROPIC_API_KEY=your_key
python -m beacon.demo
```

## Pipeline

```
raw alert
  -> triage      severity and category
  -> privacy     redact PII, classify P2, write an audit id     (the DARS layer)
  -> routing     geographic match to homes and watch zones
  -> compose     grounded message plus retrieved guidance       (the RAG step)
  -> verify      no PII, grounded in source, routing sane        (the trust gate)
  -> deliver or hold
```

## Synthetic by design

The data in `beacon/synth.py` is fake and clearly labelled. Synthetic data
keeps the demo a one command clone and run, with full control over edge cases
such as a critical alert that carries personal details and must be scrubbed
before routing. The same interfaces accept real open data, so swapping in a
government open data feed is a local change, not a rewrite.

## Mapping to a community platform

- Address based alerts and watch zones map to the routing agent.
- Community level intelligence with no PII maps to the privacy agent and the
  differential privacy helper.
- Trustworthy conversational output maps to compose plus verify.

## Notes on the state of the art

Orchestration uses LangGraph, the current standard for stateful, auditable
agent graphs. The retrieval step is written so it can grow into adaptive and
corrective RAG. Privacy uses the Laplace mechanism, the differential privacy
approach used in production by the US Census Bureau and others. A longer write
up with citations lives in `docs/architecture.md`.
