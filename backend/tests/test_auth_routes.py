"""Drives the real HTTP routes end to end: sign in, log a meal, confirm the
write actually lands in the profile store and survives a fresh read - not
just that ProfileStore's methods work in isolation (test_profiles.py covers
that). Uses FakeFirestoreClient, not a real Firebase project.
"""
from fastapi.testclient import TestClient

from backend import app as app_module
from backend.profiles import ProfileStore
from backend.tests.fakes.fake_firestore import FakeFirestoreClient


async def _fake_verify(id_token: str) -> dict:
    return {"sub": "uid-123", "email": "cook@example.com", "name": "Cook", "picture": None}


def _client_with_fake_store(monkeypatch):
    store = ProfileStore(FakeFirestoreClient())
    monkeypatch.setattr(app_module, "_profiles", store)
    monkeypatch.setattr(app_module, "verify_firebase_id_token", _fake_verify)
    return TestClient(app_module.app), store


def test_sign_in_creates_a_persisted_profile(monkeypatch):
    client, store = _client_with_fake_store(monkeypatch)

    response = client.post("/api/auth/firebase", json={"idToken": "fake"})
    assert response.status_code == 200
    body = response.json()
    assert body["authenticated"] is True
    assert body["profile"]["email"] == "cook@example.com"

    # Not just returned in the response - actually saved under that uid.
    assert store.get("uid-123")["email"] == "cook@example.com"


def test_logged_meal_persists_across_requests(monkeypatch):
    client, store = _client_with_fake_store(monkeypatch)
    client.post("/api/auth/firebase", json={"idToken": "fake"})

    response = client.post("/api/me/progress", json={"calories": 450})
    assert response.status_code == 200
    assert response.json()["xp"] == 20
    assert response.json()["meals"] == 1

    # A brand new request (same session cookie) sees the same saved state -
    # this is what "signed in on your phone, still there on your laptop"
    # actually depends on: the stored document, not anything held in memory.
    me = client.get("/api/me")
    assert me.json()["profile"]["xp"] == 20
    assert me.json()["profile"]["calories"] == 450
    assert store.get("uid-123")["meals"] == 1


def test_progress_requires_sign_in(monkeypatch):
    client, _ = _client_with_fake_store(monkeypatch)
    response = client.post("/api/me/progress", json={"calories": 450})
    assert response.status_code == 401
