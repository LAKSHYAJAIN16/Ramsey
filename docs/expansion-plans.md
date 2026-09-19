# Ramsey expansion plans

September 19, 2026 · Product direction and implementation proposals, not a list of shipped features.

## The project needs a stronger promise

**A floating recipe is not a strong reason to wear a headset. A coach that understands what is happening at your equipment, catches a missed action, and helps you recover is.**

Build toward this promise:

> Ramsey turns a recipe into a guided session in your actual kitchen. It knows which station you are working at, what the next action requires, and when you need help.

The useful interaction is a loop: **instruct → observe → check → adapt**. Recipe retrieval, speech, and a cube character support that loop. They are not the main achievement by themselves.

The best target user is a beginner who loses their place, struggles to interpret cooking instructions, or needs reassurance while their hands are occupied. Experienced cooks who want a recipe reference are unlikely to accept the headset's setup cost. Do not design for everyone at once.

The tougher comparison is a phone on a stand with a camera-enabled voice assistant, not just a paper recipe. Basic visual Q&A can exist there too. Ramsey has to win through stable equipment references, hands-free first-person context, coordinated task state, and instructions placed where the action happens. If those pieces are absent, the headset mostly adds friction.

## Product boundaries we should keep

- **Desktop website:** required Google/Firebase sign-in, choose a recipe, inspect its source, pair the Quest, and view saved profile/progress. No requirement to return to desktop during cooking.
- **Quest:** equipment setup, spatial instructions, cooking steps, timers, double-tap voice assistant, transcription, spoken replies, monitoring, automatic advancement, recovery help, plating, and completion.
- **Desktop Python:** recipe interpretation, authoritative session state, AI calls, observations, decisions, memory, and point awards. The headset supplies observations and renders the resulting guidance.
- **Firebase:** private identity and durable profile data. A headset joins a signed-in user's session using a scoped pairing credential; a guessable session ID is not authorization.
- **Wireless use:** no USB tether during cooking. The desktop still has to run and remain reachable while it hosts Python.

Equipment tracking and converting raw recipe text into usable steps are **foundation requirements**, not optional stretch features.

## What the current code actually gives us

This distinction matters when choosing the next work:

| Area | Present foundation | Remaining gap |
|---|---|---|
| Recipe retrieval | Browserbase fetch, search-result parsing, JSON-LD extraction, source URL | The redirect-link bug was fixed and a live vegetable-sandwich recipe was retrieved. Arbitrary raw text still needs a proper normalization/compilation path. |
| Recipe execution | Ordered strings, timers, shared Python state | Ingredients, tools, atomic actions, evidence rules, and dependencies are not represented as a complete execution plan. |
| Quest assistant | Cube placeholder, acoustic double-tap detector, microphone recording, transcript/audio transport | Needs installed-headset validation, noise calibration, and a working paid AI-provider path. An acoustic detector cannot prove the noise came from a table. |
| Camera assistance | Sampled capture and backend completion/plating assessment code | Vision-provider integration and actual camera behavior are not validated end to end. Two agreeing images do not establish real-world reliability. |
| Spatial support | A recipe panel can be pinned with a Meta spatial anchor | A pinned panel is not equipment tracking. There is no completed inventory of tracked tools, equipment identities, or station-specific overlays. |
| Identity/profiles | Firebase sign-in integration, protected sessions, scoped Quest pairing, completion award logic | Live profile creation encountered a missing Firebase Admin service-account file. Do not describe this as ready until configured and tested. |
| Delivery | Unity scripts compile; backend tests exist | Android APK build was blocked by disk space. Quest installation and hardware testing remain necessary. |

Do not add several more AI calls before the basic session can run on the headset. A reliable three-minute interaction is more valuable than a long untested feature list.

## The three strongest expansions

### 1. An equipment-aware kitchen, not a floating dashboard

**Moment:** the user asks, “What am I supposed to do here?” while looking at the board. Ramsey shows the relevant preparation action beside that board. A timer stays beside the sandwich press instead of occupying the center of the user's view.

**Why Quest adds value:** instructions have a physical referent. “Put it there” and “check that one” can resolve to a known station rather than requiring the user to describe everything verbally.

