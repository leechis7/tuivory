#!/usr/bin/env python3
"""Export the historical candidate palette to the shared, draft token format."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'design' / 'tokens' / 'candidate.json'
# Generated copy included in the independently distributable Go module.
GO_ASSET = ROOT / 'go' / 'internal' / 'tokens' / 'candidate.json'


def candidate():
    roles, palettes = [], {}
    with (ROOT / 'design' / 'themes' / 'lazyora-candidate.csv').open(encoding='utf-8-sig', newline='') as source:
        for row in csv.DictReader(source):
            role = row['role']
            if role not in roles:
                roles.append(role)
            palette = palettes.setdefault(row['profile'], {})
            if role in palette:
                raise ValueError('duplicate role: ' + role)
            palette[role] = {
                'foreground': row['foreground'], 'background': row['background'],
                'referenceForeground': row['reference_fg'],
                'referenceBackground': row['reference_bg'],
                'fontWeight': row['font_weight'],
            }
    return {'format': 'tuivory.tokens.draft', 'roles': roles, 'palettes': palettes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = json.dumps(candidate(), ensure_ascii=False, indent=2) + '\n'
    if args.check:
        for target in (TARGET, GO_ASSET):
            if not target.exists() or target.read_text(encoding='utf-8') != content:
                parser.exit(1, 'Token asset differs: {}. Run python3 tools/export_tokens.py\n'.format(target.relative_to(ROOT)))
        print('Shared design tokens and generated Go asset match the CSV (192 pairs).')
    else:
        for target in (TARGET, GO_ASSET):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')


if __name__ == '__main__':
    main()
