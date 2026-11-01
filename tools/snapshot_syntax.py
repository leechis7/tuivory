#!/usr/bin/env python3
"""Capture localized SQL highlighting references from actual SDK widgets."""
import argparse,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary',type=Path);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/images');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
for lang in ('ko','en'):
    for view in ('dark','light','blackwhite','ascii'):
        path=a.output/f'syntax-{view}{"-en" if lang=="en" else ""}.svg'
        command=[str(a.binary.resolve()),'--lang',lang,'--theme','dark' if view=='ascii' else view,'--colors','8' if view in ('ascii','blackwhite') else '256','--snapshot',str(path)]
        if view=='ascii':command.append('--ascii')
        subprocess.run(command,check=True)
        text=''.join(ET.parse(path).getroot().itertext())
        assert 'SELECT' in text and 'NVL' in text and 'COUNT' in text,path
        assert any('\uac00'<=c<='\ud7a3' for c in text)==(lang=='ko'),path
print('Eight bilingual syntax references generated from real widgets.')
