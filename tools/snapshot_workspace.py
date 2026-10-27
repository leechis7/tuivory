#!/usr/bin/env python3
"""Render bilingual workspace reference SVGs from the Rust public API host."""
import argparse
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path)
parser.add_argument('--output', type=Path, default=ROOT / 'docs/images')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
for lang in ('ko', 'en'):
    for view in ('dark', 'light', 'blackwhite', 'ascii'):
        target = args.output / f'workspace-{view}{"-en" if lang == "en" else ""}.svg'
        command = [str(args.binary.resolve()), '--lang', lang, '--theme',
                   'dark' if view == 'ascii' else view, '--colors', 'truecolor', '--snapshot', str(target)]
        if view == 'ascii':
            command.append('--ascii')
        subprocess.run(command, check=True)
        text = ''.join(ET.parse(target).getroot().itertext())
        if lang == 'en' and any('\uac00' <= c <= '\ud7a3' for c in text):
            raise ValueError(f'Korean text in English image: {target}')
print('Eight bilingual workspace SVGs generated and validated.')
