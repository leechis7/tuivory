#!/usr/bin/env python3
"""Capture actual popup widgets in twelve palettes, in Korean and English."""
import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path)
parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'docs/images')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
for lang in ('ko', 'en'):
    for view in ('off', 'auto', 'solid', 'dim', 'edge', 'ascii'):
        target = args.output / f'popup-shadow-{view}{"-en" if lang == "en" else ""}.svg'
        command = [str(args.binary.resolve()), '--lang', lang, '--shadow',
                   'auto' if view in ('edge', 'ascii') else view, '--snapshot', str(target)]
        if view in ('edge', 'ascii'):
            command.append('--' + view)
        subprocess.run(command, check=True)
        text = ''.join(ET.parse(target).getroot().itertext())
        assert any('\uac00' <= c <= '\ud7a3' for c in text) == (lang == 'ko'), target
print('Twelve localized shadow references generated from real widgets (12 palettes each).')
