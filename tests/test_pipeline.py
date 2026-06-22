from beacon.agents.privacy import dp_count, enforce
from beacon.agents.routing import haversine_km, route
from beacon.agents.triage import triage
from beacon.config import Settings
from beacon.graph import run_pipeline
from beacon.models import (
    Category,
    Coordinate,
    PrivacyResult,
    RawAlert,
    Recipient,
    Resident,
    RoutingResult,
    Severity,
    TriageResult,
)
from beacon.synth import generate_residents, scenario_alerts
from beacon.verify import verify


def _alert_with_pii() -> RawAlert:
    return RawAlert(
        id="t1",
        suburb="Palo Alto",
        location=Coordinate(lat=37.44, lon=-122.14),
        text="Fire on Main Street. Caller Jane Doe phone 650-555-0123 email jane@example.com.",
    )


def test_privacy_redacts_pii():
    res = enforce(_alert_with_pii())
    assert "jane@example.com" not in res.cleaned_text
    assert "650-555-0123" not in res.cleaned_text
    assert res.classification == "P2"
    assert res.redactions >= 2


def test_triage_detects_fire_as_critical():
    t = triage(_alert_with_pii())
    assert t.category == Category.FIRE
    assert t.severity == Severity.CRITICAL


def test_routing_includes_near_and_excludes_far():
    settings = Settings()
    near = Resident(id="near", suburb="Palo Alto", home=Coordinate(lat=37.441, lon=-122.141))
    far = Resident(id="far", suburb="Far", home=Coordinate(lat=38.5, lon=-121.0))
    alert = _alert_with_pii()
    t = TriageResult(severity=Severity.CRITICAL, category=Category.FIRE, confidence=0.9, rationale="x")
    result = route(alert, t, [near, far], settings)
    ids = {rec.resident_id for rec in result.recipients}
    assert "near" in ids
    assert "far" not in ids


def test_haversine_is_small_for_close_points():
    a = Coordinate(lat=37.44, lon=-122.14)
    b = Coordinate(lat=37.441, lon=-122.141)
    assert haversine_km(a, b) < 0.5


def test_verify_blocks_leaked_pii():
    t = TriageResult(severity=Severity.URGENT, category=Category.FIRE, confidence=0.9, rationale="x")
    p = PrivacyResult(cleaned_text="clean", classification="P2", audit_id="a")
    routing = RoutingResult(recipients=[Recipient(resident_id="r", reason="home", distance_km=1.0)])
    bad = verify(t, p, routing, "call 650-555-0123 now")
    assert not bad.approved


def test_dp_count_is_non_negative():
    assert dp_count(10, epsilon=1.0) >= 0.0


def test_end_to_end_scenario():
    settings = Settings()
    residents = generate_residents(n=30, seed=7)
    results = [run_pipeline(a, residents, settings) for a in scenario_alerts()]
    assert all(r.status in {"delivered", "held"} for r in results)
    fire = next(r for r in results if r.alert_id == "a001")
    assert fire.privacy.classification == "P2"
    assert "@" not in fire.message
    assert fire.status == "delivered"
