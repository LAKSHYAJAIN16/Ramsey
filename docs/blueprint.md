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

Provider credentials stay on the backend. Quest needs network access to that backend for online features; untethered does not mean that Python runs on the headset. See [setup notes](../SETUP_NOTES.md) for service details.

The imported Unity project retains the repository's newer `RamseyApp.cs` connection-loss and timer-reset fixes. The external working copy at `C:/Users/laksh/Ramsey` is not automatically synchronized.
