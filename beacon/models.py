"""Core data models.

Everything that moves through the pipeline is a typed object, so each agent has
a clear contract and the trace is easy to read and to test.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    ADVISORY = "ADVISORY"
    INFO = "INFO"


class Category(str, Enum):
    FIRE = "FIRE"
    FLOOD = "FLOOD"
    CRIME = "CRIME"
    MEDICAL = "MEDICAL"
    ROADWORKS = "ROADWORKS"
    UTILITY = "UTILITY"
    WEATHER = "WEATHER"
    COMMUNITY = "COMMUNITY"


class Coordinate(BaseModel):
    lat: float
    lon: float


class WatchZone(BaseModel):
    label: str
    center: Coordinate
    radius_km: float = 2.0


class Resident(BaseModel):
    id: str
    suburb: str
    home: Coordinate
    watch_zones: list[WatchZone] = Field(default_factory=list)


class RawAlert(BaseModel):
    id: str
    text: str
    suburb: str
    location: Coordinate
    source: str = "synthetic-feed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TriageResult(BaseModel):
    severity: Severity
    category: Category
    confidence: float
    rationale: str


class PrivacyResult(BaseModel):
    cleaned_text: str
    classification: str  # P1, P2, P3
    pii_types: list[str] = Field(default_factory=list)
    redactions: int = 0
    audit_id: str
    approved: bool = True


class Recipient(BaseModel):
    resident_id: str
    reason: str
    distance_km: float


class RoutingResult(BaseModel):
    recipients: list[Recipient] = Field(default_factory=list)
    radius_km: float = 0.0


class VerificationResult(BaseModel):
    approved: bool
    checks: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    alert_id: str
    triage: TriageResult
    privacy: PrivacyResult
    routing: RoutingResult
    message: str
    verification: VerificationResult
    status: str
    trace: list[str] = Field(default_factory=list)
