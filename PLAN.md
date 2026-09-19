# Backend + frontend cleanup for the Unity pivot

## Context

Tonight's architecture changed: the Quest headset experience (spatial
anchors + CV) is moving to a native Unity app instead of this repo's
WebXR code. Unity will call the same FastAPI backend. The website
(`frontend/`) is no longer the headset client — it's the desktop/laptop
companion only. Unity's own project setup is happening outside this
repo, on the user's machine, while this plan covers the two things
squarely in scope here: (1) the backend endpoints Unity will actually
call, and (2) cleaning the website up so it reads as a coherent
desktop-only product instead of one with dead AR buttons pointing at a
feature that no longer lives here.

Two backend pieces already exist half-wired from earlier tonight and
just need finishing: `backend/chef/vision.py` (photo -> spot ID /
doneness check, mirrors the proven `backend/chef/fridge.py` pattern) and
its `SpotIdentification`/`DonenessCheck` models in `backend/models.py`.
Nothing consumes them yet.

## Backend changes

**Wire the two vision endpoints into `backend/app.py`** (same shape as
the existing `/api/fridge/analyze` at line 225), importing
`identify_spot`/`check_doneness` from `backend.chef.vision`:

- `POST /api/vision/identify-spot` — photo in, `SpotIdentification` out.
  For Unity: point the headset camera at a surface, get back a label
  (Stove/Counter/Sink/Microwave/Fridge/Other) to confirm before pinning
  a spatial anchor there.
- `POST /api/vision/check-doneness` — photo + `session_id` in,
  `DonenessCheck` out. Pulls `dish`/`current_step` from the existing
  `_get_or_create_session(session_id).to_state_dict()` (title +
  current_step fields, confirmed in `backend/chef/session.py:101-113`)
  to give the vision prompt real context instead of guessing blind.

**Add a small kitchen-spots store** so Unity's anchor labels actually
land in the Python backend, not just on-device (this is the "gives the
data to the python backend" part of the spec). New
`backend/chef/kitchen_spots.py`, in-memory dict keyed by a
`kitchen_id` string the Unity client generates and persists locally
(same pattern as the existing `_sessions`/`getSessionId()` client-owned-ID
approach already used throughout this codebase — no auth required, no
new Firestore collection yet since Unity-side auth isn't built):

- `POST /api/kitchen/spots` — `{kitchen_id, label}` in, stores it,
  returns `{id, label}`.
- `GET /api/kitchen/spots?kitchen_id=...` — returns the list.
- `DELETE /api/kitchen/spots/{id}` — removes one.

(Reuses `SPOT_LABELS` from `vision.py` for consistency between "what
the camera thinks this is" and "what got confirmed.")

**Tests** (matching this repo's existing fakes-only testing style):
- `backend/tests/test_vision.py` — mirrors `test_fridge.py`'s
  `FakeVisionClient` pattern exactly, covers both functions in
  `vision.py` (clean JSON, fenced JSON, bad-label fallback to "Other",
  bad-confidence fallback to "low").
- `backend/tests/test_kitchen_spots.py` — plain unit tests on the new
  store class (create/list/delete, isolated by kitchen_id).
- Extend `backend/tests/test_auth_routes.py`'s `TestClient` pattern (or
  a new small file) with a route-level smoke test for
  `/api/vision/identify-spot` and `/api/kitchen/spots` round-tripping
  through the real app.

No backend changes needed for the double-tap-to-listen gesture itself —
that's Unity-side detection (user's preference: audio - the sound of the
knuckle tap itself, picked up by the headset mic, possibly correlated
with proximity to a known spatial anchor like "table" rather than pure
hand-tracking/vision gesture recognition); once triggered it just calls
the already-working `/api/chat/voice` endpoint, same as today's
hold-to-talk. Noted here so it's not lost before Unity work starts -
nothing to build against it yet.

## Frontend changes (`frontend/`)

Removing everything that assumed the website itself would be the AR
client, since that job moved to Unity:

- `frontend/index.html`: remove `#enter-ar`/`#enter-vr` buttons,
  `#scene-canvas`, and the `#anchor-panel` section (label picker + spot
  list) added earlier tonight.
- `frontend/js/main.js`: remove the `XRHost` import/instantiation and
  the `checkSupport()`/enter-ar/enter-vr wiring block.
- Delete `frontend/js/xr.js` entirely — fully orphaned once the above
  lands, no other file references it.
- `frontend/js/ui.js`: remove `setAnchorPanelVisible`,
  `setAnchorLabelPickerVisible`, `renderAnchorList` (orphaned with it).
- `frontend/css/style.css`: remove the `.anchor-panel`/`.anchor-hint`/
  `.anchor-label-*`/`.anchor-list` rule block added earlier tonight.
- Leave `frontend/camera-test.html` alone — it's unlinked from anywhere
  already, harmless, and might still be useful as a reference diagnostic
  later. Not part of the app flow either way.

Everything else in `frontend/` (Campaign/Freestyle/MasterChef modes,
the lesson path, chef packs, fridge-photo suggestions, chat, voice
hold-to-talk) is unaffected and stays exactly as-is — it's the real
desktop product now, not a fallback.

**Not in this pass, flagging so it's not forgotten:** `homepage/`
still pitches "tap Enter AR on headset" / opening the URL in Quest
Browser (hero, mode launcher, FAQ). That's now describing a dead
mechanism — the real path becomes "download/open the Ramsey Quest app."
Worth a copy pass once the Unity app actually exists to describe
accurately, but rewriting marketing copy for a not-yet-built native app
isn't productive tonight.

## README.md

Update to match: swap "WebXR AR/VR/laptop entry points" (Kitchen view
bullet) for a description of the native-Unity-app-for-Quest +
web-desktop-companion split. Remove the "tap 'Enter AR on headset'"
line from Setup. Retire the "WebXR anchors/hit-test... Tier 7, not
started" open item (superseded, not applicable to this repo anymore)
and add the two new `/api/vision/*` + `/api/kitchen/spots` endpoints to
the Project layout's `backend/app.py` description.

## Verification

- `pytest backend/tests -q` — full suite, expect all passing including
  the new vision/kitchen-spots tests.
- `node --check` on every edited `.js` file; brace-balance check on
  `style.css` (same lightweight checks used all session).
- Restart the live server, `curl` the two new vision endpoints with a
  throwaway image and `/api/kitchen/spots` round-trip, same way every
  other endpoint tonight was actually hit rather than assumed working.
- Load `/app/` and confirm no console errors from the removed
  `xr.js`/anchor-panel references (nothing left trying to call into a
  deleted file).

## Status (as of this commit)

- Backend: done. Endpoints wired, 55/55 tests passing.
- Frontend: AR/VR buttons, scene-canvas, anchor panel, `xr.js`, and the
  orphaned `ui.js`/CSS all removed.
- Still outstanding: README.md update, final verification pass
  (pytest/node --check/curl/live-load), homepage copy (explicitly
  deferred, see above).
