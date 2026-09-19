# Backend

The authoritative cooking session: recipe acquisition, authentication, pairing, steps, voice, visual assistance, and profile completion.

| Start here | Why |
| --- | --- |
| [app.py](app.py) | HTTP/WebSocket routes and access checks |
| [models.py](models.py) | Structured recipe and assistant payloads |
| [recipe_engine](recipe_engine/README.md) | Search, parse, race, cache |
| [chef](chef/README.md) | Stateful guidance and perception |
| [tests](tests/README.md) | Offline evidence for behavior |

From the repository root: `python -m pip install -r backend/requirements.txt`, then `python -m uvicorn backend.app:app --reload --port 8000`. Configuration is in `.env.example`; credentials stay off the headset. Tests: `python -m pytest backend/tests -q`.

**Evidence:** 78 local tests passed on September 19, 2026. Provider and headset tests are separate. Active sessions/pairing grants are in memory; a restart loses them. See [the judge guide](../docs/judging.md).
