# Build plan

## Local checks

From the repository root, install `backend/requirements.txt`, then run:

```powershell
python -m pytest backend/tests -q
python scripts/check_unity_project.py
```

## Quest project

In Unity Hub, add the repository's `unity-client` directory. Use Unity **6000.6.2f1** with Android Build Support, SDK/NDK, and OpenJDK. Open `Assets/Ramsey/Scenes/RamseyKitchen.unity`. Packages and project settings are included; Unity regenerates Library and other caches.

The original machine's editor source was imported, retaining newer repository-side RamseyApp fixes. The embedded MCP for Unity development package includes its upstream license. Meta/Unity dependencies resolve through Unity Package Manager under their applicable terms.

Build for Android ARM64/IL2CPP. The previous native build failed due to disk space. Compilation of the imported project and a new APK are still unverified; free sufficient space and run a clean device rehearsal.

## GitHub Actions

`.github/workflows/ci.yml` runs on main pushes, pull requests, and manual dispatch. It tests the backend on Ubuntu and Windows using Python 3.13, uploads JUnit results, validates the Unity source layout, and checks browser JavaScript syntax. No provider secrets are needed.

The Unity source job checks metadata, package presence, and scene references. It does **not** compile Unity or build an APK. A licensed Unity build runner and Android tooling are follow-up work; this workflow does not pretend those are configured.

## Device acceptance

Pair a desktop-selected recipe; ask a contextual voice question; check camera permissions and monitoring controls; advance or confirm a step; reconnect without resetting state; finish and verify profile points are recorded once. Verify passthrough, audio, and anchors on real hardware.
