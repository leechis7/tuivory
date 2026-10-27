#!/usr/bin/env python3
"""Mirror the shared tree navigation contract into standalone module tests."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
data = (ROOT / 'design/tree-navigation.json').read_bytes()
for relative in ('go/testdata/tree-navigation.json', 'rust/tests/data/tree-navigation.json'):
    target = ROOT / relative
    if args.check:
        if not target.exists() or target.read_bytes() != data:
            raise SystemExit(f'Generated tree contract differs: {relative}')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
print('Go/Rust tree navigation contract copies match.' if args.check else 'Tree contract copies generated.')
