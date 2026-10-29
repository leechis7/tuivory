#!/usr/bin/env python3
"""Generate localized references from the public Rust menu host."""
import argparse,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary',type=Path);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/images');args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
for lang in ('ko','en'):
 for view in ('dark','light','blackwhite','ascii'):
  path=args.output/f'menu-{view}{"-en" if lang=="en" else ""}.svg'
  cmd=[str(args.binary.resolve()),'--lang',lang,'--theme','dark'if view=='ascii'else view,'--colors','256','--open','--snapshot',str(path)]
  if view=='ascii':cmd.append('--ascii')
  subprocess.run(cmd,check=True);text=''.join(ET.parse(path).getroot().itertext());assert any('\uac00'<=c<='\ud7a3'for c in text)==(lang=='ko'),path
print('Eight bilingual menu references generated and validated.')

for lang in ('ko','en'):
 path=args.output/f'menu-nested{"-en" if lang=="en" else ""}.svg'
 subprocess.run([str(args.binary.resolve()),'--lang',lang,'--open','--menu-id','recent','--snapshot',str(path)],check=True)
 text=''.join(ET.parse(path).getroot().itertext());assert any('\uac00'<=c<='\ud7a3' for c in text)==(lang=='ko'),path
print('Two localized nested-menu references generated.')
