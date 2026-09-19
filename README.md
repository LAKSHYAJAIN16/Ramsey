# Ramsey

A mixed-reality cooking companion. Pick a recipe on desktop; bring its steps and a conversational chef into your kitchen on Quest.

**The pitch:** Recipes tell you what to do. Ramsey is designed to help you do it: choose a recipe on your laptop, then use Quest for hands-free instructions and a voice assistant that knows your current step. Camera-based progress checks and timely cooking help are the next experience to validate on hardware.

[Judge guide](docs/judging.md) · [Deck](deck.md) · [Blueprint](docs/blueprint.md) · [Build plan](docs/build-plan.md) · [Critique](docs/critique.md)

## What is in this repo

| Path | What |
| --- | --- |
| [backend](backend/README.md) | Python API, identity, pairing, cooking sessions and profiles |
| [backend/recipe_engine](backend/recipe_engine/README.md) | Search, raw-content parsing, ordered recipe steps and cache |
| [backend/chef](backend/chef/README.md) | Conversation, timers, visual assistance and progression rules |
| [backend/tests](backend/tests/README.md) | Offline evidence: 78 passing local tests |
| [unity-client](unity-client/README.md) | Complete Unity 6 Quest project: Assets, Packages, ProjectSettings |
| [frontend](frontend/README.md) | Signed-in desktop recipe/session companion |
| [homepage](homepage/README.md) | Project introduction and entry point |
| [data](data/README.md) | Bundled development recipe |
| [docs](docs/README.md) | Judge guide, blueprint, team plan, build plan and critique |
| [scripts](scripts/README.md) | Portable Unity project checks |
| [.github](.github/README.md) | Backend tests and source validation in GitHub Actions |

## Two ideas hold it together

**One cooking session.** Desktop selects the recipe, Python owns the steps and logic, and Quest presents guidance in passthrough. Recipe selection, voice questions, timers, and observations should refer to that same session.

**Help belongs beside the task.** The intended assistant knows the current step and the equipment around you. Spatial guidance, spoken help, and visual feedback should reduce the need to stop cooking and consult a screen. Unknown observations are not proof that a step is done.

## Run it

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item .env.example .env             # fill in provider/auth configuration
.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --port 8000
```

Open [the homepage](http://localhost:8000) or [the desktop companion](http://localhost:8000/app/). Provider-backed features require configured services; an offline recipe is included for development.

```powershell
.venv\Scripts\python.exe -m pytest backend/tests -q
```

Useful: [Quest build and controls](unity-client/README.md), [backend setup and API notes](SETUP_NOTES.md), [roadmap](TODO.md). Add `unity-client/` directly in Unity Hub; the complete source project is included. Online Quest features need a reachable backend even when the headset is untethered.

## Honest labels

**Implemented in the repository:** recipe parsing/search and session logic, desktop UI and homepage, identity/profile and pairing routes, chef/vision integration code, step/plating assistance, and Unity client source. This is a code inventory, not a claim of complete live operation.

**Verified locally on September 19, 2026:** 78 backend tests pass; Unity project structure, asset metadata and scene references pass; browser JavaScript syntax passes. Provider responses are faked in automated tests. Earlier Unity compilation notes refer to the previous client, not a new build of this imported project.

**Not verified end to end:** headset pairing, passthrough, voice, camera, spatial anchors, and the complete cooking loop. The last recorded APK build failed from insufficient disk space; earlier live AI tests encountered provider billing restrictions.

**Product goals requiring further integration/validation:** continuous monitoring, equipment tracking, double-table-tap assistant activation, evidence-based automatic progression, and polished on-headset plating guidance. No certified hazard detection or automatic emergency calling is claimed.

Sources and credits: [SOURCES.md](SOURCES.md). Development record: [CODEX_LOG.md](CODEX_LOG.md).
