#!/usr/bin/env python3
"""Exercise every demo through each unified executable, including PTY input."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEMOS = ['playground', 'tree', 'workspace', 'focus', 'catalog', 'menu', 'controls', 'syntax']


def check(binary, languages):
    binary = str(binary.resolve())
    for lang in languages:
        listing = subprocess.run([binary, '--list', '--lang', lang], capture_output=True, text=True, check=True)
        assert all(demo in listing.stdout for demo in DEMOS), listing.stdout
        if lang == 'en':
            assert not any('\uac00' <= char <= '\ud7a3' for char in listing.stdout)
        for demo in DEMOS:
            subprocess.run([binary, '--demo', demo, '--help'], capture_output=True, check=True, timeout=5)
        for invalid in [['--demo', 'unknown'], ['--demo'], ['--demo', 'tree', '--demo', 'menu']]:
            result = subprocess.run([binary] + invalid, stdin=subprocess.DEVNULL, capture_output=True, timeout=5)
            assert result.returncode != 0, invalid
        cases = [
            ('playground', 'smoke_playground.py', ['--resize']),
            ('tree', 'smoke_playground.py', []),
            ('workspace', 'smoke_workspace.py', []),
            ('focus', 'smoke_focus.py', []),
            ('catalog', 'smoke_catalog.py', []),
            ('catalog', 'smoke_catalog.py', ['--mode', 'grid', '--grid-preset', 'data']),
            ('menu', 'smoke_menu.py', []),
            ('menu', 'smoke_menu.py', ['--ascii', '--shadow', 'auto']),
            ('controls', 'smoke_controls.py', []),
            ('controls', 'smoke_controls.py', ['--ascii']),
            ('syntax', 'smoke_syntax.py', []),
            ('syntax', 'smoke_syntax.py', ['--ascii']),
        ]
        for demo, script, options in cases:
            subprocess.run([sys.executable, str(ROOT / 'tools' / script), binary, '--demo', demo, '--lang', lang] + options, check=True)
            print('PASS', binary, lang, demo, *options, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binaries', type=Path, nargs='+')
    parser.add_argument('--lang', choices=['ko', 'en'])
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda binary: check(binary, [args.lang] if args.lang else ['ko', 'en']), args.binaries))
