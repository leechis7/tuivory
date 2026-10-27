#!/usr/bin/env python3
"""Compare all shared token pairs in Go/Python/Node.js, optionally also Rust."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rust', action='store_true', help='also check the Rust crate example')
    args = parser.parse_args()
    document = json.loads((ROOT / 'design/tokens/candidate.json').read_text())
    # Go runs on the current host as a temporary verification executable only.
    with tempfile.TemporaryDirectory(prefix='tuivory-consumers-') as tmp:
        binary = str(Path(tmp) / 'tokens')
        subprocess.run(['go', 'build', '-o', binary, './examples/tokens'], cwd=ROOT / 'go', check=True)
        rust_binary = Path(tmp) / 'rust' / 'debug' / 'examples' / 'tokens'
        if args.rust:
            subprocess.run(['cargo', 'build', '--manifest-path', str(ROOT / 'rust/Cargo.toml'),
                            '--locked', '--example', 'tokens', '--target-dir', str(Path(tmp) / 'rust')], check=True)
        for name, expected in document['palettes'].items():
            theme, profile = name.split('-')
            commands = [
                [binary], ['python3', 'python/examples/read_tokens.py'],
                ['node', 'javascript/examples/read-tokens.mjs'],
            ]
            if args.rust:
                commands.append([str(rust_binary)])
            for command in commands:
                result = subprocess.run(command + [theme, profile], cwd=ROOT, check=True, capture_output=True, text=True)
                if json.loads(result.stdout) != expected:
                    raise ValueError('Consumer differs: {} / {}'.format(command[0], name))
    languages = 'Go/Python/Node.js/Rust' if args.rust else 'Go/Python/Node.js'
    print(f'{languages}: all 12 palettes / 192 pairs match shared JSON.')


if __name__ == '__main__':
    main()
