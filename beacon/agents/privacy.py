"""Privacy and governance agent (the DARS layer).

Before anything leaves the system it is stripped of personal identifiers and
classified. P2 means non sensitive, community level, no PII. If anything
sensitive survives, we mark it P1 and hold it. This logic is deterministic on
purpose: privacy rules you can read and test beat a model you have to trust.
"""
from __future__ import annotations

import hashlib
import math
import random
import re

from ..models import PrivacyResult, RawAlert

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
_NAMED_CONTACT = re.compile(
    r"\b(?:caller|contact|victim|resident|name)\b[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)",
    re.IGNORECASE,
)


def _audit_id(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"audit_{digest[:12]}"


def enforce(alert: RawAlert) -> PrivacyResult:
    text = alert.text
    pii_types: list[str] = []
    redactions = 0

    names = _NAMED_CONTACT.findall(text)
    for full in names:
        text = text.replace(full, "[NAME]")
        redactions += 1
    if names:
        pii_types.append("name")

    if _EMAIL.search(text):
        text, n = _EMAIL.subn("[EMAIL]", text)
        redactions += n
        pii_types.append("email")

    if _PHONE.search(text):
        text, n = _PHONE.subn("[PHONE]", text)
        redactions += n
        pii_types.append("phone")

    leftover = bool(_EMAIL.search(text) or _PHONE.search(text))
    classification = "P1" if leftover else "P2"

    return PrivacyResult(
        cleaned_text=text.strip(),
        classification=classification,
        pii_types=pii_types,
        redactions=redactions,
        audit_id=_audit_id(alert.text),
        approved=not leftover,
    )


def dp_count(true_count: int, epsilon: float = 1.0, rng: random.Random | None = None) -> float:
    """Laplace mechanism for a differentially private count.

    Used when we publish community level aggregates, so a single household can
    never be reverse engineered from a released number. This is the mechanism
    used in production by the US Census Bureau and others.
    """
    rng = rng or random.Random()
    scale = 1.0 / max(epsilon, 1e-6)
    u = rng.random() - 0.5
    noise = -scale * math.copysign(1.0, u) * math.log(1.0 - 2.0 * abs(u))
    return max(0.0, true_count + noise)
