# Computer vision plan

> Historical design reference, not a completion report. Quest currently samples frames through `/api/vision/assist`; the older multi-vessel WebSocket loop is separate. See [automatic localization](spatial-localization.md) for the new measured-depth implementation and outstanding live/device checks.

## Context

Everything here is built on the same proven pattern already in
`backend/chef/vision.py` and `backend/chef/fridge.py`: a
`VisionClient.analyze_image(image_bytes, filename, prompt)` call
(currently `BackboardClient`, swappable), a prompt that demands ONLY
JSON in an exact shape, and fenced-JSON parsing with a safe fallback if
the model doesn't cooperate. That core logic doesn't change - what's
new here is (1) open-vocabulary object recognition instead of a fixed
enum, and (2) a streaming delivery layer on top of it.

The Unity client is the caller for all of it: headset camera frame ->
this pipeline -> result feeds back into the AR UI (a label, a
checkmark, a spoken-aloud note via the existing chat/voice pipeline).

## Reality check on "realtime" - read this before the architecture below

A vision-capable LLM call takes real time per call, typically 1-5
seconds - that's true of every provider, not a limitation specific to
this stack. There's no version of "stream 30fps through an LLM and get
instant feedback" that exists today at usable latency or cost. Claiming
otherwise would mean the demo quietly stalls or times out live.

What's real and still reads as "realtime" to a person watching: a
persistent connection that pushes results as they finish instead of a
one-shot request/response, combined with sampling frames periodically
(every few seconds) rather than continuously - a pan of simmering sauce
doesn't meaningfully change between 500ms and 3 seconds, so there's
nothing lost by not analyzing every frame. That's the design below.

## Design: one combined "check my cooking" call, not five, over a
## streaming connection instead of one-shot requests

A user pointing at their pan wants one answer covering everything
visible + doneness + any problem, not four separate uploads. So:

**One rich analysis function, two ways to reach it:**
- `POST /api/vision/check-cooking` (HTTP, one-shot) - for a manual
  "check now" trigger, or a phone-fallback path.
- `WS /ws/vision/{session_id}` (WebSocket, streaming) - Unity holds this
  open during an active cooking session, sends a frame (JSON message,
  base64-encoded JPEG - simpler to implement/debug than raw binary
  framing, and the size overhead doesn't matter at a once-every-few-
  seconds send rate) whenever it wants a check, gets the same JSON
  result pushed back when the analysis finishes. The backend tracks one
  in-flight analysis per connection and drops/ignores a new frame that
  arrives while the previous one is still processing, so it never
  queues up expensive calls faster than they can complete.

Both paths call the exact same `check_cooking()` function in
`vision.py` - the WebSocket is a delivery mechanism, not a second
implementation of the logic.

Spot identification (`/api/vision/identify-spot`) stays a plain HTTP
endpoint - it's used once per anchor placement, not repeatedly.

## Capabilities

### 1. Spot identification (exists, keep as-is)
`POST /api/vision/identify-spot`. Unchanged.

### 2. Cooking check - the core, repeated capability
`check_cooking()` / `POST /api/vision/check-cooking` /
`WS /ws/vision/{session_id}`. Photo + `session_id` in.

**Object recognition is open-vocabulary, not a fixed enum** - "pots,
pans, cutting trays, sandwich trays, everything" means the model
describes what it actually sees rather than being forced into a
pot/pan/other-style list that will always miss things.

**Response is a list of per-vessel entries, not one flat status - this
is what makes multi-cooking work without a separate code path.** One
photo of a stove with a pot of pasta and a pan of sauce should come
back as two entries, not one blended answer. Single-dish cooking is
just the one-entry case of the same shape - no special-casing needed:

```
{
  "objects": ["cutting board", "chef's knife"],   // loose items in frame, not tied to a specific vessel
  "stations": [
    {
      "vessel": "pot, left burner",
      "contents": ["pasta", "boiling water"],
      "doneness": "in progress",
      "matches_expected_step": true,
      "note": "Still a couple minutes from al dente."
    },
    {
      "vessel": "pan, right burner",
      "contents": ["tomato sauce"],
      "doneness": "done",
      "matches_expected_step": true,
      "note": "Sauce looks ready - can come off heat whenever the pasta's done."
    }
  ]
}
```

`matches_expected_step`/doneness are judged per station against
whatever's actually happening there - `session.to_state_dict()["current_step"]`
still gives the overall recipe context (e.g. a step like "while the
pasta boils, start the sauce" naturally covers both stations at once;
true parallel step-tracking across a whole recipe - separate step
indices per station - is a bigger data-model change and not something
this plan takes on tonight, see out-of-scope). This is the tractable
version of "did they mess up": comparing what's visible at each vessel
against what the recipe currently calls for, not auditing the whole
session history.

