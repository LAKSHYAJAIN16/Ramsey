# Ramsey Quest client

## Platform
Android / Meta Quest 3S, native Unity mixed reality.

## Purpose
Help a cook follow one recipe step at a time while seeing their real kitchen. The user has authorized a standalone Quest demo with passthrough, recipe controls, and the existing FastAPI backend.

The confirmed product flow is desktop-led: the user selects the recipe on the desktop, Python owns all cooking/AI logic, and the paired Quest receives steps and sends audio/camera input back. Continuous monitoring and a conversational chef are core requirements. See ../QUEST-FLOW.md for the authoritative flow and current implementation gaps. The bundled headset recipe is a development fallback only.

## Constraints
The installed application must run without a laptop or USB cable. An embedded sandwich recipe works offline. Remote AI requires an internet-accessible backend. No provider secrets belong in the APK. Headset validation is pending because no headset is connected.

## Existing identity
Inherit Ramsey's white, charcoal, green and blue cooking interface from frontend/css/style.css. Adapt the existing step card to spatial presentation with large controls, opaque text surfaces, and explicit connection and permission states.

