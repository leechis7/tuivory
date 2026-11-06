#!/usr/bin/env python3
"""Run shared focus-scope fixtures through independent external language APIs."""
import argparse,json,os,shutil,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from build_language import build
F=json.loads((ROOT/'design/interaction-cases.json').read_text())
SFLAGS=['disabled','read_only','busy','selected','edited','invalid']
camel=lambda k:''.join(v.title()if i else v for i,v in enumerate(k.split('_')))
def source(lang):
 c=lang=='c';java=lang=='java';counter=0
 if java:s=['import static io.tuivory.Tuivory.*;import java.util.*;public class FocusCases{static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){']
 else:s=['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <string.h>','#include <stdio.h>','int main(void){'if c else'int main(){using namespace tuivory;']
 def check(expr):return ('check('if java else'assert(')+expr+');'
 def eq(expr,v):return check(expr+'.equals('+quote(v)+')')if java else check('!strcmp('+expr+','+quote(v)+')')if c else check(expr+'=='+quote(v))
 def targets(items):
  nonlocal counter
  name='items'+str(counter);counter+=1
  if c:
   s.append(f'TuiFocusTarget {name}[{max(1,len(items))}]={{0}};')
   for i,t in enumerate(items):
    s.append(f'{name}[{i}].id={quote(t["id"])};{name}[{i}].hidden={int(t.get("hidden",False))};')
    for k in SFLAGS:s.append(f'{name}[{i}].state.{k}={int(t.get("state",{}).get(k,False))};')
  else:
   s.append(f'var {name}=new ArrayList<FocusTarget>();'if java else f'std::vector<FocusTarget>{name};')
   for t in items:
    if java:s.append('{var state=new State();')
    else:s.append('{State state;')
    for k in SFLAGS:s.append(f'state.{camel(k)if java else k}={str(t.get("state",{}).get(k,False)).lower()};')
    s.append(f'{name}.add(new FocusTarget({quote(t["id"])},state,{str(t.get("hidden",False)).lower()}));}}'if java else f'{name}.push_back({{{quote(t["id"])},state,{str(t.get("hidden",False)).lower()}}});}}')
  return name
 root=targets(F['root']);s.append(f'TuiFocus*f=tui_focus_new("root",{root},{len(F["root"])});assert(f);'if c else f'var f=new Focus("root",{root});'if java else f'Focus f("root",{root});')
 for step in F['steps']:
  op=step['op'];call=''
  if op=='move':s.append(f'tui_focus_move(f,{int(step.get("backwards",False))});'if c else f'f.move({str(step.get("backwards",False)).lower()});')
  elif op=='focus':s.append(check((f'tui_focus_focus(f,{quote(step["id"])})'if c else f'f.focus({quote(step["id"])})')+'=='+(str(int(step['accepted']))if c else str(step['accepted']).lower())))
  elif op in ['open','update']:
   items=targets(step['targets'])
   if op=='open':call=f'tui_focus_open(f,{quote(step["id"])},{items},{len(step["targets"])},{quote(step.get("initial",""))},{int(step.get("dismissible",False))})'if c else f'f.open({quote(step["id"])},{items},{quote(step.get("initial",""))},{str(step.get("dismissible",False)).lower()})'
   else:call=f'tui_focus_update(f,{quote(step["id"])},{items},{len(step["targets"])})'if c else f'f.update({quote(step["id"])},{items})'
  elif op=='close':call=f'tui_focus_close(f,{quote(step["id"])})'if c else f'f.close({quote(step["id"])})'
  elif op=='route':s.append(check((f'tui_focus_route(f,{quote(step["target"])}).blocked'if c else f'f.route({quote(step["target"])}).blocked()'if java else f'f.route({quote(step["target"])}).blocked')+'=='+(str(int(step['blocked']))if c else str(step['blocked']).lower())))
  elif op=='request':s.append(eq('tui_focus_request_close(f).id'if c else'f.requestClose().map(PopupCloseRequest::id).orElse("")'if java else'(f.request_close()?f.request_close()->id:std::string())',step['request']))
  if call:
   if c:s.append(check(call+'=='+('TUI_INVALID'if step.get('error')else'TUI_OK')))
   elif step.get('error'):s.append('{boolean bad=false;try{'+call+';}catch(IllegalArgumentException e){bad=true;}check(bad);}'if java else'{bool bad=false;try{'+call+';}catch(const std::invalid_argument&){bad=true;}assert(bad);}')
   else:s.append(call+';')
  s += [eq('tui_focus_scope(f)'if c else'f.scopeId()'if java else'f.scope_id()',step['expect_scope']),eq('tui_focus_focused(f)'if c else'f.focused()',step['expect_focus']),check(('tui_focus_depth(f)'if c else'f.depth()')+'=='+str(step['expect_depth']))]
 if c:s+=['tui_focus_free(f);TuiFocusTarget root={.id="original"};f=tui_focus_new("root",&root,1);root.state.disabled=1;assert(!strcmp(tui_focus_focused(f),"original"));for(int i=0;i<64;i++){char id[20];snprintf(id,sizeof(id),"popup%d",i);assert(tui_focus_open(f,id,NULL,0,"",0)==TUI_OK);}assert(tui_focus_open(f,"overflow",NULL,0,"",0)==TUI_INVALID);assert(tui_focus_depth(f)==64);assert(!*tui_focus_request_close(f).id);assert(!tui_focus_route(f,"").blocked);assert(tui_focus_route(f,"root").blocked);tui_focus_free(f);return 0;}']
 elif java:s+=['{var target=new FocusTarget("original");var stack=new Focus("root",List.of(target));target.state().disabled=true;check(stack.focused().equals("original"));for(int i=0;i<64;i++)stack.open("p"+i,List.of(),"",false);boolean bad=false;try{stack.open("overflow",List.of());}catch(IllegalArgumentException e){bad=true;}check(bad&&stack.depth()==64);check(stack.requestClose().isEmpty());check(!stack.route("").blocked()&&stack.route("root").blocked());}}}']
 else:s+=['{FocusTarget target;target.id="original";Focus stack("root",{target});target.state.disabled=true;assert(stack.focused()=="original");for(int i=0;i<64;i++)stack.open("p"+std::to_string(i),{},"",false);bool bad=false;try{stack.open("overflow",{});}catch(const std::invalid_argument&){bad=true;}assert(bad&&stack.depth()==64);assert(!stack.request_close());assert(!stack.route().blocked&&stack.route("root").blocked);}return 0;}']
 return '\n'.join(s)
def main():
 p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
 with tempfile.TemporaryDirectory(prefix='tuivory-focus-')as d:
  base=Path(d)
  if lang=='java':
   shutil.copy2(artifact,base/'tuivory.jar');src=base/'FocusCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);run(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'FocusCases'],base)
  else:
   src=base/('focus.c'if lang=='c'else'focus.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
   run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);run([base/'checked'],base,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
   if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
   run(flags+['-static','-o',base/'isolated'],base);run([base/'isolated'],base)
 print(lang+': shared focus scope input routing, updates/restoration, close requests and atomic failures passed')
if __name__=='__main__':main()
