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
