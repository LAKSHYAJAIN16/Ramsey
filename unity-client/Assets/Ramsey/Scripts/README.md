# Quest runtime

Start with `RamseyApp.cs`: it coordinates pairing, state polling, controls, voice and monitoring. `RamseyApi.cs` transports backend requests; voice, vision and anchor components connect headset capabilities to the application. The assistant currently uses a cube representation.

Backend state remains authoritative after pairing. Connection-loss handling must not silently replace a paired recipe with the offline fixture. Source checks pass; headset input/audio/camera/anchor behavior still needs rehearsal. [Asset map](../README.md).
