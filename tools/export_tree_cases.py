#!/usr/bin/env python3
"""Mirror shared component contracts and layout tokens into standalone tests."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
for name in ('tree-navigation.json', 'components-cases.json', 'interaction-cases.json', 'layout-tokens.json'):
    data = (ROOT / 'design' / name).read_bytes()
    for directory in ('go/testdata', 'rust/tests/data'):
        target = ROOT / directory / name
        if args.check:
            if not target.exists() or target.read_bytes() != data:
                raise SystemExit(f'Generated component contract differs: {target}')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
print('Go/Rust component contract copies match.' if args.check else 'Component contract copies generated.')
