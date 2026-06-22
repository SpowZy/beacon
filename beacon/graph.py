"""LangGraph orchestration.

The pipeline is a small typed state graph: triage, then privacy, then routing,
then compose, then verify. A conditional edge after verify decides whether the
alert is delivered or held. The trace accumulates so every run is auditable.
"""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from .agents.privacy import enforce
from .agents.routing import route
from .agents.triage import triage as run_triage
from .compose import compose_message
from .config import Settings
from .llm import get_llm
from .models import (
    PipelineResult,
    PrivacyResult,
    RawAlert,
    Resident,
    RoutingResult,
    TriageResult,
    VerificationResult,
)
from .verify import verify


class PipelineState(TypedDict, total=False):
    raw_alert: RawAlert
    residents: list[Resident]
    triage: TriageResult
    privacy: PrivacyResult
    routing: RoutingResult
    message: str
    verification: VerificationResult
    status: str
    trace: Annotated[list[str], operator.add]


def build_graph(settings: Settings):
    llm = get_llm(settings)

    def triage_node(state: PipelineState) -> PipelineState:
        t = run_triage(state["raw_alert"])
        return {"triage": t, "trace": [f"triage: {t.severity.value} / {t.category.value} (conf {t.confidence})"]}

    def privacy_node(state: PipelineState) -> PipelineState:
        p = enforce(state["raw_alert"])
        return {
            "privacy": p,
            "trace": [f"privacy: {p.classification}, redactions {p.redactions}, types {p.pii_types}"],
        }

    def routing_node(state: PipelineState) -> PipelineState:
        r = route(state["raw_alert"], state["triage"], state["residents"], settings)
        return {"routing": r, "trace": [f"routing: {len(r.recipients)} recipients within {r.radius_km} km"]}

    def compose_node(state: PipelineState) -> PipelineState:
        msg = compose_message(state["raw_alert"], state["triage"], state["privacy"], llm)
        return {"message": msg, "trace": [f"compose: {msg}"]}

    def verify_node(state: PipelineState) -> PipelineState:
        v = verify(state["triage"], state["privacy"], state["routing"], state["message"])
        return {"verification": v, "trace": [f"verify: approved={v.approved} issues={v.issues}"]}

    def decide(state: PipelineState) -> str:
        return "deliver" if state["verification"].approved else "hold"

    def deliver_node(state: PipelineState) -> PipelineState:
        return {"status": "delivered", "trace": ["status: delivered"]}

    def hold_node(state: PipelineState) -> PipelineState:
        return {"status": "held", "trace": ["status: held for review"]}

    g = StateGraph(PipelineState)
    g.add_node("triage", triage_node)
    g.add_node("privacy", privacy_node)
    g.add_node("routing", routing_node)
    g.add_node("compose", compose_node)
    g.add_node("verify", verify_node)
    g.add_node("deliver", deliver_node)
    g.add_node("hold", hold_node)

    g.add_edge(START, "triage")
    g.add_edge("triage", "privacy")
    g.add_edge("privacy", "routing")
    g.add_edge("routing", "compose")
    g.add_edge("compose", "verify")
    g.add_conditional_edges("verify", decide, {"deliver": "deliver", "hold": "hold"})
    g.add_edge("deliver", END)
    g.add_edge("hold", END)
    return g.compile()


def run_pipeline(raw_alert: RawAlert, residents: list[Resident], settings: Settings) -> PipelineResult:
    graph = build_graph(settings)
    final = graph.invoke({"raw_alert": raw_alert, "residents": residents, "trace": []})
    return PipelineResult(
        alert_id=raw_alert.id,
        triage=final["triage"],
        privacy=final["privacy"],
        routing=final["routing"],
        message=final["message"],
        verification=final["verification"],
        status=final.get("status", "unknown"),
        trace=final.get("trace", []),
    )
