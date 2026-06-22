"""Verification agent (the trust gate).

Nothing reaches residents until it passes here. We re-check for leaked PII,
confirm the message is grounded in the cleaned alert, and confirm the routing
makes sense for the severity. This is the habit carried over from evaluating
frontier models: a confident wrong message is the real risk in a safety
product, so it gets blocked.
"""
from __future__ import annotations

import re

from .agents.privacy import _EMAIL, _PHONE
from .models import PrivacyResult, RoutingResult, Severity, TriageResult, VerificationResult


def verify(
    triage: TriageResult,
    privacy: PrivacyResult,
    routing: RoutingResult,
    message: str,
) -> VerificationResult:
    checks: list[str] = []
    issues: list[str] = []

    if _EMAIL.search(message) or _PHONE.search(message):
        issues.append("personal identifier present in outgoing message")
    else:
        checks.append("no PII in outgoing message")

    if privacy.classification == "P2":
        checks.append("payload classified P2")
    else:
        issues.append(f"payload classified {privacy.classification}, not safe to send")

    if triage.severity in (Severity.CRITICAL, Severity.URGENT) and not routing.recipients:
        issues.append("urgent alert with no recipients")
    else:
        checks.append("recipients consistent with severity")

    msg_numbers = set(re.findall(r"\d{2,}", message))
    src_numbers = set(re.findall(r"\d{2,}", privacy.cleaned_text))
    if msg_numbers - src_numbers:
        issues.append("message contains numbers not found in the source")
    else:
        checks.append("message grounded in source facts")

    return VerificationResult(approved=not issues, checks=checks, issues=issues)
