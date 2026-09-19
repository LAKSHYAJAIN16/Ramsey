from fastapi.testclient import TestClient
from backend import app as app_module
from backend.tests.fakes.authenticated import signed_client


def test_quest_recipe_and_actions_share_server_state(monkeypatch):
    monkeypatch.setattr(app_module, "_sessions", {})
    client = signed_client(monkeypatch)
    recipe = {"title": "Sandwich", "source_url": "", "ingredients": ["Bread", "Cheese"], "steps": ["Lay out bread", "Add cheese"]}
    response = client.post("/api/session/quest-test/recipe", json=recipe)
    assert response.status_code == 200
    assert response.json()["current_step"] == "Lay out bread"
    assert client.post("/api/session/quest-test/action", json={"action": "next"}).json()["step_index"] == 1
    assert client.get("/api/session/quest-test").json()["current_step"] == "Add cheese"


def test_quest_rejects_recipe_without_usable_steps(monkeypatch):
    monkeypatch.setattr(app_module, "_sessions", {})
    client = signed_client(monkeypatch)
    for steps in ([], ["   "]):
        response = client.post("/api/session/quest-test/recipe", json={"title": "Sandwich", "source_url": "", "ingredients": [], "steps": steps})
        assert response.status_code == 422
    assert client.get("/api/session/quest-test").status_code == 404
