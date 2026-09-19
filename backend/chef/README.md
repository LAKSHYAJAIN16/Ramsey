# Chef and cooking state

Start with [session.py](session.py) for steps, timers and completion, then [brain.py](brain.py) for the conversation/tool loop. [step_assist.py](step_assist.py) evaluates camera evidence and plating feedback; [vision.py](vision.py) defines visual questions. [cooking_monitor.py](cooking_monitor.py) maintains the monitoring loop. [kitchen_spots.py](kitchen_spots.py) stores equipment labels; [memory.py](memory.py) stores assistant memory.

Automatic progression requires repeated qualifying observations. Uncertain, stale, duplicate, timer-dependent or nonvisual evidence must not silently complete a step. [Tests](../tests/README.md) exercise those rules with fake provider output; visual accuracy is not established by these tests.

The persona uses an original voice. This is not a celebrity endorsement or certified hazard detector. [Backend overview](../README.md).
