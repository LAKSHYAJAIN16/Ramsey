from backend.profiles import ProfileStore, rank_for_xp
from backend.tests.fakes.fake_firestore import FakeFirestoreClient


def test_firebase_profile_is_persisted_and_ranked():
    store = ProfileStore(FakeFirestoreClient())
    profile = store.upsert_firebase_user("firebase-123", "cook@example.com", "Cook", None)

    assert profile["rank"] == "Prep Cook"
    saved = profile
    for _ in range(5):
        saved = store.add_completed_meal("firebase-123", 400)

    assert saved["xp"] == 100
    assert saved["rank"] == "Line Cook"
    assert saved["calories"] == 2000


def test_rank_thresholds():
    assert rank_for_xp(0) == "Prep Cook"
    assert rank_for_xp(1400) == "Head Chef"


def test_completion_unlock_survives_reload_and_retry():
    client = FakeFirestoreClient()
    store = ProfileStore(client)
    store.upsert_firebase_user("cook", "cook@example.com", "Cook", None)
    store.add_completed_meal("cook", 0, "session-one", dish="Chickpea bowl")
    store.add_completed_meal("cook", 0, "session-one", dish="Chickpea bowl")
    saved = ProfileStore(client).get("cook")
    assert saved["xp"] == 20
    assert saved["completed_dishes"] == ["Chickpea bowl"]
    assert saved["daily_goal_complete"] is True
    assert saved["next_rank"] == {"name": "Line Cook", "xp": 100}


def test_old_streak_is_not_displayed_as_active():
    saved = ProfileStore._serialize({"xp": 100, "streak": 9, "last_cooked_on": "2000-01-01"})
    assert saved["streak"] == 0
    assert saved["daily_goal_complete"] is False
