#!/usr/bin/env python3
"""Compare all 192 token pairs consumed by Go, Python and Node.js with the JSON."""
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    document = json.loads((ROOT / 'design/tokens/candidate.json').read_text())
    # Go runs on the current host as a temporary verification executable only.
    with tempfile.TemporaryDirectory(prefix='tuivory-consumers-') as tmp:
        binary = str(Path(tmp) / 'tokens')
        subprocess.run(['go', 'build', '-o', binary, './examples/tokens'], cwd=ROOT / 'go', check=True)
        for name, expected in document['palettes'].items():
            theme, profile = name.split('-')
            commands = [
                [binary], ['python3', 'python/examples/read_tokens.py'],
                ['node', 'javascript/examples/read-tokens.mjs'],
            ]
            for command in commands:
                result = subprocess.run(command + [theme, profile], cwd=ROOT, check=True, capture_output=True, text=True)
                if json.loads(result.stdout) != expected:
                    raise ValueError('Consumer differs: {} / {}'.format(command[0], name))
    print('Go/Python/Node.js: all 12 palettes / 192 pairs match shared JSON.')


if __name__ == '__main__':
    main()
