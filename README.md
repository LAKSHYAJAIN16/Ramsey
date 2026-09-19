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
- **Chef (Tier 3)** — real, against documented (not guessed) API shapes
  for both Browserbase Fetch and Backboard's thread/run/tool-call flow —
  see "API shapes used" below for what's confirmed by docs vs. what's
  still only a good guess. None of it has run against a live key yet.

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

## API shapes used

Confirmed against current docs (Sept 2026), not guessed:

- **Browserbase Fetch** — `POST https://api.browserbase.com/v1/fetch`,
  header `X-BB-API-Key`, body `{"url", "format": "raw"|"markdown"|"json"}`,
  response has the page HTML in `content`. `format="raw"` (the default)
  is confirmed to return real page HTML — resolves known-unknown #1.
  [docs.browserbase.com/platform/fetch/overview](https://docs.browserbase.com/platform/fetch/overview)
- **Stagehand Model Gateway** — `AsyncStagehand(browserbase_api_key=...)`
  needs no separate model-provider key; Model Gateway routes model calls
  through the one Browserbase key. Resolves known-unknown #2.
  [browserbase.com/blog/model-gateway](https://www.browserbase.com/blog/model-gateway),
  [docs.stagehand.dev/v3/sdk/python](https://docs.stagehand.dev/v3/sdk/python)
- **Backboard** — `https://app.backboard.io/api`, header `X-API-Key`,
  `POST /threads/messages` to talk, `POST /threads/tool-outputs` to
  answer a tool call. It's an Assistants-style thread/run API: a turn
  either `COMPLETED`s with text or comes back `REQUIRES_ACTION` with
  `tool_calls` to run locally — `chef/brain.py`'s loop is built around
  that, not a client-side chat-completions messages list.
  [docs.backboard.io](https://docs.backboard.io/),
  tool-calls format confirmed at docs.backboard.io/sdk/tool-calls

Still open — verify before the demo (Tier 0):

- Whether it's `client.sessions.start(...)` or `.create(...)` on the
  Stagehand session — doc mirrors disagreed; `browserbase_client.py`
  uses `.start`.
- Backboard's voice STT/TTS provider/model naming (`app.py`'s
  `/api/chat/voice` guesses `{"provider": "elevenlabs"}` for both).
- The Browserbase live-view iframe being embeddable on the launcher page
  (not wired up in the frontend yet — Tier 1 nice-to-have).
- Mic access during a passthrough session on the Quest.
- WebXR anchors/hit-test for pinning timers to real pots (Tier 7, not
  started — `xr.js` requests the `hit-test` feature but doesn't use it
  yet).

## Persona

Blunt but encouraging. Never clones or imitates the real Gordon Ramsay's
voice or likeness — enforced in the system prompt in `backend/chef/brain.py`.
