# Codex log

One row per concrete contribution. Dates are used where precise times were not recorded. Time savings were not measured.

## Demo example: fixing progression across desktop and Quest

**Prompt:** “Work on the landing page + Duolingo functionality. Look at TODO.md, PLAN.md.”

**Before:** Campaign unlocks read browser-local meal records, while Quest completion saved to the server profile. Completing a recipe in Quest did not supply the campaign's unlock data.

**Codex contribution:** Traced both paths, recovered the removed plans from Git history, and implemented durable completed-dish records attached to the recipe selected on desktop. Added daily-goal state, stale-streak handling, next-rank targets, and regression tests.

**Evidence:** [c6c0da9 — profile progression](https://github.com/LAKSHYAJAIN16/Ramsey/commit/c6c0da9), [profile tests](backend/tests/test_profiles.py). `python -m pytest backend/tests/test_profiles.py -q -p no:cacheprovider`: **4 passed**. Tests check persistence across store reload, duplicate-completion retry, and expired streak display using a fake Firestore client.

**Boundary:** The backend change is committed and pushed. Desktop campaign wiring is in progress; no end-to-end Firebase/Quest success is claimed for this change yet. No measured time savings.

## Contribution history

| Time | Who | Task | Prompt (summary) | What Codex produced | What we changed | Minutes saved |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-09-19 | Laksh + Codex | Repair campaign progression | Connect Duolingo-style progress to real cooking | [c6c0da9](https://github.com/LAKSHYAJAIN16/Ramsey/commit/c6c0da9): persistent dish completions, daily goal and rank targets; four passing profile tests | Replaced the missing server-side unlock record; desktop consumption is still being wired | Not measured |
| 2026-09-19 | Developer + Codex | Automatic equipment localization | Locate objects using CV without pointing | [Detection contract](backend/chef/spatial.py), capture-time depth samples and world-space labels | Text-only scene recognition now has a measured-location path; uncertain depth withholds labels; moving-object identity remains unfinished | Not measured |
| 2026-09-19 | Developer + Codex | Spatial verification | Validate implementation before calling it working | 89 backend tests; seven Editor spatial/portrait checks; spatial permission setup | Added malformed-box tests, depth-edge rejection and duplicate-observation guard. No live CV/device success claimed | Not measured |
| 2026-09-19 | Developer + Codex | Product direction and public documentation | Explore soft pivots, use Flaivor as baseline, omit private details | [Product direction](docs/product-direction.md) and [spatial guide](docs/spatial-localization.md) | Explicit acceptance gaps and four related directions; machine paths removed from current docs | Not measured |
| 2026-09-19 | Laksh + Codex | Publish the Quest project | Add Unity to Ramsey GitHub | [8c63c6d](https://github.com/LAKSHYAJAIN16/Ramsey/commit/8c63c6d): Assets, Packages and ProjectSettings | External Editor project became a checked-in Unity project; retained newer reconnect/timer fixes | Not measured |
| 2026-09-19 | Laksh + Codex | Automated checks | Set up .github/workflows | [6e8dcfc](https://github.com/LAKSHYAJAIN16/Ramsey/commit/6e8dcfc): offline backend tests, browser syntax and Unity source validation | Added Linux/Windows test jobs and test reports; APK compilation remains separate | Not measured |
| 2026-09-19 | Laksh + Codex | Judge navigation | Use Cut Once as a guide | [5fef46d](https://github.com/LAKSHYAJAIN16/Ramsey/commit/5fef46d): deck, root map, component guides, evidence matrix | Scattered notes became linked entry points with explicit implementation limits | Not measured |
| 2026-09-19 | Codex | Verification | Check what actually works | 78 backend tests passed locally; Unity source and JavaScript syntax checks passed; later 28 CV-related tests passed | Distinguished fake-provider logic tests from unverified live CV and headset behavior | Not measured |
| 2026-09-19 | Laksh + Codex | Pixel assistant asset | Put the supplied pixel portrait on the cube | [8305830](https://github.com/LAKSHYAJAIN16/Ramsey/commit/8305830): cleaned portrait, import settings and provenance | Added a project-owned texture without screenshot controls | Not measured |
| 2026-09-19 | Laksh + Codex | Assistant visibility | Cube should appear only when summoned | [e83ed02](https://github.com/LAKSHYAJAIN16/Ramsey/commit/e83ed02): portrait shader, summon/dismiss and idle hiding | Replaced flat colour; removed hazard-triggered cube spawning. New behavior is not yet Editor/device validated | Not measured |
| 2026-09-19 | Laksh + Codex | Remove document clutter | Match the reference README and remove irrelevant Markdown | [c436933](https://github.com/LAKSHYAJAIN16/Ramsey/commit/c436933), [e403892](https://github.com/LAKSHYAJAIN16/Ramsey/commit/e403892): consolidated plans and setup | Removed stale handoffs/package snapshots; setup now lives in infra, active technical notes in docs | Not measured |

Automatic CV-based 3D equipment localization is implemented as a sampled detection/depth pipeline, with no live-provider or hardware-success claim. No time savings, visual-recognition accuracy, or OpenAI prize eligibility is fabricated. Earlier development is not fully reconstructable from this log; linked commits are the inspectable evidence.
