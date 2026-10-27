#!/usr/bin/env python3
"""Render language-matched reference SVGs from the public Rust Tree example."""
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
    target = args.output / ('tree-dark-en.svg' if lang == 'en' else 'tree-dark.svg')
    subprocess.run([str(args.binary.resolve()), '--lang', lang, '--colors', 'truecolor',
                    '--snapshot', str(target)], check=True)
    text = ''.join(ET.parse(target).getroot().itertext())
    if lang == 'en' and any('\uac00' <= c <= '\ud7a3' for c in text):
        raise ValueError(f'Korean text in English image: {target}')
print('Korean/English public Tree reference SVGs generated and validated.')
