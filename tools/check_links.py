#!/usr/bin/env python3
"""Check local Markdown file targets; external URLs and fragments are not fetched."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    missing = []
    files = list(ROOT.rglob('*.md'))
    for path in files:
        if set(path.relative_to(ROOT).parts) & {'.git', '.venv', 'node_modules', 'target', 'bin'}:
            continue
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith(('mailto:', '#')):
                continue
            target = target.split('#', 1)[0]
            if target and not (path.parent / target).exists():
                missing.append('{}: {}'.format(path.relative_to(ROOT), target))
    for error in missing:
        print(error, file=sys.stderr)
    if missing:
        return 1
    print('Local Markdown file targets passed (external URLs/fragments not checked).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
