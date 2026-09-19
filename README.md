# Ramsey

A mixed-reality cooking companion for Meta Quest. Choose a recipe on desktop, then bring its steps and a conversational chef into your kitchen. Python owns the cooking session; Quest supplies the spatial interface, voice input and camera observations.

## What is in this repo

| Path | What |
| --- | --- |
| [unity-client](unity-client/README.md) | Complete Unity 6 Quest project: Assets, Packages, ProjectSettings |
| [frontend](frontend/README.md) | Desktop sign-in, recipe selection and session controls |
| [homepage](homepage/README.md) | Project landing page |
| [backend](backend/README.md) | FastAPI server: identity, pairing, recipes, sessions and profiles |
| [backend/recipe_engine](backend/recipe_engine/README.md) | Recipe acquisition, parsing, source race and cache |
| [backend/chef](backend/chef/README.md) | Conversation, timers, visual assistance and progression rules |
| [backend/tests](backend/tests/README.md) | Offline behavior tests with fake external services |
| [data](data/README.md) | Bundled development recipe |
| [docs](docs/README.md) | Judge guide, blueprint, team plan, build plan and critique |
| [infra](infra/README.md) | Local setup, container and hosting instructions |
| [scripts](scripts/README.md) | Portable Unity source checks |
| [.github](.github/README.md) | Backend tests and source validation workflows |

## Two ideas hold it together

1. **One cooking session.** Desktop selects the recipe, Python owns its state, and Quest displays the same steps. Questions, timers and observations belong to that session.
2. **Help beside the task.** Instructions and conversational help belong in the kitchen. The next spatial milestone is automatically locating equipment through CV and measured depth; a floating panel alone is not that experience.

## Run it

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item .env.example .env         # configure identity and provider access
.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --port 8000
.venv\Scripts\python.exe -m pytest backend/tests -q
python scripts/check_unity_project.py
```

Open the homepage at `http://localhost:8000`, or the desktop companion at `/app/`. Add `unity-client/` in Unity Hub using Unity **6000.6.2f1** with Android Build Support. Online Quest features require a reachable backend.

Useful: [judge route](docs/judging.md), [deck](deck.md), [Quest controls/build](unity-client/README.md), [hosting](infra/README.md), [CI](.github/README.md).

## Honest labels

**Verified locally:** 78 backend tests, browser JavaScript syntax and Unity source-layout checks passed on September 19, 2026. Tests use fake providers. These results predate the new portrait/lifecycle changes.

**Implemented, not verified end to end:** recipe/session logic, sign-in and pairing, voice transport, sampled camera assistance, guarded step progression, plating feedback and the pixel-textured summon-only assistant. The prior APK build failed from disk space; no successful headset cooking session is claimed.

**Vision, not built:** automatic 3D equipment localization and reliable moving-object tracking. Live image/voice provider behavior also needs validation. No certified hazard detection or automatic emergency calling is claimed.

Credits and licences: [SOURCES.md](SOURCES.md). Codex log: [CODEX_LOG.md](CODEX_LOG.md).
