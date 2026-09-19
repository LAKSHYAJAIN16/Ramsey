# Judge guide — start here

## Two-minute reading route

1. [Pitch deck](../deck.md): problem, experience, and differentiation.
2. [Blueprint](blueprint.md): what runs on desktop, Python, and Quest.
3. [Backend tests](../backend/tests/README.md): reproducible evidence.
4. [Quest project](../unity-client/README.md): source, setup, and device limitations.

## Demo route

Run the backend using the [root instructions](../README.md), open the homepage, then the desktop companion. Sign-in needs configured Firebase; live recipe search/AI needs its respective provider access. Do not substitute mocked login or recipe data without labeling it.

For a complete device demo, select a recipe, generate its pairing code, join from Quest, ask one contextual question, advance a step, and verify completion on the same profile. This is the acceptance route, not a claim it has already been rehearsed successfully.

Without keys or a headset, inspect the source and run the offline test suite. The Unity preview is an Editor image. Do not describe it as live passthrough.

## Evidence matrix

| Claim | Evidence | Boundary |
| --- | --- | --- |
| Backend logic | 78 local tests passed on September 19, 2026 | Fake external providers |
| Browser source | JavaScript syntax checks pass | Not a browser UX test |
| Portable Unity source | Assets, Packages, ProjectSettings and static checks | Not C# compilation or an APK |
| Pairing, voice, visual assistance | Routes, client code and contract tests | Full live/headset path unverified |
| Android deployment | Prior failed native build notes | No working APK claimed |

## Where the original work is

[Recipe parsing](../backend/recipe_engine/README.md), [stateful guidance and guarded progression](../backend/chef/README.md), [desktop session setup](../frontend/README.md), and [Quest application code](../unity-client/Assets/Ramsey/Scripts/README.md). Unity/Meta and embedded editor tooling are dependencies; see [credits](../SOURCES.md).
