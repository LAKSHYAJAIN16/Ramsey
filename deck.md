# Ramsey
## Slide 1 — Cooking help, where you cook

A mixed-reality cooking companion: choose a recipe on desktop, then receive guidance in your kitchen through Quest.

Speaker note: The product uses passthrough so the user can see their real workspace. Show verified functionality and label proposed interactions.

---

## Slide 2 — Recipes describe a dish, not your situation

During cooking, people switch between instructions, ingredients, timers, and questions. A static recipe cannot see whether the current step appears complete or whether something needs attention.

Ramsey's ambition is contextual guidance while keeping the user's hands available.

---

## Slide 3 — One cooking session, two surfaces

1. Sign in and choose a recipe on desktop.
2. Pair the Quest to that session.
3. Follow spatial step cards in passthrough.
4. Ask the chef for help by voice.
5. Receive cooking/plating feedback and complete the recipe.

The Python backend owns recipe and session logic. The Quest displays state and captures input. Wireless operation still requires a reachable backend for online features.

---

## Slide 4 — An assistant that knows the current step

The intended experience combines structured recipe steps, contextual conversation, timers, equipment locations, and visual observations.

Requested interactions include a double-table-tap voice assistant, automatic progression when supported by evidence, and completion points. Present these as product goals unless the exact path is demonstrated on hardware.

---

## Slide 5 — What exists in the repository

- Python recipe parsing/search, session state, conversation and vision integration code.
- Desktop companion and marketing homepage.
- Firebase/profile and Quest pairing routes with associated tests.
- Step/plating assistance code and tests.
- Unity client source for recipe UI, audio transport, manual camera checks, and spatial-panel anchoring.

Repository presence is not proof of live provider or on-headset operation. Some earlier documentation predates pairing/assistance code; verify the selected demo path before presenting.

---

## Slide 6 — Demo with an honest boundary

Show desktop recipe selection, parsed steps, and session progression first. Demonstrate any verified voice or vision integration next.

Only demonstrate Quest pairing, passthrough, camera permissions, and spatial anchors as working after a hardware rehearsal. If using an Editor view, label it “Unity Editor preview.” Use fixture/offline recipes with a visible label.

---

## Slide 7 — Architecture

Desktop selection and identity connect to a Python/FastAPI session service. Quest exchanges recipe state, audio, and observations with that service. Recipe acquisition and AI services run behind the backend; provider keys stay off the headset.

Named integrations in the codebase include Browserbase, Backboard, Firebase, and Meta/Unity tooling. Sponsor eligibility and live readiness must be checked separately.

---

## Slide 8 — Current limits and next proof

Prior build notes report an Android build failure due to disk space and no completed headset verification. Live voice/AI credentials and provider billing were also outstanding in those notes; this deck does not claim those issues were resolved.

Next proof: one desktop-selected recipe reaches the Quest, a voice question refers to the correct step, and the session survives a reconnect without replacing the recipe.

Visual guidance is experimental. Do not pitch it as a certified alarm or claim automatic emergency calling. The chef persona uses an original voice, not a verified celebrity partnership or licensed imitation.

---

## Slide 9 — Where this can grow

Prioritize dependable pairing and voice interaction, then equipment-aware guidance, cautious step recognition, and plating feedback. Evaluate whether each feature improves a real cooking session before expanding.

Close: “The recipe stays with you. The help responds to what you are doing.”

Build record: [CODEX_LOG.md](CODEX_LOG.md). Existing references: [README.md](README.md), [Quest client notes](unity-client/README.md), and [expansion plans](EXPANSION_PLANS.md).
