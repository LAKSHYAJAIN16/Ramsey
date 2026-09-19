# Quest client — openable Unity project

This directory includes **Assets, Packages, and ProjectSettings**. In Unity Hub, add this directory and open it with **Unity 6000.6.2f1** plus Android Build Support, SDK/NDK and OpenJDK. Unity regenerates its ignored caches.

Open `Assets/Ramsey/Scenes/RamseyKitchen.unity`. Build for Android ARM64/IL2CPP. The backend URL is configured at runtime; provider API keys stay on Python.

| Start here | Purpose |
| --- | --- |
| [Ramsey assets](Assets/Ramsey/README.md) | App scripts, scene, editor setup, resources |
| [Packages](Packages/README.md) | Unity/Meta dependencies and embedded editor tooling |
| [ProjectSettings](ProjectSettings/README.md) | Editor version, Android and XR configuration |
| [Client documentation](docs/README.md) | Preview and historical build evidence |
| [Build plan](../docs/build-plan.md) | Checks and hardware acceptance |

## Intended demo

Choose a recipe while signed in on desktop. Enter the reachable backend address and one-time pairing code in Quest. The client joins that session, displays its steps, and exposes voice and monitoring controls. The current source includes a cube assistant, microphone double-tap detection, periodic visual assistance requests and state polling; hardware behavior is unverified.

Untethered means no USB/PC VR connection during use. Online guidance still needs the backend. The bundled sandwich is an offline development fallback.

## Honest status

Source import and static project checks pass. The repository preserves newer connection-loss and timer-reset fixes in `RamseyApp.cs` that were absent from the external editor copy. That external copy is not automatically synchronized.

The earlier APK build failed because the disk filled; no new APK or headset validation is claimed. Historical notes in `BUILD-STATUS.md` and `docs/legacy-client-notes.md` describe an earlier client state. Current acceptance steps are in the build plan above.
