"""Portable source checks, not a substitute for compiling or running Unity."""
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'unity-client'


def main():
    errors = []
    required = ['Assets/Ramsey/Scenes/RamseyKitchen.unity', 'Packages/manifest.json',
                'Packages/packages-lock.json', 'ProjectSettings/ProjectVersion.txt',
                'ProjectSettings/EditorBuildSettings.asset']
    for name in required:
        if not (PROJECT / name).is_file():
            errors.append('Missing ' + name)
    if errors:
        print('\n'.join(errors))
        return 1
    manifest = json.loads((PROJECT / 'Packages/manifest.json').read_text(encoding='utf-8-sig'))
    lock = json.loads((PROJECT / 'Packages/packages-lock.json').read_text(encoding='utf-8-sig'))
    for name, dependency in lock['dependencies'].items():
        if dependency.get('source') == 'embedded' and not (PROJECT / 'Packages' / name / 'package.json').is_file():
            errors.append('Missing embedded package ' + name)
    for name, version in manifest['dependencies'].items():
        if version.startswith('file:') and not (PROJECT / 'Packages' / version[5:]).exists():
            errors.append('Missing local package ' + name)
    for asset in (PROJECT / 'Assets').rglob('*'):
        if asset.is_file() and asset.suffix != '.meta' and not asset.name.startswith('.'):
            if not Path(str(asset) + '.meta').is_file():
                errors.append('Missing meta for ' + str(asset.relative_to(PROJECT)))
    settings = (PROJECT / 'ProjectSettings/EditorBuildSettings.asset').read_text(encoding='utf-8-sig')
    for path, guid in re.findall(r'path: (.+)\n\s+guid: ([a-f0-9]+)', settings):
        scene = PROJECT / path.strip()
        if not scene.is_file() or not Path(str(scene) + '.meta').is_file():
            errors.append('Missing build scene ' + path)
        elif 'guid: ' + guid not in Path(str(scene) + '.meta').read_text():
            errors.append('Build scene GUID mismatch: ' + path)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    forbidden = {'library', 'temp', 'logs', 'usersettings', 'obj', 'builds', 'captures'}
    for path in tracked:
        parts = Path(path).parts
        if len(parts) > 1 and parts[0] == 'unity-client' and parts[1].lower() in forbidden:
            errors.append('Generated Unity directory tracked: ' + path)
        if path.endswith(('.apk', '.aab', '.keystore', '.jks')):
            errors.append('Build output or signing key tracked: ' + path)
    if errors:
        print('\n'.join(errors))
        return 1
    print('Unity project structure, embedded packages, asset metadata and build scene references pass.')
    print('This does not compile C# or validate headset behavior.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
