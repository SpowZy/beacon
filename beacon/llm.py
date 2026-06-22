"""Pluggable language model layer.

The default backend is a deterministic mock, so the project runs from a clean
clone with no API key, no downloaded model, and no network. Set
BEACON_LLM_BACKEND to ollama or anthropic to use a real local small model or
Claude, without touching the agents.
"""
from __future__ import annotations

from typing import Protocol

from .config import Settings


class LLM(Protocol):
    name: str

    def generate(self, system: str, user: str) -> str: ...


class MockLLM:
    """Deterministic stand in.

    It never invents facts. For the one place we use free text generation
    (polishing the outgoing message) it returns the grounded draft unchanged,
    which keeps the demo reproducible and safe.
    """

    name = "mock"

    def generate(self, system: str, user: str) -> str:
        marker = "DRAFT:"
        if marker in user:
            return user.split(marker, 1)[1].strip()
        return user.strip()


class OllamaLLM:
    name = "ollama"

    def __init__(self, model: str) -> None:
        import ollama  # imported lazily so it is not required by default

        self._client = ollama
        self._model = model

    def generate(self, system: str, user: str) -> str:
        resp = self._client.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp["message"]["content"].strip()


class AnthropicLLM:
    name = "anthropic"

    def __init__(self, model: str, api_key: str) -> None:
        from anthropic import Anthropic  # imported lazily

        self._client = Anthropic(api_key=api_key or None)
        self._model = model

    def generate(self, system: str, user: str) -> str:
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()


def get_llm(settings: Settings) -> LLM:
    backend = settings.llm_backend.lower()
    if backend == "ollama":
        return OllamaLLM(settings.ollama_model)
    if backend == "anthropic":
        return AnthropicLLM(settings.anthropic_model, settings.anthropic_api_key)
    return MockLLM()
