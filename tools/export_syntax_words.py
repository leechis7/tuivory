#!/usr/bin/env python3
"""Mirror the shared highlighting vocabulary into standalone optional analyzers."""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
words=(ROOT/'design/sql-syntax-words.json').read_text()
outputs={ROOT/'go/internal/sqlsyntax/words_generated.go':'// Code generated from design/sql-syntax-words.json; DO NOT EDIT.\npackage sqlsyntax\n\nconst wordJSON = `'+words.rstrip()+'`\n',ROOT/'rust/src/data/sql-syntax-words.json':words}
for path,text in outputs.items():
    if a.check:
        if not path.exists() or path.read_text()!=text:raise SystemExit(f'Stale SQL vocabulary: {path}')
    else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
print('Shared SQL vocabulary matches.' if a.check else 'Shared SQL vocabulary generated.')
