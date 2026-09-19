# Ramsey roadmap

## Safety — XR fire detection and emergency escalation

- Investigate on-device Quest passthrough CV models / APIs for smoke and flame detection; this must be designed for high recall and must never be presented as a certified fire alarm.
- Route recognized voice phrases: **Code Red** opens an emergency confirmation surface; **Code Yellow** opens immediate first-aid guidance for burns, cuts, choking, and other kitchen injuries. Do not automatically call 911.
- Add a multi-signal confirmation flow (visual cue, duration, confidence threshold, and a clearly audible user prompt) to reduce false positives from stove flames, reflections, and warm lighting.
- Show an immediate, accessible emergency screen with local emergency-number guidance and a one-tap call action where platform permissions allow it.
- Do **not** automatically call 911 from a prototype. Any automatic emergency-contact or emergency-services escalation needs legal, privacy, regional-number, platform-policy, and user-consent review first.
- Test with fire-safety experts and real kitchen edge cases before treating the feature as safety-critical.
