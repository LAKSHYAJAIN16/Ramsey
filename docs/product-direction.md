# Product direction and minimum benchmark

## Flaivor baseline

The user selected [this Flaivor post](https://www.reddit.com/r/virtualreality/comments/1d99hhq/how_do_yall_feel_about_cooking_in_vr_flaivor_meta/) as the minimum reference. The author's text describes ingredient-photo input, recipe creation and step-by-step AI assistance. The linked video has not been independently inspected frame by frame here; movable timers are mentioned by commenters, not established by this review as a tested implementation detail. Do not claim feature parity from this checklist.

| Minimum experience | Ramsey state | Acceptance |
| --- | --- | --- |
| Ingredient photo to meal suggestions | Backend exists; complete UI/live flow unverified | Recognize a real ingredient photo and present usable choices |
| Recipe selection and structured instructions | Desktop selection and parser exist | User chooses on desktop; identical recipe arrives on Quest |
| Conversational cooking help | Voice transport exists | Real spoken question gets a contextual spoken answer |
| Useful spatial presentation | Panel plus new automatic equipment-label code | Labels align to measured objects on hardware |
| Independent spatial timers | Current panel displays timer state | Separate timers can be associated with relevant equipment |
| Complete cooking session | Individual logic tests pass | Rehearse one uninterrupted recipe on Quest |

Desktop recipe selection remains the user's requirement; do not silently move selection into the headset to imitate another product.

## Soft pivots that preserve the implementation

| Direction | Promise | Reuse | New work | Demo |
| --- | --- | --- | --- | --- |
| **Kitchen setup coach — recommended** | Get your workspace ready, then know where to act | CV labels, recipes, voice, session state | Confirmed readiness checklist and equipment-to-step association | Recognize board/bowl/press, show missing setup, guide sandwich assembly |
| Cooking practice coach | Learn one technique through guided attempts | Pixel chef, step checks, profiles | Short authored lessons, reference visuals, feedback rubric | Practice even spreading or plating and compare attempts |
| Meal coordination assistant | Finish components together | Timers, sessions, equipment labels | Task dependencies, independent spatial timers, schedule updates | Assemble two sandwiches while the press heats and a side is prepared |
| Kitchen rescue assistant | Adapt when ingredients or a step go wrong | Contextual chat, recipes, preferences | User-confirmed substitutions and versioned recipe edits | Missing sauce ingredient changes only the remaining relevant steps |

Prioritize the setup coach and one complete sandwich demo. Rescue can be a follow-up capability; it should not conceal failures in the basic headset flow. These are proposals, not shipped features.
