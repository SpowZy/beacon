"""Offline evaluation harness.

The habit from evaluating frontier models, written as code: a small labelled
set, a few metrics that matter for a safety product, and hard thresholds the CI
can gate on. It runs on the mock backend, so it needs no API key.

Metrics:
  triage_accuracy  fraction where both severity and category match the label
  pii_leak_rate    fraction of delivered messages that still contain PII, target 0
  grounded_rate    fraction approved by the verification gate
  delivered_rate   fraction that reached delivery
"""
from __future__ import annotations

from dataclasses import dataclass

from .agents.privacy import _EMAIL, _PHONE
from .config import load_settings
from .graph import run_pipeline
from .models import Category, Coordinate, RawAlert, Severity
from .synth import SUBURBS, generate_residents


@dataclass
class Case:
    text: str
    suburb: str
    gold_severity: Severity
    gold_category: Category


def eval_set() -> list[Case]:
    return [
        Case("House fire on Elm Street, smoke visible.", "Palo Alto", Severity.CRITICAL, Category.FIRE),
        Case("Flooding reported after a water main break.", "Mountain View", Severity.URGENT, Category.FLOOD),
        Case("Planned roadworks on Oak Road this weekend.", "Menlo Park", Severity.ADVISORY, Category.ROADWORKS),
        Case("Robbery in progress near the plaza, suspect on foot.", "Palo Alto", Severity.URGENT, Category.CRIME),
        Case("Cardiac emergency, ambulance requested.", "Mountain View", Severity.CRITICAL, Category.MEDICAL),
        Case("Power outage affecting the area.", "Menlo Park", Severity.URGENT, Category.UTILITY),
        Case(
            "Assault reported. Victim Jane Doe, phone 555-123-4567.",
            "Palo Alto",
            Severity.URGENT,
            Category.CRIME,
        ),
        # A deliberately hard case. "gas smell" is not the keyword "gas leak",
        # so the simple classifier misses it. The eval exists to surface gaps
        # like this one, which is the whole point of measuring quality.
        Case("Strong gas smell reported near the school.", "Menlo Park", Severity.CRITICAL, Category.UTILITY),
    ]


def _has_pii(text: str) -> bool:
    return bool(_EMAIL.search(text) or _PHONE.search(text))


def run_eval() -> dict[str, float]:
    settings = load_settings()
    residents = generate_residents(n=30, seed=7)
    cases = eval_set()

    correct = leaks = grounded = delivered = 0
    for i, case in enumerate(cases):
        centre = SUBURBS.get(case.suburb, Coordinate(lat=37.44, lon=-122.14))
        alert = RawAlert(id=f"e{i:03d}", text=case.text, suburb=case.suburb, location=centre)
        res = run_pipeline(alert, residents, settings)
        if res.triage.severity == case.gold_severity and res.triage.category == case.gold_category:
            correct += 1
        if _has_pii(res.message):
            leaks += 1
        if res.verification.approved:
            grounded += 1
        if res.status == "delivered":
            delivered += 1

    n = len(cases)
    return {
        "cases": float(n),
        "triage_accuracy": round(correct / n, 3),
        "pii_leak_rate": round(leaks / n, 3),
        "grounded_rate": round(grounded / n, 3),
        "delivered_rate": round(delivered / n, 3),
    }


def main() -> None:
    m = run_eval()
    print("Beacon evaluation")
    for key in ("cases", "triage_accuracy", "pii_leak_rate", "grounded_rate", "delivered_rate"):
        print(f"  {key:16} {m[key]}")
    ok = m["triage_accuracy"] >= 0.8 and m["pii_leak_rate"] == 0.0 and m["grounded_rate"] >= 0.9
    print("  result          ", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
