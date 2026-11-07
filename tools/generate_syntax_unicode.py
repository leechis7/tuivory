#!/usr/bin/env python3
"""Generate shared Unicode17 SQL character data from official UCD source files."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def merged(ranges):
 out=[]
 for lo,hi in sorted(ranges):
  if out and lo<=out[-1][1]+1:out[-1][1]=max(out[-1][1],hi)
  else:out.append([lo,hi])
 return out

def property_ranges(path,name):
 ranges=[]
 for raw in path.read_text().splitlines():
  line=raw.split('#')[0].strip()
  if not line:continue
  fields=[s.strip()for s in line.split(';')]
  if len(fields)<2 or fields[1]!=name:continue
  points=fields[0].split('..');ranges.append((int(points[0],16),int(points[-1],16)))
 return merged(ranges)

def generate(directory):
 for name in ['DerivedCoreProperties','PropList']:
  if name+'-17.0.0.txt'not in (directory/(name+'.txt')).read_text().splitlines()[0]:raise ValueError('Expected official Unicode17.0.0 '+name)
 alpha=property_ranges(directory/'DerivedCoreProperties.txt','Alphabetic');space=property_ranges(directory/'PropList.txt','White_Space');number=[];pending=None
 for line in (directory/'UnicodeData.txt').read_text().splitlines():
  fields=line.split(';');cp=int(fields[0],16);name,category=fields[1:3]
  if name.endswith(', First>'):pending=(cp,category);continue
  if name.endswith(', Last>'):
   assert pending and pending[1]==category
   if category.startswith('N'):number.append((pending[0],cp))
   pending=None;continue
  if category.startswith('N'):number.append((cp,cp))
 paths=['DerivedCoreProperties.txt','UnicodeData.txt','PropList.txt'];data={'format':1,'unicode':'17.0.0','license':'Unicode License V3; see design/casefold.LICENSE and packaged CASEFOLD-LICENSE','sources':{name:{'url':'https://www.unicode.org/Public/17.0.0/ucd/'+name,'sha256':hashlib.sha256((directory/name).read_bytes()).hexdigest()}for name in paths},'alphabetic':alpha,'number':merged(number),'whitespace':space}
 (ROOT/'design/syntax-unicode.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n');print('Generated alphabetic/number/whitespace ranges:',len(alpha),len(data['number']),len(space))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path,required=True);generate(p.parse_args().source_dir)