Start with three user-confirmed stations: **prep board, sandwich press, serving plate**. In Quest, point to a location, select a label, and confirm the marker. Computer vision can suggest the label; it should not silently decide which of two similar objects it is.

Each equipment record should include:

- Stable equipment ID, user/kitchen ID, equipment type, and user-assigned name.
- Quest anchor ID and device/room association.
- Tracking state: located, uncertain, moved, or lost; plus last-seen time.
- Active recipe action and any timer assigned to that equipment.

**Important distinction:** a spatial anchor remembers a place. It does not follow a movable plate or a press that someone picks up. For the first demo, use fixed stations and explicitly ask the user to re-pin moved equipment. Later, add object detection and temporal tracking to reacquire movable objects.

For automatic localization, image detections are not enough by themselves: an image rectangle needs camera calibration and a spatial reference such as a mapped surface or depth estimate before it becomes a meaningful 3D location. Do not invent a world-space position from a label.

Unity should own local tracking and rendering. Python should associate equipment IDs with recipe state. Avoid shipping every headset pose through the model. When tracking is lost, hide precise arrows and show a clear “Find your board again” instruction. Never leave a confidently positioned marker on the wrong object.

**MVP success test:** leave the station, turn around, return, and find the instruction still aligned with the correct location. Move the plate and verify that the app does not claim it is still tracked at its old position.

### 2. A recipe compiler that creates observable actions

**Moment:** a page says, “Prepare the filling, assemble the sandwiches, and grill until golden.” Ramsey makes this executable: prepare filling → spread bread → add filling → close sandwich → transfer to press → start timer → inspect surface → plate.

This is the missing bridge between retrieving a recipe and monitoring one. A list of long paragraphs gives the vision model an ambiguous target.

Proposed pipeline:

1. Retrieve the real source and retain its URL and original instructions.
2. Prefer structured recipe data when available; otherwise isolate the actual recipe text from the surrounding article.
3. Normalize ingredients, quantities, units, servings, equipment, and instructions.
4. Split compound instructions into small actions without dropping dependencies, conditions, timing, or safety instructions.
5. Assign each action an equipment/station role and a completion method.
6. Validate the result against the source; keep uncertain details explicit instead of inventing a temperature or quantity.
7. Send the structured plan to Quest while Python retains authoritative execution state.

Example action record:

```json
{
  "id": "assemble-03",
  "source_step": 2,
  "instruction": "Place the cheese on the bottom bread slice.",
  "equipment_role": "prep_board",
  "ingredients": [{"ingredient_id": "cheese", "quantity_from_source": true}],
  "depends_on": ["assemble-02"],
  "completion": {
    "mode": "vision_or_user",
    "evidence": "Cheese is visibly on the designated bottom bread slice.",
    "cannot_infer": ["Whether cheese was added beneath an opaque filling"]
  }
}
```

Useful completion modes are `vision`, `timer_and_user`, `user`, and `sensor_and_user`. Do not force every action into computer vision. Taste, hidden ingredients, internal temperature, and elapsed cooking time need other evidence.

Retain source text alongside generated instructions so the user can ask “Why?” or “What did the original recipe say?” Show whether a substitution or suggestion was generated by Ramsey rather than present in the source.

**MVP success test:** one raw-text recipe and one JSON-LD recipe become short actions with equipment roles. All source ingredients and required conditions survive. Malformed or ambiguous input produces a useful explanation, not a different demo dish.

### 3. Contextual recovery: help with the mistake that actually happened

**Moment:** the user says “I tore the bread” or “I already put the tomato in.” Ramsey understands the current step and visible scene, offers a practical repair, and updates the remaining plan.

This is a much stronger demo than asking a chatbot to repeat a recipe. It shows the system responding to the user's situation.

Start with a small, demonstrable set:

- Missing ingredient → propose a compatible alternative or omission and explain the effect.
- Assembly out of order → continue from what is already done instead of restarting the recipe.
- Overfilled sandwich/wrap → redistribute the filling before closing.
- Torn wrap/bread → suggest a feasible presentation change using the available ingredients.

