# Ramsey: desktop-led cooking flow

> Historical planning document. Pairing and periodic visual-assistance client code were added after its gap list was written. See [current judge evidence](docs/judging.md) and [Quest setup](unity-client/README.md) for the current implementation/verification boundary.

Confirmed by the user on September 19, 2026. This supersedes the earlier proposal to select recipes in the headset.

## User journey

1. On the desktop website, the user chooses a recipe. The Python backend owns the recipe, ordered steps, ingredients, timers, conversation, and monitoring state.
2. The user pairs their Quest with that desktop cooking session. The desktop/backend sends the selected recipe and its current state to the paired Quest. Pairing must not reset the recipe or replace it with the headset's bundled sandwich.
3. The user puts on the Quest. Passthrough shows the kitchen; the headset displays the recipe and chef interface. It renders state and captures input rather than deciding recipe progression or cooking corrections locally.
4. The user cooks and talks with the Ramsey chef: questions, requests for help, repeated instructions, and navigation all refer to the same desktop session. Audio goes from the headset to Python; spoken responses and updated state return to the headset and desktop.
5. With monitoring enabled and camera permission granted, the Quest sends sampled camera frames continuously during the cooking session. Python compares observations with the active recipe step, tracks each cooking vessel, and stays quiet when no correction is needed.
6. If something appears to be burning or going wrong, the assistant interrupts with a visible and audible alert, gives situation-appropriate help, and checks subsequent observations for improvement. Unknown or missing observations must not be treated as proof that a problem is resolved. Urgent hazards must not be suppressed by the normal correction cooldown.
7. The user can pause monitoring and microphone capture. On completion, monitoring stops and the desktop records the final session state.

## Ownership

- Desktop UI: recipe selection, session setup and control, progress display.
- Python backend: authoritative recipe state, timers, conversation, AI/vision reasoning, corrections and hazard handling.
- Quest app: passthrough, spatial UI, local anchors, controller/hand input, audio recording/playback, camera capture and transport.

The Quest is an installed, wireless application and needs no USB tether during use. With Python running on the desktop, that desktop must remain powered on and reachable during the cooking session. Hosting Python later changes where computation runs; it does not move recipe selection into the headset.

## Chef experience

A conversational Ramsey chef is central to the experience, not an optional text-only panel. The user can ask for help during a step and hear a contextual reply. The existing project persona uses an original voice rather than a recording or clone of Gordon Ramsay. Any specific avatar or licensed likeness remains a separate asset decision.

## Implementation gaps in the current prototype

- No desktop-to-Quest pairing or recipe push yet. The headset currently creates its own session and uploads its bundled recipe on Connect; this must be replaced with joining the desktop session.
- The backend already has a stateful `/ws/vision/{session_id}` monitoring path, but the Quest currently sends only manually requested HTTP cooking checks.
- Hazard analysis exists separately; its alerts need to be integrated into the continuous monitoring and spoken-response flow.
- Voice transport is wired but not validated on hardware. Live Backboard chat is blocked by account credit restrictions.
- The offline sandwich is only a development fallback, not the primary product flow.
- The Android APK build is blocked by disk space; headset functionality remains unverified.

## Next implementation order

1. Pair a Quest with the desktop session and deliver the selected recipe plus ongoing state updates.
2. Replace headset session creation with joining/rejoining that session without overwriting desktop state.
3. Enable ongoing frame sampling with bounded in-flight work, clear capture status, pause/resume, and reconnection handling.
4. Deliver contextual chef replies and priority burning/hazard alerts through one coordinated audio/UI channel.
5. Test the complete sequence on the headset, including recipe changes, connection loss, unknown visual results, and confirmed corrections.
