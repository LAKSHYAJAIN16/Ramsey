# Unity project configuration

`ProjectVersion.txt` selects Unity 6000.6.2f1. `EditorBuildSettings.asset` names the cooking scene. Other settings define Android, rendering, input and XR behavior.

Commit portable settings, not UserSettings or signing credentials. Source checks validate scene references; an actual Android build remains necessary. [Project setup](../README.md).
