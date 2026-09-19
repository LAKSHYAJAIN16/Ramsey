# Repository checks

Run `python scripts/check_unity_project.py` from the root. It checks the Unity project skeleton, embedded package presence, asset metadata, scene references, and accidentally tracked build/cache directories.

This is a source portability check, not a C# compiler or device test. [CI](../.github/README.md) runs it alongside backend tests and browser syntax checks.
