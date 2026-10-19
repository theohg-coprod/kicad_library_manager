#!/usr/bin/env python3
"""Build an unpublished testing PCM ZIP; optionally validate official KiCad schemas."""
from pathlib import Path
import argparse
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from library_manager import __version__

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--schemas', type=Path)
args = parser.parse_args()
metadata = json.loads((ROOT / 'pcm/metadata.in-zip.json').read_text())
metadata['versions'] = [{'version': __version__, 'status': 'testing', 'runtime': 'ipc',
                         'kicad_version': '9.0', 'kicad_version_max': '10.99',
                         'platforms': ['linux', 'windows', 'macos']}]
manifest = json.loads((ROOT / 'plugin.json').read_text())
if args.schemas:
    import jsonschema
    for document, name in ((metadata, 'pcm'), (manifest, 'api')):
        jsonschema.Draft7Validator(json.loads((args.schemas / f'{name}.v1.schema.json').read_text())).validate(document)
payload = {'metadata.json': (json.dumps(metadata, indent=2) + '\n').encode(),
           'resources/icon.png': (ROOT / 'pcm/icon.png').read_bytes()}
files = [ROOT / name for name in ('README.md', 'plugin.json', 'run_library_manager.py', 'requirements.txt', 'pcm/icon.png')]
for folder in ('library_manager', 'kicad_footprint_generator', 'scripts'):
    files.extend(p for p in (ROOT / folder).rglob('*') if p.is_file())
for file in files:
    if '__pycache__' in file.parts or file.suffix in ('.pyc', '.pyo'):
        continue
    if file.is_symlink():
        raise ValueError(f'Symlink in payload: {file}')
    payload[f'plugins/kicad_library_manager/{file.relative_to(ROOT).as_posix()}'] = file.read_bytes()
output = ROOT / f'dist/kicad-library-manager-{__version__}.zip'
output.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for name, value in sorted(payload.items()):
        info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, value)
print(f'Built testing package {output}; no release or upload performed')
