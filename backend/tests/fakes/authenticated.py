from fastapi.testclient import TestClient
from backend import app as app_module
from backend.profiles import ProfileStore
from backend.tests.fakes.fake_firestore import FakeFirestoreClient


def signed_client(monkeypatch, uid="cook-test"):
    async def verify(token):
        return {"sub": token, "email": "test@example.com", "name": "Test cook"}
    monkeypatch.setattr(app_module.config, "FIREBASE_PROJECT_ID", "test-project")
    monkeypatch.setattr(app_module, "verify_firebase_id_token", verify)
    monkeypatch.setattr(app_module, "_profiles", ProfileStore(FakeFirestoreClient()))
    client = TestClient(app_module.app)
    assert client.post('/api/auth/firebase', json={"idToken": uid}).status_code == 200
    return client
