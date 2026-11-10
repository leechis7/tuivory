#!/usr/bin/env python3
"""Exercise the same split-control transitions in the five independent SDKs."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
# Axis lengths and positions are local to the split; focus starts on the first pane.
CASES = json.loads((ROOT/'design/split-control-cases.json').read_text())['steps']


def run(command, **kwargs):
    return subprocess.check_output(command, cwd=ROOT, text=True, **kwargs)


def cases_source(call):
    return '\n'.join(f'{call}({total},"{action}",{pos},{inside},{side});' for total, action, pos, inside, side, *_ in CASES)


def expected():
    return ''.join(' '.join(map(str, case[5:]))+'\n' for case in CASES)


def main():
    env = dict(os.environ, PYTHONPATH=str(ROOT/'python/src'))
    py = '''from tuivory import Split, SplitControl
s,c=Split(10,12,30),SplitControl()
def run(t,a,p,i,d):
    if a == "key": c.toggle(s,t,d)
    elif a != "draw": c.pointer(s,t,p,bool(i),a,d)
    l=c.layout(s,t)
    print(l.first,l.divider,l.second,int(l.compact),int(c.captured),int(c.visible_focus(False)))
'''
    assert run([sys.executable,'-c',py+cases_source('run')],env=env) == expected(), 'Python'
    js = '''import {Split,SplitControl} from "./javascript/dist/index.js";
const s=new Split(10,12,30),c=new SplitControl();
function run(t,a,p,i,d){
 if(a==="key") c.toggle(s,t,d);
 else if(a!=="draw") c.pointer(s,t,p,!!i,a,d);
 const l=c.layout(s,t);
 console.log(l.first,l.divider,l.second,+l.compact,+c.captured,+c.visibleFocus(false));
}
'''
    assert run(['node','--input-type=module','-e',js+cases_source('run')]) == expected(), 'TypeScript/JavaScript'
    c = '''#include "tuivory.h"
#include <stdio.h>
#include <string.h>
static TuiSplit s={30,10,12};
static TuiSplitControl c={0};
static void run(int t,const char*a,int p,int i,int d){
 if(!strcmp(a,"key")) tui_split_control_toggle(&c,s,t,d);
 else if(strcmp(a,"draw")) tui_split_control_pointer(&c,&s,t,p,i,a,d);
 TuiSplitLayout l=tui_split_control_layout(&c,s,t);
 printf("%d %d %d %d %d %d\\n",l.first,l.divider,l.second,l.compact,c.pressed,tui_split_control_visible_focus(&c,0));
}
int main(void){
'''
    cpp = '''#include "tuivory.hpp"
#include <cstdio>
using namespace tuivory;
static Split s(10,12,30);
static SplitControl c;
static void run(int t,std::string_view a,int p,int i,int d){
 auto side=static_cast<SplitSide>(d);
 if(a=="key") c.toggle(s,t,side);
 else if(a!="draw") c.pointer(s,t,p,i,a,side);
 auto l=c.layout(s,t);
 std::printf("%d %d %d %d %d %d\\n",l.first,l.divider,l.second,l.compact,c.captured(),c.visible_focus(false));
}
int main(){
'''
    java = '''import static io.tuivory.Tuivory.*;
class SplitCases {
 static Split s=new Split(10,12,30);
 static SplitControl c=new SplitControl();
 static void run(int t,String a,int p,int i,int d){
  var side=SplitSide.values()[d];
  if(a.equals("key")) c.toggle(s,t,side);
  else if(!a.equals("draw")) c.pointer(s,t,p,i!=0,a,side);
  var l=c.layout(s,t);
  System.out.printf("%d %d %d %d %d %d%n",l.first(),l.divider(),l.second(),l.compact()?1:0,c.captured()?1:0,c.visibleFocus(false)?1:0);
 }
 public static void main(String[] args){
'''
    with tempfile.TemporaryDirectory(prefix='tuivory-split-') as tmp:
        tmp = Path(tmp)
        for lang, code, cc, args in [('c',c,'cc',[ROOT/'.cache/native/c/libtuivory.a']),
                                     ('cpp',cpp,'c++',[])]:
            src = tmp/f'test.{lang}'
            src.write_text(code+cases_source('run')+'\n}\n')
            binary = tmp/lang
            run([cc,'-Wall','-Wextra','-Werror','-I',ROOT/lang/'include',src,*args,'-o',binary])
            assert run([binary]) == expected(), lang
        src = tmp/'SplitCases.java'
        src.write_text(java+cases_source('run')+'\n}}\n')
        jar = ROOT/'.cache/packages/java'/f'tuivory-{(ROOT/"VERSION").read_text().strip()}.jar'
        run(['javac','--release','17','-cp',jar,'-d',tmp,src])
        assert run(['java','-cp',os.pathsep.join(map(str,(jar,tmp))),'SplitCases']) == expected(), 'Java'
    print(f'Five independent SDKs: {len(CASES)} split transitions each passed.')


if __name__ == '__main__':
    main()
