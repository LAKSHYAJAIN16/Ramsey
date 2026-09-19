# Blueprint

The desktop chooses a recipe and authenticates the user. Python owns recipe steps, session state, timers, AI calls, and profile updates. Quest pairs to a session and provides spatial UI, microphone audio, camera observations, and user input.

| Path | Responsibility |
| --- | --- |
| `backend/` | FastAPI API, recipe engine, chef, identity/profile/session logic |
| `frontend/` | Desktop recipe and session companion |
| `homepage/` | Project landing page |
| `unity-client/` | Openable Unity project: Assets, Packages, ProjectSettings |
| `data/` | Bundled recipe fixture |
| `scripts/` | Repository validation |
| `.github/workflows/` | Offline tests and source checks |

Provider credentials stay on the backend. Quest needs network access to that backend for online features; untethered does not mean that Python runs on the headset. See [setup notes](../infra/README.md) for service details.

The checked-in Unity project is the source of record. Local Editor copies must be synchronized before testing; machine-specific locations are intentionally omitted.