The response should contain a short explanation plus a **proposed plan patch**, not just prose. The cook confirms a meaningful ingredient or method change in Quest. Python validates the patch, updates the plan revision, and invalidates observations for the old step.

Use the user's stored allergies/preferences when proposing alternatives, but do not infer that a product is allergen-free from its appearance. Readable packaging or user confirmation is needed for ingredient-specific claims.

**MVP success test:** deliberately deviate in one supported way. Ramsey explains the change, the user accepts it, and later instructions consistently reflect the revised plan.

## Other expansions ranked by usefulness

Effort is relative to this repository, not a delivery-time guarantee. “Medium” can still require hardware work.

| Idea | Useful interaction in Quest | Why it improves the project | Effort / priority |
|---|---|---|---|
| Ingredient readiness check | “What am I missing?” before starting | Prevents beginning with the wrong setup; visually clear demo | Medium · after recipe compiler |
| Step-specific “Did I do it right?” | Feedback tied to the action and board in view | Teaches technique rather than merely advancing | Medium · high |
| Equipment-bound timers | A timer and task label beside the right press/pan | Solves “which timer is this?” and makes spatial UI worthwhile | Low–medium · high |
| “Why this step?” teaching | A one-sentence explanation on request | Builds understanding without overwhelming the cook | Low · high |
| Plating before/after | One actionable visual suggestion, then a comparison | Produces an immediate, visible payoff | Medium · high |
| Attention manager | “Your press timer finished; the board can wait” | Helps coordinate tasks without constant chatter | Medium · after station IDs |
| Resume after interruption | “You finished filling; the next action is closing” | Saves the user's place and summarizes what was actually confirmed | Low–medium · high |
| Personalized skill practice | A short practice goal based on prior sessions | Makes the profile useful beyond a name and XP total | Medium · later |
| Accessible instruction controls | Larger captions, repeat, slower speech, one action at a time | Practical support for different users and noisy environments | Low–medium · high |
| Multi-dish timing | Coordinate parallel tasks to finish together | Strong real-world value, but requires a dependency graph | High · later |
| Shared cooking | Two headsets split prep tasks in the same kitchen | Interesting collaboration, much harder identity/spatial synchronization | High · defer |

### More ambitious directions with a real reason to exist

**Show me the motion.** At the prep board, show a short, spatially aligned demonstration of a folding or assembly technique. Start with one authored animation and a replay control, not generated hands for arbitrary knife work. This adds something speech cannot convey well. It requires suitable assets and reliable alignment, so it follows equipment setup.

**Practice before cooking.** Run a no-heat rehearsal of a technique using the real board and utensils. The user can practice the sequence, ask why each move matters, and restart without wasting a full meal. This could make Ramsey more compelling as a short cooking lesson than as an assistant worn through every everyday meal.

**Remember what is hidden.** Maintain an ingredient/action ledger from observations and user confirmations. Once the sandwich is closed, the assistant can say “You confirmed the cheese earlier” instead of pretending it can see through the bread. Keep the distinction between observed, user-confirmed, and unknown visible in the underlying state.

**Cook with what this kitchen has.** Before starting, adapt a recipe to confirmed equipment and available ingredients. A recipe that requires an oven should not reach the headset unchanged when the only available appliance is a sandwich press. Offer a suitable alternative or explain that the method is unsupported; do not invent a supposedly equivalent conversion.

**Ask the kitchen, not a menu.** “What needs my attention?” resolves across active equipment and action states. This becomes powerful with multiple tasks: identify the station, explain why it matters now, and give one next action. It is a later payoff of the same state model, not a separate chatbot feature.

### Make plating assistance specific

Avoid a generic “Looks great!” or a supposedly objective beauty score. Offer one visible adjustment: center the sandwich, separate overlapping portions, use an ingredient already available as a garnish, or clean a visible smear on the rim. Let the cook choose whether to apply it.

The comparison should say what changed, not claim that a stylistic preference is universally better. Keep cultural and personal preferences in mind. Completion points should reward finishing and practicing, not penalize someone for a subjective plating judgment.

### Give the cube a functional role

The cube should clearly show listening, thinking, speaking, and needs-attention states. Place captions near it without covering the food. A double tap opens the conversation; a visible controller/hand fallback must always work.

