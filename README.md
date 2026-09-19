# Ramsey — AI Cooking Assistant

Mixed-reality cooking assistant for the Meta Quest 3S (passthrough, not
VR — you see your real kitchen with the recipe floating in it). Say or
type a dish, Ramsey finds a recipe, walks you through it step by step,
and talks back.

Target device: Quest 3S. Also runs as a plain laptop fallback (keyboard
controls, no headset needed) and a full VR fallback.

## What's here vs. what's a stub

- **Recipe engine (Tier 1)** — real, tested: JSON-LD recipe parsing,
  the parallel source race with cancellation, the result cache, and the
  offline demo recipe are all implemented and covered by tests that run
  against fakes, no API keys required.
- **Kitchen view (Tier 2)** — real: step card, ingredient checklist,
  duration auto-detection + timers, Back/Timer/Next, WebXR AR/VR/laptop
  entry points, recent recipes, `?q=`/`?demo=1` links.
- **Chef (Tier 3)** — structurally real (tool-call loop, memory,
  session state, voice endpoint) but the actual Browserbase/Stagehand/
  Backboard network calls are unverified against live keys — see "Known
  unknowns" below. Wire up real keys and confirm the request/response
  shapes before relying on it live.

## Setup

```bash
python -m venv .venv
./.venv/Scripts/activate        # or: source .venv/bin/activate on macOS/Linux
pip install -r backend/requirements.txt
cp .env.example .env             # fill in BROWSERBASE_* / BACKBOARD_* keys
```

Run the tests (no keys needed — everything hits fakes):

```bash
pytest backend/tests -q
```

Run the server:

```bash
uvicorn backend.app:app --reload --port 8000
```

Open `http://localhost:8000` for the laptop view, or `?demo=1` to skip
straight to the offline demo recipe, or `?q=shakshuka` to search on load.

On the Quest 3S, open the same URL in the Quest Browser (same Wi-Fi, or
host it publicly — see Tier 6) and tap "Enter AR on headset".

## Project layout

```
backend/
  app.py                FastAPI app: recipe, session, chat, chat/voice endpoints
  recipe_engine/         search -> race -> parse -> cache -> demo fallback
  chef/                  KitchenSession, memory, tool-call loop, Backboard client
  tests/                 pytest suite + fakes shaped like the real SDKs
frontend/
  index.html             single page, dom-overlay UI for WebXR AR
  js/                     api client, state, ui rendering, voice recorder, XR host
data/demo_recipe.json    the recipe that always works, even offline
```

## Known unknowns — verify before the demo (Tier 0)

- `BrowserbaseClient.fetch_raw` really returning usable HTML for real
  recipe sites (`backend/recipe_engine/browserbase_client.py`).
- `Stagehand.create` working off just the Browserbase key.
- The Browserbase live-view iframe being embeddable on the launcher page
  (not wired up in the frontend yet — Tier 1 nice-to-have).
- Backboard's actual request/response shape for chat + tool calls + voice
  (`backend/chef/backboard_client.py` guesses an OpenAI-style shape).
- Mic access during a passthrough session on the Quest.
- WebXR anchors/hit-test for pinning timers to real pots (Tier 7, not
  started — `xr.js` requests the `hit-test` feature but doesn't use it
  yet).

## Persona

Blunt but encouraging. Never clones or imitates the real Gordon Ramsay's
voice or likeness — enforced in the system prompt in `backend/chef/brain.py`.
