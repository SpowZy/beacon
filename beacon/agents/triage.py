"""Triage agent: assign a severity and a category.

The classifier is deterministic by default, so the demo is stable and free. The
deterministic result is the source of truth. A model can be routed in to add a
rationale, but it never overrides the safety decision.
"""
from __future__ import annotations

from ..models import Category, RawAlert, Severity, TriageResult

_CATEGORY_KEYWORDS: list[tuple[Category, tuple[str, ...]]] = [
    (Category.FIRE, ("fire", "smoke", "blaze")),
    (Category.FLOOD, ("flood", "water main", "flooding")),
    (Category.MEDICAL, ("medical", "ambulance", "injured", "cardiac")),
    (Category.CRIME, ("robbery", "burglary", "assault", "theft", "suspect")),
    (Category.ROADWORKS, ("roadworks", "road works", "detour", "lane closure")),
    (Category.UTILITY, ("power outage", "outage", "gas leak", "electricity")),
    (Category.WEATHER, ("storm", "hail", "heatwave", "high wind")),
]

_CRITICAL = ("fire", "gas leak", "cardiac", "explosion", "trapped")
_URGENT = ("flood", "water main", "assault", "robbery", "outage")


def triage(alert: RawAlert) -> TriageResult:
    text = alert.text.lower()

    category = Category.COMMUNITY
    for cat, keys in _CATEGORY_KEYWORDS:
        if any(k in text for k in keys):
            category = cat
            break

    if any(k in text for k in _CRITICAL):
        severity = Severity.CRITICAL
    elif any(k in text for k in _URGENT):
        severity = Severity.URGENT
    elif "planned" in text or "expect" in text:
        severity = Severity.ADVISORY
    else:
        severity = Severity.INFO

    matched = sum(1 for _, keys in _CATEGORY_KEYWORDS for k in keys if k in text)
    confidence = min(0.55 + 0.15 * matched, 0.98)
    rationale = f"matched category {category.value} and severity {severity.value} from the alert wording"
    return TriageResult(
        severity=severity,
        category=category,
        confidence=round(confidence, 2),
        rationale=rationale,
    )