### 3. Safety/hazard check - separate call, different trigger
`check_hazard()` / `POST /api/vision/check-hazard`. Photo only, no
session needed. Meant to run on its own periodic cadence in the
background (could share the same WebSocket connection, tagged
differently, or its own lightweight poll - implementation detail for
when Unity work starts).

```
{"hazard": "none" | "smoke" | "fire" | "boil-over" | "other", "severity": "low" | "high", "note": "..."}
```

**Hard constraint, unchanged from before:** never triggers an automatic
emergency call. Feeds into the existing manual-confirmation Code Red
dialog (`backend/app.py: _safety_response`) exactly like the
voice-triggered "code red" phrase already does - a person still has to
act. Not reopening this.

## Out of scope tonight (honest, not just deferred)

- **Whole-session step-skip auditing** ("they never turned off the
  stove") - needs reasoning across multiple photos over time plus full
  step history; meaningfully harder and less reliable than judging one
  photo against the current step. Not attempting tonight.
- **Portion/serving-size verification** - vision-LLMs are unreliable at
  quantity estimation from a single photo.
- **Plating/presentation comparison against a reference photo** - a
  real, separate feature (needs a reference image, different prompt),
  not part of the core loop. Possible fast-follow.

## Implementation shape (once approved)

- `backend/chef/vision.py`: `check_cooking()` (replaces
  `check_doneness()`, open-vocabulary `objects`/`contents`),
  `check_hazard()`, `check_kitchen_setup()` - all pure/stateless, same
  fenced-JSON-parse pattern as `identify_spot()`.
- `backend/chef/session.py`: add `pending_correction: Optional[str] = None`
  to `KitchenSession`.
- `backend/chef/cooking_monitor.py` (new): `monitor_cooking()` - the
  WATCHING/CORRECTING state machine described above. Calls
  `vision.check_cooking()`, `memory.remember_mistake()` (already exists,
  unused until now), and `brain.handle_message()` (unchanged) with a
  synthetic camera-observation message when a correction is warranted.
- `backend/models.py`: `CookingCheck`, `HazardCheck`, `KitchenSetup`;
  retire `DonenessCheck`.
- `backend/app.py`: `POST /api/vision/check-cooking` (one-shot, calls
  `vision.check_cooking()` directly - no state machine, for a manual
  check or phone fallback), `POST /api/vision/check-hazard`,
  `POST /api/vision/scan-kitchen`, and `WS /ws/vision/{session_id}`
  wrapping `cooking_monitor.monitor_cooking()` - that's the one
  carrying the loop.
- Tests: `test_vision.py` covers the pure vision functions
  (`FakeVisionClient`, matching existing style); a new
  `test_cooking_monitor.py` covers the state machine itself - WATCHING
  with a match (silent, no chat call), WATCHING with a mismatch
  (mistake logged + correction generated), CORRECTING resolved
  (cleared + acknowledged), CORRECTING still-wrong-within-cooldown
  (stays silent) - using `FakeVisionClient` + the existing
  `FakeBackboardClient` (`backend/tests/fakes/fake_backboard.py`) so
  none of this touches a real model; `test_vision_routes.py` gets a
  WebSocket round-trip test via `TestClient.websocket_connect()` (same
  `TestClient` already used in `test_auth_routes.py`).

## The step-by-step correction loop

Everything above treats each photo as a one-shot, stateless question.
What you're describing - identify the setup, watch each step, catch a
mistake, correct it, then verify the correction actually landed - is a
**closed loop with memory**, not a bigger prompt. Designing it as a
stateless call would mean either nagging on every single frame or
missing real corrections entirely. So this adds real state and reuses
the chef system that already exists instead of building a second,
parallel one.

### The key move: route corrections through the existing brain.py, not a new text path

`handle_message()` (`backend/chef/brain.py`) already does everything a
spoken correction needs: Ramsey's persona/tone, the tool-call loop,
access to `CookMemory`, and the existing TTS delivery
(`audio_url` in the response). Its signature is
`handle_message(client, session, memory, user_text, ...)` - `user_text`
doesn't have to come from the microphone. A vision observation can be
fed in as a synthetic turn (e.g.
`"[camera] Sees oregano in the pan; recipe calls for basil at this step."`)
and Ramsey answers in his actual established voice, using the same
system prompt, the same "never a real Gordon Ramsay impression"
constraint, the same tool-calling ability - for free, zero changes to
`brain.py` itself. This also means a mistake naturally gets logged via
`memory.remember_mistake()` (already exists, already called nothing
yet) so it's not just spoken once and forgotten - Ramsey can reference
it later the same way he already references allergies/dislikes.

### State machine (new field: `KitchenSession.pending_corrections`)

**Keyed per vessel, not a single flag** - matches the per-station
response shape above, so two independent problems at two different
pans (multi-cooking) get tracked and corrected independently instead of
one clobbering the other: `pending_corrections: Dict[str, str] = {}`,
keyed by the `vessel` string from `check_cooking()`. Each vessel is
independently WATCHING or CORRECTING:

**WATCHING** (that vessel has no entry in `pending_corrections` - the
normal, common case):
- Run `check_cooking()` (one vision call covers every station in frame).
- A station matches its expected step, doneness progressing normally ->
  **silent for that station, no chat call at all.** This is the
  low-latency path for the 99% case: one vision call, nothing else, no
  unnecessary narration - and it stays cheap even with multiple pans in
  frame, since it's still one call either way.
- A station doesn't match, or doneness is `overcooked`/`burnt` ->
  **mistake at that vessel.** Set `pending_corrections[vessel]` to a
  short description, call `memory.remember_mistake()` directly and
  immediately (deterministic, not dependent on the LLM deciding to call
  a tool - keeps the bookkeeping reliable even if the model gets
  chatty), then call `handle_message()` once with the synthetic camera
  observation (naming which vessel) to get the actual spoken
  correction. Multiple simultaneous mistakes across different vessels
  each get their own entry and their own correction, not one merged
  message.

**CORRECTING** (that vessel has a pending entry):
- `check_cooking()` is called with that vessel's pending issue as extra
  context, explicitly asking "has this specific thing been fixed"
  rather than a generic check.
- Fixed -> clear that vessel's entry, brief acknowledgment. This
  should be a short templated response ("Better - carry on."), not a
  full LLM round-trip - a second full chat call just to say "good job"
  is latency spent on the least important response in the loop.
- Not fixed yet -> **don't re-nag every cycle.** Stay silent for that
  station (`action: "silent"`) until a cooldown passes (~30s) since the
  correction was first given, then escalate once if it's genuinely
  still wrong. Ramsey repeating himself every 3 seconds because a photo
  arrived again is worse than not enough feedback.

### Full kitchen setup (separate, infrequent - not part of the per-step loop)

`check_kitchen_setup()` - open-vocabulary inventory of the whole scene
(`available_equipment`, visible ingredients, and, cross-referenced
against what the recipe's steps actually mention, `missing_for_recipe`
if determinable). Called once at session start or on an explicit
"look around my kitchen" trigger - re-scanning the entire room on every
cycle would be wasted cost; the per-step loop only needs to watch the
active cooking vessel, which `check_cooking()` already does.

### Where the orchestration lives

New `backend/chef/cooking_monitor.py` - `monitor_cooking(client, session, memory, image_bytes, filename)`,
the single function the Unity-facing streaming endpoint actually calls.
`vision.py` stays a pure, stateless wrapper around the vision API
(easy to unit-test with `FakeVisionClient`, no side effects);
`cooking_monitor.py` is where the state machine, the `brain.py` calls,
and the memory writes live - mirroring how `brain.py` already sits
above `session.py`/`memory.py`/`tools.py` as the orchestration layer,
not inside any of them. The `WS /ws/vision/{session_id}` connection
from the earlier section wraps `monitor_cooking()`, not raw
`check_cooking()` - that's the piece that's actually stateful across
the connection's lifetime.

## Recipes to target for the demo

Starting point: **making a sandwich** - no-heat assembly is the
simplest possible first target (zero burn risk, zero timing pressure,
pure "does the vision loop actually work" validation), with a clear
path to add a cooked variant once the assembly loop is solid.

### Sandwich options, simplest first

1. **Classic deli sandwich** (bread, turkey/ham, cheese, lettuce,
   tomato, condiment - no cooking at all). The right *first* target:
   cutting board for tomato, a tray for the build, layering ingredients
   one at a time. Every layer is a natural "step" to check against
   (`matches_expected_step` per layer: "is lettuce actually down yet").
   Zero doneness/heat logic needed, so it isolates the object-recognition
   and step-matching pieces before the doneness/mistake-correction loop
   gets layered on top. Easiest to stage a clean "mistake" too: swap the
   condiment or skip a layer on purpose.
2. **Grilled cheese** (natural next step once #1 works - adds real heat
   and a doneness signal). Cutting board -> tray -> pan is three
   distinct objects across the sequence, and golden/pale/burnt is about
   the easiest doneness call a vision model can make. ~4 minutes total.
   Good moment to demo the correction loop for real: let one side go a
   little too long on purpose, watch it get caught and corrected.
3. **BLT** (stretch, once 1-2 are solid). Combines both halves in one
   recipe - bacon in a pan (raw-pink -> crispy-brown doneness, easy to
   over-cook on purpose) plus cold assembly (lettuce, tomato, cutting
   board) - the fullest single-recipe showcase of the whole loop.

### If there's time for a second, non-sandwich recipe

4. **Fried or scrambled eggs**. Single pan, ~2-3 minutes, the clearest
   possible raw-to-set visual transition.
5. **Pancakes**. Bubbling-then-flip is very legible even for a rough
   model, fast per-cake.

Keep the existing **Shakshuka** demo recipe (`data/demo_recipe.json`)
as the offline/no-network fallback it already is - fully built and
tested, just longer (~15-20 min) than ideal for a live CV showcase.
