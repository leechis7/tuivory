#!/usr/bin/env python3
"""Generate bilingual reference SVGs from the Rust playground's Ratatui cells."""
import argparse
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/images')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for lang in ('ko', 'en'):
        suffix = '-en' if lang == 'en' else ''
        for view in ('dark', 'light', 'blackwhite', 'popup'):
            target = args.output / f'rust-playground-{view}{suffix}.svg'
            command = [str(args.binary.resolve()), '--lang', lang, '--colors', 'truecolor',
                       '--theme', 'dark' if view == 'popup' else view, '--snapshot', str(target)]
            if view == 'popup':
                command.append('--popup')
            subprocess.run(command, check=True)
            text = ''.join(ET.parse(target).getroot().itertext())
            if lang == 'en' and any('\uac00' <= char <= '\ud7a3' for char in text):
                raise ValueError(f'Korean text in English UI: {target}')
    print('Eight Korean/English Ratatui reference SVGs generated and validated.')


if __name__ == '__main__':
    main()
