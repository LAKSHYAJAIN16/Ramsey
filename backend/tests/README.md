# Backend verification

Run `python -m pytest backend/tests -q` from the repository root. Latest local result: **78 passed**, September 19, 2026; two dependency deprecation warnings.

| Evidence | Tests |
| --- | --- |
| Recipe parsing and retrieval | `test_parser.py`, `test_browserbase_search.py`, `test_race.py`, `test_cache_and_service.py` |
| Identity and pairing | `test_auth_routes.py`, `test_pairing_auth.py`, `test_profiles.py` |
| Cooking state and assistance | `test_session.py`, `test_step_assist.py`, `test_quest_session.py` |
| Audio and perception contracts | `test_quest_audio.py`, `test_voice_transcript.py`, `test_vision.py`, `test_vision_routes.py` |

[Fakes](fakes/README.md) isolate external services. Passing tests establish application logic under those fixtures, not real image recognition, provider availability, or Quest behavior. GitHub Actions also runs this suite on Ubuntu and Windows; see [CI details](../../.github/README.md).
