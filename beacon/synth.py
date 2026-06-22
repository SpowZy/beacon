"""Synthetic data.

Everything here is fake and clearly labelled as such. The point is a clone and
run demo with zero external data and full control over edge cases. The README
explains how to swap this module for a real open data ingestion path.
"""
from __future__ import annotations

import random

from .models import Coordinate, RawAlert, Resident, WatchZone

# A few real suburb centres so distances feel natural. The residents are fake.
SUBURBS: dict[str, Coordinate] = {
    "Palo Alto": Coordinate(lat=37.4419, lon=-122.1430),
    "Mountain View": Coordinate(lat=37.3861, lon=-122.0839),
    "Menlo Park": Coordinate(lat=37.4530, lon=-122.1817),
}


def _jitter(base: Coordinate, rng: random.Random, spread: float = 0.02) -> Coordinate:
    return Coordinate(
        lat=base.lat + rng.uniform(-spread, spread),
        lon=base.lon + rng.uniform(-spread, spread),
    )


def generate_residents(n: int = 30, seed: int = 7) -> list[Resident]:
    rng = random.Random(seed)
    suburbs = list(SUBURBS.items())
    residents: list[Resident] = []
    for i in range(n):
        suburb, centre = suburbs[i % len(suburbs)]
        home = _jitter(centre, rng)
        zones: list[WatchZone] = []
        if rng.random() < 0.4:
            other_suburb, other_centre = suburbs[(i + 1) % len(suburbs)]
            zones.append(
                WatchZone(label=f"watch:{other_suburb}", center=_jitter(other_centre, rng), radius_km=2.5)
            )
        residents.append(Resident(id=f"r{i:03d}", suburb=suburb, home=home, watch_zones=zones))
    return residents


def scenario_alerts() -> list[RawAlert]:
    """A curated set, including an edge case that carries personal details."""
    pa = SUBURBS["Palo Alto"]
    mv = SUBURBS["Mountain View"]
    mp = SUBURBS["Menlo Park"]
    return [
        RawAlert(
            id="a001",
            suburb="Palo Alto",
            location=Coordinate(lat=pa.lat + 0.005, lon=pa.lon - 0.004),
            text=(
                "Structure fire reported on Hamilton Avenue. Crews on scene. "
                "Caller Sarah Jensen left contact 650-555-0199 and email sarah.jensen@example.com."
            ),
        ),
        RawAlert(
            id="a002",
            suburb="Mountain View",
            location=Coordinate(lat=mv.lat - 0.003, lon=mv.lon + 0.006),
            text="Water main break causing flooding near Castro Street. Avoid the area.",
        ),
        RawAlert(
            id="a003",
            suburb="Menlo Park",
            location=Coordinate(lat=mp.lat, lon=mp.lon),
            text="Planned roadworks on Santa Cruz Avenue this weekend. Expect short delays.",
        ),
    ]