Use short responses, interruption, repeat, and “not now.” Most of the time, the assistant should stay quiet. Continuous monitoring does not imply continuous talking.

The name, voice, and eventual character design are presentation choices. A recognizable celebrity imitation is not necessary to demonstrate the underlying capability.

## A demo that proves the concept

**Preferred story: one sandwich, one recoverable mistake, three tracked stations.**

1. On desktop, sign in and select a real recipe. Briefly show the source link and pair Quest.
2. In Quest, confirm the prep board, press location if approved, and plate. Instructions attach to the board.
3. Spread and add a visible filling. The app recognizes a completed action and advances. Keep manual confirmation available.
4. Deliberately omit a visible component before closing. Ramsey asks whether it was intentionally skipped; it must not assert an ingredient is missing if it could be hidden.
5. Double tap the table. Ask for an available substitution. Confirm the plan update.
6. If a press is allowed, demonstrate a timer at its station. Otherwise use a no-heat recipe and complete assembly.
7. Look at the serving plate. Receive one specific plating suggestion and show the improved arrangement.
8. Finish in Quest. The headset shows points, and the signed-in profile receives one completion award.

The first automatic advancement and the contextual recovery are the two key proof points. If a feature is unreliable, simplify the action or use explicit confirmation. Do not present a prerecorded or manually triggered decision as live recognition.

For a press demo, closed equipment hides the food. Use time and user confirmation while the lid is closed; inspect appearance only after it is opened. Do not promise the camera can see inside it. Venue approval is required before bringing a powered cooking appliance.

## What to build next, in order

### Gate 0: make the existing flow usable

- Configure Firebase profile storage and complete an actual sign-in/profile-save test.
- Resolve build storage, install the native app, and verify pairing over the intended Wi-Fi network.
- Verify one microphone → transcription → reply → speaker round trip.
- Verify one actual headset-camera frame reaches a vision-capable model and returns a meaningful observation. A JSON response from a fake does not establish this.
- Keep the desktop as setup/profile, with the cooking controls on Quest.

### Gate 1: build the distinctive core

- Introduce the structured recipe/action representation and raw-text normalization.
- Add confirmed equipment IDs and three stationary spatial anchors.
- Show the current action at its assigned station, including a station-bound timer.
- Add completion evidence and uncertainty states for two or three visible actions.

### Gate 2: demonstrate adaptation

- Implement one substitution/recovery path that changes the actual remaining plan.
- Add one manual plating-check interaction in Quest.
- Save completion and a short useful skill summary to the user's profile.

### Gate 3: expand only after the core works

- More recipes and completion detectors.
- Moved-object reacquisition.
- Parallel-task scheduling and multi-dish support.
- Longer-term coaching and optional before/after history.

**If time is tight:** cut chef packs, extra modes, complex scoring, and decorative website work before cutting the equipment/action/feedback loop.

## Concrete implementation map

These are proposed changes, not declarations that the modules already implement the feature.

| Repository area | Next responsibility |
|---|---|
| `backend/recipe_engine/parser.py` | Keep source extraction and text cleanup separate from execution planning; preserve the source instructions. |
| New `backend/recipe_engine/compiler.py` | Produce validated ingredients, atomic actions, equipment roles, dependencies, and completion rules from structured or raw recipe text. |
| `backend/models.py` | Introduce versioned `RecipePlan`, `Action`, `EquipmentBinding`, and `Observation` schemas. Preserve compatibility with existing recipe strings during migration. |
| `backend/chef/session.py` | Hold action states, equipment bindings, plan revisions, user confirmations, and the completion event. |
| `backend/chef/step_assist.py` | Evaluate evidence against the specific compiled action, rather than asking whether a long recipe paragraph is finished. |
| `backend/chef/kitchen_spots.py` | Evolve label-only spots into profile-owned equipment records. The existing label list does not contain usable tracking geometry. |
| New Quest `RamseyEquipment.cs` | Create/select/re-pin equipment stations, manage their anchors and tracking state, and render station labels. |
| Quest `RamseyApp.cs` / `RamseyAssistant.cs` | Expose equipment setup, plating checks, recovery confirmation, and all cooking interactions inside Quest. |
| `backend/app.py` | Add authenticated plan/equipment/event transport. Explicitly extend the Quest-token allowlist for the new operations; do not bypass ownership checks. |
| `backend/profiles.py` | Save confirmed skill progress and optional equipment metadata, with repeat-safe completion handling. |

