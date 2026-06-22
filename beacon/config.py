"""Runtime configuration.

Everything is environment driven so the same code runs three ways: a
deterministic mock (default, zero cost), a local Ollama model, or the
Anthropic API. Prefix every variable with BEACON_, for example
BEACON_LLM_BACKEND=ollama.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BEACON_", env_file=".env", extra="ignore")

    # mock | ollama | anthropic
    llm_backend: str = "mock"
    ollama_model: str = "llama3.2"
    anthropic_model: str = "claude-opus-4-8"
    anthropic_api_key: str = ""

    # routing radii in km, selected by severity
    radius_critical_km: float = 5.0
    radius_urgent_km: float = 3.0
    radius_advisory_km: float = 1.5
    radius_info_km: float = 0.8

    # differential privacy budget for community level aggregates
    dp_epsilon: float = 1.0


def load_settings() -> Settings:
    return Settings()
