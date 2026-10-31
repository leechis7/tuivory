#!/usr/bin/env python3
"""Capture localized public controls/container references from real widgets."""
import argparse
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('binary', type=Path)
p.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'docs/images')
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
for lang in ('ko', 'en'):
    for view in ('dark', 'light', 'blackwhite', 'ascii', 'popup'):
        path = a.output / f'controls-{view}{"-en" if lang == "en" else ""}.svg'
        command = [str(a.binary.resolve()), '--lang', lang, '--theme', view if view in ('dark', 'light', 'blackwhite') else 'dark', '--snapshot', str(path)]
        if view == 'ascii':
            command.append('--ascii')
        if view == 'popup':
            command.append('--open')
        subprocess.run(command, check=True)
        text = ''.join(ET.parse(path).getroot().itertext())
        assert any('\uac00' <= c <= '\ud7a3' for c in text) == (lang == 'ko'), path
        assert 'example-secret' not in text and 'never-render-this' not in text, path
print('Ten bilingual controls references generated and checked for localization/secret masking.')
