from fastapi.testclient import TestClient

from beacon.api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_alert_redacts_and_delivers():
    r = client.post(
        "/alert",
        json={
            "id": "x1",
            "text": "Fire on Oak Street. Caller John Smith 650-555-0000.",
            "suburb": "Palo Alto",
            "lat": 37.4419,
            "lon": -122.143,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "650-555-0000" not in body["message"]
    assert body["privacy"]["classification"] == "P2"
    assert body["status"] == "delivered"


def test_community_insight_is_private():
    r = client.get("/community/Palo Alto/insight")
    assert r.status_code == 200
    body = r.json()
    assert body["classification"] == "P2"
    assert body["value_dp"] >= 0
