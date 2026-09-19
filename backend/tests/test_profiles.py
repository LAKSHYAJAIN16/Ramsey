from backend.profiles import ProfileStore, rank_for_xp


def test_google_profile_is_persisted_and_ranked(tmp_path):
    store = ProfileStore(tmp_path / "profiles.sqlite3")
    profile = store.upsert_google_user("google-123", "cook@example.com", "Cook", None)

    assert profile["rank"] == "Prep Cook"
    saved = profile
    for _ in range(5):
        saved = store.add_completed_meal("google-123", 400)

    assert saved["xp"] == 100
    assert saved["rank"] == "Line Cook"
    assert saved["calories"] == 2000


def test_rank_thresholds():
    assert rank_for_xp(0) == "Prep Cook"
    assert rank_for_xp(1400) == "Head Chef"
