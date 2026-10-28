#!/usr/bin/env python3
"""Generate localized references using the public Rust focus/popup host."""
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
views = {'dark': ['--theme', 'dark'], 'light': ['--theme', 'light'],
         'blackwhite': ['--theme', 'blackwhite'], 'popup': ['--popup'],
         'nested': ['--nested'], 'ascii': ['--popup', '--ascii']}
for lang in ('ko', 'en'):
    for name, options in views.items():
        target = args.output / f'focus-{name}{"-en" if lang == "en" else ""}.svg'
        subprocess.run([str(args.binary.resolve()), '--lang', lang, '--colors', '256',
                        '--snapshot', str(target), *options], check=True)
        text = ''.join(ET.parse(target).getroot().itertext())
        if any('\uac00' <= char <= '\ud7a3' for char in text) != (lang == 'ko'):
            raise ValueError(f'Wrong image language: {target}')
        if 'Scope=' not in text or 'TUIVORY' not in text:
            raise ValueError(f'Missing host rendering: {target}')
print('Twelve localized focus/control/popup reference SVGs generated.')
