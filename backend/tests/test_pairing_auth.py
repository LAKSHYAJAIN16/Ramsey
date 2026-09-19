from fastapi.testclient import TestClient
from backend import app as app_module
from backend.tests.fakes.authenticated import signed_client


def test_sign_in_required_for_recipe_and_voice():
    client = TestClient(app_module.app)
    assert client.get('/api/recipe?dish=demo&demo=true').status_code == 401
    assert client.get('/api/session/someone-elses').status_code == 401
    assert client.post('/api/chat', json={'session_id': 'x', 'text': 'hello'}).status_code == 401


def test_pairing_joins_without_reset_and_restricts_access(monkeypatch):
    monkeypatch.setattr(app_module, '_sessions', {})
    desktop = signed_client(monkeypatch, 'alice')
    assert desktop.get('/api/recipe?dish=demo&demo=true&session_id=alice-session').status_code == 200
    desktop.post('/api/session/alice-session/action', json={'action': 'next'})
    code = desktop.post('/api/session/alice-session/pair').json()['code']
    quest = TestClient(app_module.app)
    paired = quest.post('/api/pair', json={'code': code}).json()
    assert paired['state']['step_index'] == 1
    assert quest.post('/api/pair', json={'code': code}).status_code == 404
    quest.headers['Authorization'] = 'Bearer ' + paired['token']
    assert quest.get('/api/session/alice-session').status_code == 200
    assert quest.get('/api/session/different').status_code == 403
    assert quest.post('/api/session/alice-session/pair').status_code == 403
    desktop.post('/api/auth/logout')
    assert quest.get('/api/session/alice-session').status_code == 401


def test_second_user_cannot_read_or_replace_first_users_recipe(monkeypatch):
    alice = signed_client(monkeypatch, 'alice')
    alice.get('/api/recipe?dish=demo&demo=true&session_id=private')
    bob = signed_client(monkeypatch, 'bob')
    assert bob.get('/api/session/private').status_code == 403
    assert bob.get('/api/recipe?dish=demo&demo=true&session_id=private').status_code == 403


def test_completed_recipe_saves_once_to_its_firebase_profile(monkeypatch):
    client = signed_client(monkeypatch, 'owner')
    recipe = dict(title='Plated sandwich', source_url='', ingredients=['bread'], steps=['Place sandwich on plate'])
    client.post('/api/session/one/recipe', json=recipe)
    for _ in range(3):
        state = client.post('/api/session/one/action', json={'action': 'complete'}).json()
        assert state['completed'] and state['profile_saved']
    profile = client.get('/api/me').json()['profile']
    assert profile['xp'] == 20 and profile['meals'] == 1
