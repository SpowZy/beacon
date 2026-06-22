"""Geographic routing.

Pure geometry, no model and no cost. A resident is notified when the alert is
within a severity scaled radius of their home, or inside one of their watch
zones. This mirrors the watch zone feature of a community alert app directly.
"""
from __future__ import annotations

import math

from ..config import Settings
from ..models import Coordinate, RawAlert, Recipient, Resident, RoutingResult, Severity, TriageResult


def haversine_km(a: Coordinate, b: Coordinate) -> float:
    radius = 6371.0
    p1 = math.radians(a.lat)
    p2 = math.radians(b.lat)
    dphi = math.radians(b.lat - a.lat)
    dlmb = math.radians(b.lon - a.lon)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def _radius_for(severity: Severity, settings: Settings) -> float:
    return {
        Severity.CRITICAL: settings.radius_critical_km,
        Severity.URGENT: settings.radius_urgent_km,
        Severity.ADVISORY: settings.radius_advisory_km,
        Severity.INFO: settings.radius_info_km,
    }[severity]


def route(
    alert: RawAlert,
    triage: TriageResult,
    residents: list[Resident],
    settings: Settings,
) -> RoutingResult:
    radius = _radius_for(triage.severity, settings)
    recipients: list[Recipient] = []
    for res in residents:
        d_home = haversine_km(alert.location, res.home)
        if d_home <= radius:
            recipients.append(
                Recipient(resident_id=res.id, reason="home in range", distance_km=round(d_home, 2))
            )
            continue
        for zone in res.watch_zones:
            d_zone = haversine_km(alert.location, zone.center)
            if d_zone <= zone.radius_km:
                recipients.append(
                    Recipient(resident_id=res.id, reason=f"watch zone {zone.label}", distance_km=round(d_zone, 2))
                )
                break
    return RoutingResult(recipients=recipients, radius_km=radius)
