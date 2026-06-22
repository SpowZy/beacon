"""HTTP service.

Two endpoints that mirror the two sides of a community platform:
  POST /alert                      run the agentic pipeline on an incoming alert
  GET  /community/{suburb}/insight a differentially private community aggregate

The aggregate is the privacy preserving, P2 classified number you could sell to
a retail partner without ever exposing a household. Run it with:
  pip install -e ".[api]"
  uvicorn beacon.api:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from .agents.privacy import dp_count
from .config import load_settings
from .graph import run_pipeline
from .models import Coordinate, PipelineResult, RawAlert
from .synth import generate_residents

settings = load_settings()
residents = generate_residents(n=30, seed=7)

app = FastAPI(title="Beacon", version="0.1.0")


class AlertIn(BaseModel):
    id: str
    text: str
    suburb: str
    lat: float
    lon: float


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "backend": settings.llm_backend, "residents": len(residents)}


@app.post("/alert", response_model=PipelineResult)
def ingest_alert(payload: AlertIn) -> PipelineResult:
    alert = RawAlert(
        id=payload.id,
        text=payload.text,
        suburb=payload.suburb,
        location=Coordinate(lat=payload.lat, lon=payload.lon),
    )
    return run_pipeline(alert, residents, settings)


@app.get("/community/{suburb}/insight")
def community_insight(suburb: str) -> dict:
    true_count = sum(1 for r in residents if r.suburb.lower() == suburb.lower())
    private_value = dp_count(true_count, epsilon=settings.dp_epsilon)
    return {
        "suburb": suburb,
        "metric": "registered_residents",
        "value_dp": round(private_value, 1),
        "epsilon": settings.dp_epsilon,
        "classification": "P2",
        "note": "differentially private aggregate, no PII, safe for B2B release",
    }
