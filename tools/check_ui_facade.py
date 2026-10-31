#!/usr/bin/env python3
"""Check SDK-only examples/consumers and pinned Go compatibility exports."""
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
violations=[]
go_files=list((ROOT/'go/examples').rglob('*.go'))+list((ROOT/'go').glob('*_test.go'))
rust_files=list((ROOT/'rust/examples').rglob('*.rs'))+[ROOT/'rust/tests/ui_facade.rs']
for p in go_files:
    if 'examples' in p.parts and re.search(r'"github.com/leechis7/tuivory/go/(?:ui|terminal)"',p.read_text()):
        violations.append(str(p.relative_to(ROOT))+' (use the single root import)')
    for line in p.read_text().splitlines():
        if re.match(r'\s*(?:\w+\s+)?"github.com/(?:rivo/tview|gdamore/tcell)',line):
            violations.append(str(p.relative_to(ROOT)))
for p in rust_files:
    # Match direct crate paths, including inline expressions; Tuivory's legacy
    # adapter paths are SDK paths and remain a supported migration option.
    if re.search(r'(?<![\w:])(?:ratatui|crossterm)::',p.read_text()):
        violations.append(str(p.relative_to(ROOT)))
if violations:
    raise SystemExit('Direct backend imports/paths: '+', '.join(violations))
subprocess.run(['go','run','./internal/cmd/facadegen','--check'],cwd=ROOT/'go',check=True)
print(f'SDK-only facade: {len(go_files)} Go and {len(rust_files)} Rust sources; pinned Go exports match.')
