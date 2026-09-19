# Ramsey on Quest

**Product-flow correction:** recipe selection belongs on the desktop, with Python owning session logic and sending the chosen steps to a paired headset. The prototype below does not yet implement that pairing or continuous monitoring. See [the confirmed user flow](../QUEST-FLOW.md); it supersedes the earlier headset-led connection flow.

This source folder mirrors `C:/Users/laksh/Ramsey/Assets/Ramsey`. The Unity project is separate from this backend repository.

![Unity rendering of the Ramsey recipe panel; the blue backdrop is the Editor, not headset passthrough.](docs/kitchen-preview.png)

## Standalone operation

Install the Android APK on a Quest 3 or 3S. After installation, the app runs on the headset without a USB cable, PC VR streaming, or a running laptop. The bundled four-step Garden sandwich recipe, navigation, ingredient list and five-minute timer work offline.

AI chat and camera analysis require a reachable Ramsey backend. The app starts offline. Choose **Connect** to enter the backend's HTTPS URL with the Quest system keyboard. The address is saved on the headset. Provider API keys stay on the backend, never in the APK. Reconnecting starts a fresh server session from the bundled recipe.

## Controls

- Point with the right controller and press the index trigger, or point with the tracked right hand and pinch.
- **Next step / Back** advances the recipe. **Ingredients** toggles the ingredient list.
- **5-min timer** starts five minutes offline; connected mode uses the backend's step-duration detection.
- **Talk to Ramsey** starts recording; tap **Stop recording** to send. Recording ends at 20 seconds. The app requests microphone permission.
- **Check cooking** requests headset-camera permission and uploads one JPEG. It closes the camera after capture. It does not stream continuously.
- **Recenter**, or the right controller B button, brings the panel in front of you.
- **Pin / unpin** stores/removes a local Meta spatial anchor for the panel. The pin is restored at startup when the room can be localized.
- Editor-only: mouse clicks, left/right arrows, R to recenter. **Connect** defaults to `http://127.0.0.1:8000` in the Editor.

## Reproduce in Unity

Unity 6000.6.2f1 with Android Build Support, SDK/NDK and OpenJDK. Installed packages: Meta XR Core SDK 205.0.0, Interaction SDK 205.0.0, MR Utility Kit 205.0.0, and Unity OpenXR 1.18.0.

Copy `Assets/Ramsey` into the Unity project. Let scripts compile. Use **Ramsey > Configure Quest**, **Ramsey > Create Kitchen Scene**, then **Ramsey > Validate Kitchen Scene**. Scene creation opens an existing Ramsey scene rather than replacing it. Android targets ARM64 with IL2CPP. The bundle ID is `com.ramsey.kitchen`.

Build `Assets/Ramsey/Scenes/RamseyKitchen.unity` for Android. Development builds accept HTTP for LAN testing; release builds require HTTPS. To bake in a hosted URL, edit `Assets/Ramsey/Resources/ramsey-config.json` before building. An address already saved on the headset takes precedence.

## Hosting the backend

The repository includes a Dockerfile. Run one worker: cooking sessions and kitchen-spot labels currently live in memory. A restart loses server sessions; reconnect from the app to start again. Persistent user memory needs a mounted `backend/data` directory. Configure credentials as hosting environment variables, not Docker build arguments or committed files.

```sh
docker build -t ramsey .
docker run --rm -p 8000:8000 --env-file .env ramsey
```

For laptop-free use, deploy this container on your chosen host with HTTPS and set the resulting URL in the app. The cloud service has not been provisioned. Optional Firebase credentials must be mounted as a secret file if Firebase features are used. Health check: `/health`.

## Remaining device checks and scope

No headset was connected during development. Verify passthrough, controller/hand aiming, system keyboard, microphone/camera permissions, audio playback and spatial-anchor restoration on hardware. Existing Backboard voice provider settings still need a live end-to-end check. Windows ARM Editor cannot load the SDK's x64 desktop OVRPlugin; this is separate from the Android build.

This first client implements manual single-frame cooking checks and a panel anchor. The planned continuous correction loop, audio double-knuckle-tap activation, semantic kitchen-station anchors and recipe-search UI are not implemented here yet. The backend has additional endpoints for those future flows.

## Verification on September 19, 2026

- All 59 backend tests pass, including Quest WAV and browser WebM upload-format coverage.
- Live localhost HTTP: health check, loading the bundled recipe, advancing a step, and reading the saved session all passed after restarting the backend.
- Live AI chat reached Backboard, which returned a billing restriction: its free credit is reserved for Memory/RAG and cannot cover LLM chat. AI responses need available LLM credit/subscription before end-to-end testing can pass.
- Unity Editor and Android player script compilation succeeded. The cooking panel was inspected in a rendered screenshot. Hardware behavior remains unverified.
- APK build failed during native linking because C: ran out of disk space. The follow-up disk check showed 0.37 GiB free. No installable APK was produced. Free roughly 10 GB before retrying the Android build; keep the existing build cache so Unity can reuse completed compilation.
