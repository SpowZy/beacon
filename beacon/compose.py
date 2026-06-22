"""Message composition.

We build a grounded draft from the cleaned alert and the retrieved guidance,
then optionally let the configured model polish the wording. With the mock
backend the grounded draft is returned unchanged, so nothing is ever invented.
"""
from __future__ import annotations

from .llm import LLM
from .models import PrivacyResult, RawAlert, TriageResult
from .retrieval import retrieve

_SYSTEM = (
    "You rewrite a community safety notice to be calm, clear and short. "
    "Use only the facts in the draft. Do not add names, numbers or locations."
)


def compose_message(alert: RawAlert, triage: TriageResult, privacy: PrivacyResult, llm: LLM) -> str:
    guidance = retrieve(triage.category, privacy.cleaned_text, k=1)
    guidance_line = guidance[0] if guidance else "Follow local guidance."
    draft = (
        f"[{triage.severity.value}] {triage.category.value} near {alert.suburb}. "
        f"{privacy.cleaned_text} {guidance_line}"
    )
    if llm.name == "mock":
        return draft
    user = f"Rewrite the draft and keep every fact.\nDRAFT:\n{draft}"
    return llm.generate(_SYSTEM, user)
