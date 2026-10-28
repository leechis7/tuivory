#!/usr/bin/env python3
"""Generate localized references from the public component catalog host."""
import argparse
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary',type=Path)
parser.add_argument('--mode',default='forms')
parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/images')
args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
for lang in ('ko','en'):
 for theme in ('dark','light','blackwhite'):
  path=args.output/f'{args.mode}-{theme}{"-en" if lang=="en" else ""}.svg'
  subprocess.run([str(args.binary.resolve()),'--mode',args.mode,'--lang',lang,'--theme',theme,'--colors','256','--snapshot',str(path)],check=True)
  text=''.join(ET.parse(path).getroot().itertext())
  assert any('\uac00'<=c<='\ud7a3' for c in text)==(lang=='ko'),path
print(f'{args.mode}: six localized references generated')
