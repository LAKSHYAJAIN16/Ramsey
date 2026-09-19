# GitHub automation

[workflows/ci.yml](workflows/ci.yml) runs on main pushes, pull requests and manual dispatch. It runs offline backend tests on Ubuntu and Windows, uploads JUnit results, checks the Unity source project, and validates browser JavaScript syntax.

No service credentials are needed. Workflow permissions are read-only. Unity compilation/APK signing is not configured: it needs a licensed build environment and Android tooling. See [build plan](../docs/build-plan.md).
