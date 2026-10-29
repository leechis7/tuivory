#!/usr/bin/env python3
"""Generate localized references from the public component catalog host."""
import argparse
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary',type=Path)
parser.add_argument('--mode',default='forms')
parser.add_argument('--grid-preset',choices=['simple','data'])
parser.add_argument('--grid-sample',action='store_true')
parser.add_argument('--ascii',action='store_true')
parser.add_argument('--name',help='output filename prefix')
parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/images')
args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
for lang in ('ko','en'):
 for theme in ('dark','light','blackwhite'):
  path=args.output/f'{args.name or args.mode}-{theme}{"-en" if lang=="en" else ""}.svg'
  subprocess.run([str(args.binary.resolve()),'--mode',args.mode,'--lang',lang,'--theme',theme,'--colors','256','--snapshot',str(path)]+(['--grid-preset',args.grid_preset] if args.grid_preset else [])+(['--grid-sample'] if args.grid_sample else [])+(['--ascii'] if args.ascii else []),check=True)
  text=''.join(ET.parse(path).getroot().itertext())
  assert any('\uac00'<=c<='\ud7a3' for c in text)==(lang=='ko'),path
print(f'{args.mode}: six localized references generated')
