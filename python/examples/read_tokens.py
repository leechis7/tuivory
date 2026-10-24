#!/usr/bin/env python3
"""Read shared tokens without any TUI framework. Outputs data, not ANSI escapes."""
import json
import sys
from pathlib import Path


def load_palette(theme='dark', profile='256'):
    path = Path(__file__).resolve().parents[2] / 'design' / 'tokens' / 'candidate.json'
    document = json.loads(path.read_text(encoding='utf-8'))
    if document['format'] != 'tuivory.tokens.draft':
        raise ValueError('unsupported token format')
    return document['palettes'][theme + '-' + profile]


if __name__ == '__main__':
    theme, profile = sys.argv[1:] if len(sys.argv) == 3 else ('dark', '256')
    print(json.dumps(load_palette(theme, profile), ensure_ascii=False, sort_keys=True))
