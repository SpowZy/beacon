# Beacon architecture

Beacon is a small, readable model of the AI layer a community safety platform
needs. It takes a raw local alert and turns it into a trustworthy, geographically
targeted notification, while keeping every community level number free of
personal data. This note explains the design and the choices behind it.

## The pipeline

The orchestrator is a typed state graph built with LangGraph. Each step is an
agent with a single responsibility, and a conditional edge at the end decides
whether a message is delivered or held.

```
triage  ->  privacy  ->  routing  ->  compose  ->  verify  ->  deliver or hold
```

- triage assigns a severity and a category.
- privacy redacts personal identifiers, classifies the payload P2, and writes an
  audit id. This is the governance layer, the DARS idea.
- routing matches the alert to residents by distance and by watch zones.
- compose builds a grounded message and adds retrieved local guidance. This is
  the retrieval augmented step.
- verify re-checks for leaked PII, confirms the message is grounded in the
  source, and confirms the routing fits the severity. Nothing ships unless this
  gate passes.

## Why these choices

Orchestration with LangGraph. In 2026 LangGraph is the common choice for
stateful, auditable agent graphs, with durable state and explicit conditional
routing. A single prompt cannot give you a trust gate you can test.

Privacy as code, not as a prompt. The redaction and classification are
deterministic, so they are auditable and unit tested. For a safety product this
is the right default. The differential privacy helper uses the Laplace
mechanism, the same approach used in production by the US Census Bureau, so
released community aggregates cannot be traced back to a household.

A verification gate. The habit comes from evaluating frontier models: a
confident wrong message is the real risk in a safety setting, so it is blocked
before delivery and measured in the evaluation harness.

LLM and SLM orchestration. The model layer is pluggable. The default is a
deterministic mock, so the project runs free and reproducibly. The same code
runs on a local small model through Ollama, or on Claude, by changing one
environment variable.

## How it maps to a community platform

- Address based alerts and watch zones map to the routing agent.
- Community level intelligence with no PII maps to the privacy agent and the
  differential privacy endpoint, which is the shape of a privacy preserving B2B
  data product.
- Simple, trustworthy conversational output maps to compose plus verify.

## How to grow it

- Retrieval. The lexical retriever shares the interface a vector store would
  use, so it can grow into adaptive and corrective retrieval, where a router
  picks naive, agentic, or graph retrieval per query, and a critic re-retrieves
  when the context is weak.
- Data. The synthetic generator can be swapped for a real open data ingestion
  path without touching the agents.
- Memory. A working, episodic, and semantic memory can be added per resident and
  per community, with governance over what may be written, read, or forgotten.

## References

- LangGraph for stateful agent orchestration, the production standard in 2026.
- Adaptive, corrective, and self reflective retrieval augmented generation, and
  graph based retrieval for relationship questions. See the 2026 survey work on
  retrieval augmented generation (arXiv 2507.18910) and agentic graph retrieval
  (arXiv 2509.22009).
- Differential privacy with the Laplace mechanism, as deployed by the US Census
  Bureau. Open tooling includes OpenDP and the IBM differential privacy library.
- Agent memory as a first class component, with multi layer designs and
  governance over memory (arXiv 2603.29194, arXiv 2604.16548).