Start with one vertical slice: one imported recipe → one compiled action → one bound prep-board anchor → one observation → one justified state transition → one on-headset update. Extend that working slice rather than building each subsystem in isolation.

Compiler validation should reject missing ingredient references, dangling dependencies, cycles, lost source conditions, and unsupported unit conversions. Tests should include a compound step, a timed step, an ingredient mentioned only in the instructions, and ambiguous raw prose. Hardware tests should include an occluded board, two similar plates, a moved plate, a disconnected desktop, and an old camera result arriving after Next or Back.

## State and evidence design

The backend needs more than a current step number. Track action states such as `ready`, `in_progress`, `waiting_for_confirmation`, `completed`, and `needs_help`, along with the plan revision and evidence that caused a transition.

An observation should carry session ID, recipe/plan revision, action ID, equipment ID, frame ID, capture time, visibility, and model evidence. Reject late observations for an old action. Keep a bounded latest-frame queue rather than a backlog that tells the cook what was happening a minute ago.

Treat model confidence as a heuristic, not a calibrated probability. Two similar frames can repeat the same mistake. Test against negative examples, require all conditions for the action, and use human confirmation when an important fact is not visible.

A fixed-station map is a practical first step. For later object tracking, distinguish **where an object was last seen** from **where it is currently tracked**. Never turn “not visible” into “gone,” “finished,” or “safe.”

Keep an event log for debugging: observation accepted/rejected, action advanced, correction offered, user overrode decision, recipe revised, completion awarded. This makes the project explainable to judges and helps diagnose failures without guessing.

## Make profiles useful, not ornamental

Persist confirmed preferences, allergy statements, completed recipes, skill practice, and user-approved equipment labels. Keep those separate from temporary camera observations.

Good personalization: “You prefer smaller steps, so I'll guide the folding one move at a time.” Bad personalization: accumulating vague AI scores or presenting guessed health/nutrition information as measured facts.

Awards should be idempotent per completed session and stored under the verified Firebase user. A refresh or repeated headset event must not award extra XP. Local browser storage is not the authoritative profile.

Do not save raw kitchen video by default. If optional plating photos are introduced, let the user choose to save them and delete them later. Retain the useful session summary without requiring a permanent recording of their home.

## How to tell whether this is actually better than a recipe

Run the same short task with a phone recipe and with Ramsey. Use comparable participants or alternate order to reduce the effect of practice.

Measure:

- How often someone stops cooking to retrieve the next instruction.
- Missed actions and incorrect automatic advancements.
- Time to recover from the same deliberately introduced, harmless mistake.
- How many assistant interruptions the user found unnecessary.
- Whether users understand why they performed a technique afterward.
- Setup time, headset comfort, and whether they would choose to use it again.

For the prototype, suggested engineering goals are zero incorrect automatic advances in the scripted demo, no incorrect equipment labels left active after tracking loss, a successful plan update after the supported mistake, and exactly one saved completion award. These are targets to test, not results already achieved.

The project earns its headset if hands-free, situated help compensates for the burden of wearing it. If testers prefer the phone, narrow the use case to guided skill practice or complex coordination rather than adding more effects.

## What not to spend the hackathon on

- A marketplace of celebrity chefs before one original assistant works reliably.
- Grocery checkout, social feeds, or broad leaderboards.
- Arbitrary numerical plating scores or unmeasured calorie claims.
- Claiming reliable burn detection, internal doneness, or emergency response from occasional camera images.
- Automatic emergency-service calls as a demo feature. Actual emergency calling remains unimplemented; it should not be presented as a safety system.
- A visual redesign that moves the cooking experience back to the desktop.

**Recommended pitch:** “A spatial cooking coach that turns real recipes into actions, understands your workstations, and helps you recover when cooking doesn't go to plan.”
