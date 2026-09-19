"""Route-level smoke tests for the endpoints the Unity client calls:
confirms they're actually wired into the FastAPI app (right method, right
path, right response shape end to end), not just that the underlying
functions work in isolation (test_vision.py / test_kitchen_spots.py cover
that). Same TestClient + monkeypatched Backboard pattern as
test_auth_routes.py.
"""
from fastapi.testclient import TestClient

from backend import app as app_module
from backend.tests.fakes.authenticated import signed_client


async def _fake_analyze_image(image_bytes, filename, prompt):
    if "surface" in prompt or "label" in prompt.lower():
        return {"content": '{"label": "Stove", "confidence": "high"}'}
    return {"content": '{"objects": [], "stations": [{"vessel": "pan", "contents": ["eggs"], "doneness": "done", "matches_expected_step": true, "note": "Looks ready."}]}'}


def _client(monkeypatch):
    monkeypatch.setattr(app_module._backboard, "analyze_image", _fake_analyze_image)
    client = signed_client(monkeypatch, "k1")
    client.get('/api/recipe', params={'session_id': 'vision-test', 'dish': 'demo', 'demo': True})
    return client


def test_identify_spot_route(monkeypatch):
    client = _client(monkeypatch)
    response = client.post("/api/vision/identify-spot", files={"photo": ("spot.jpg", b"fake-bytes", "image/jpeg")})
    assert response.status_code == 200
    assert response.json()["label"] == "Stove"


def test_check_cooking_route(monkeypatch):
    client = _client(monkeypatch)
    response = client.post(
        "/api/vision/check-cooking",
        data={"session_id": "vision-test"},
        files={"photo": ("dish.jpg", b"fake-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["stations"][0]["doneness"] == "done"


def test_kitchen_spots_routes_round_trip(monkeypatch):
    client = _client(monkeypatch)
    created = client.post("/api/kitchen/spots", json={"kitchen_id": "k1", "label": "Counter"})
    assert created.status_code == 200
    spot_id = created.json()["id"]

    listed = client.get("/api/kitchen/spots", params={"kitchen_id": "k1"})
    assert listed.json() == [{"id": spot_id, "label": "Counter"}]

    deleted = client.delete(f"/api/kitchen/spots/{spot_id}", params={"kitchen_id": "k1"})
    assert deleted.status_code == 200
    assert client.get("/api/kitchen/spots", params={"kitchen_id": "k1"}).json() == []
