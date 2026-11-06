#!/usr/bin/env python3
"""Verify independent-language Tree packages against shared behavior fixtures."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache/validation/languages'
CACHE.mkdir(parents=True,exist_ok=True)


def run(cmd,cwd=ROOT,env=None):
    subprocess.run(list(map(str,cmd)),cwd=cwd,env=env,check=True)


def quote(value):
    return json.dumps(value,ensure_ascii=False)


def native_cases(language):
    f=json.loads((ROOT/'design/tree-navigation.json').read_text())
    nodes=[]
    if language=='c':
        lines=['#include "tuivory.h"','#include <assert.h>','#include <string.h>','int main(void){','TuiNode nodes[]={']
        for n in f['nodes']:
            fields=','.join('.'+key+'='+quote(n.get(key,''))for key in ['id','name','parent','secondary','icon','ascii_icon'])
            lines.append('{'+fields+',.branch='+str(int(n.get('branch',False)))+'},')
        lines+=['};TuiTree*t=tui_tree_new(nodes,sizeof(nodes)/sizeof(nodes[0]));assert(t);TuiEvent e;']
        for case in json.loads((ROOT/'design/language-unicode-cases.json').read_text())['cases']:
            lines.append(f'assert(tui_cells({quote(case["text"])})=={case["cells"]});')
        for s in f['steps']:
            call=f'tui_tree_click(t,{s["column"]},{s["row"]},{f["height"]})'if s['action']=='click'else f'tui_tree_handle(t,{quote(s["action"])},{f["height"]})'
            lines+=[f'e={call};assert(!strcmp(tui_tree_selected(t),{quote(s["selected"])}));',f'assert(tui_tree_scroll(t)=={s["scroll"]});assert(tui_tree_horizontal(t)=={s["horizontal"]});',f'assert(!strcmp(e.kind,{quote(s.get("event",""))}));assert(!strcmp(e.id,{quote(s.get("id",""))}));']
            for n in f['nodes']:lines.append(f'assert(tui_tree_expanded(t,{quote(n["id"])})=={int(n["id"] in s["expanded"])});')
            lines.append('{const char*ids[64];size_t n=tui_tree_visible(t,ids,64);assert(n=='+str(len(s['visible']))+');')
            for i,id in enumerate(s['visible']):lines.append(f'assert(!strcmp(ids[{i}],{quote(id)}));')
            lines.append('}')
        lines+=['tui_tree_free(t);return 0;}']
    else:
        lines=['#include "tuivory.hpp"','#include <cassert>','int main(){using namespace tuivory;std::vector<Node>nodes;']
        for n in f['nodes']:
            lines.append('{Node n;'+''.join('n.'+key+'='+quote(n.get(key,''))+';'for key in ['id','name','parent','secondary','icon','ascii_icon'])+'n.branch='+str(n.get('branch',False)).lower()+';nodes.push_back(n);}')
        lines+=['Tree t(nodes);Event e;']
        for case in json.loads((ROOT/'design/language-unicode-cases.json').read_text())['cases']:
            lines.append(f'assert(cells({quote(case["text"])})=={case["cells"]});')
        for s in f['steps']:
            call=f't.click({s["column"]},{s["row"]},{f["height"]})'if s['action']=='click'else f't.handle({quote(s["action"])},{f["height"]})'
            lines.append(f'e={call};assert(t.selected=={quote(s["selected"])});assert(t.scroll=={s["scroll"]});assert(t.horizontal=={s["horizontal"]});assert(e.kind=={quote(s.get("event",""))});assert(e.id=={quote(s.get("id",""))});')
            expected=','.join(map(quote,s['expanded']))
            lines.append('{std::set<std::string>expected={'+expected+'};assert(t.expanded==expected);}')
            lines.append('{auto rows=t.visible();assert(rows.size()=='+str(len(s['visible']))+');')
            for i,id in enumerate(s['visible']):lines.append(f'assert(rows[{i}].id=={quote(id)});')
            lines.append('}')
        lines+=['}']
    states=json.loads((ROOT/'design/interaction-cases.json').read_text())['states']
    state_lines=[]
    for case in states:
        if language=='c':
            state_lines.append('{TuiState state={0};char markers[7];'+''.join('state.'+k+'='+str(int(v))+';'for k,v in case['state'].items())+'assert(!strcmp(tui_state_role(state),'+quote(case['role'])+'));assert(tui_state_markers(state,markers)==TUI_OK);assert(!strcmp(markers,'+quote(case['markers'])+'));'+''.join('assert(tui_state_'+k+'(state)=='+str(int(case[k]))+');'for k in ['focusable','activatable','editable'])+'}')
        else:
            state_lines.append('{State state;'+''.join('state.'+k+'='+str(v).lower()+';'for k,v in case['state'].items())+'assert(state.role()=='+quote(case['role'])+');assert(state.markers()=='+quote(case['markers'])+');'+''.join('assert(state.'+k+'()=='+str(case[k]).lower()+');'for k in ['focusable','activatable','editable'])+'}')
    lines[-1:-1]=state_lines
    return '\n'.join(lines)+'\n'


def check_native(language):
    from build_language import build
    build(language)
    with tempfile.TemporaryDirectory(prefix='tuivory-'+language+'-')as directory:
        base=Path(directory)
        shutil.copytree(ROOT/language/'include',base/'include')
        source=base/('consumer.c'if language=='c'else'consumer.cpp')
        source.write_text(native_cases(language))
        if language=='c':
            shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a')
            cmd=['cc','-std=c11','-Wall','-Wextra','-Werror','-static','-I',base/'include',source,base/'libtuivory.a','-o',base/'consumer']
        else:
            cmd=['c++','-std=c++17','-Wall','-Wextra','-Werror','-static','-I',base/'include',source,'-o',base/'consumer']
        run(cmd,cwd=base);run([base/'consumer'],cwd=base)
        print(f'{language}: isolated external static-link consumer and shared Tree cases passed')
    if language=='c':
        run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',ROOT/'c/include',ROOT/'c/src/tuivory.c',ROOT/'c/tests/components.c','-o',CACHE/'c-sanitize'])
        run([CACHE/'c-sanitize'],env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))
        print('C ASan/UBSan passed; leak detection disabled because ptrace host disallows LeakSanitizer')
    else:
        run(['c++','-std=c++17','-Wall','-Wextra','-Werror','-Wno-missing-field-initializers','-fsanitize=address,undefined','-I',ROOT/'cpp/include',ROOT/'cpp/tests/components.cpp','-o',CACHE/'cpp-sanitize'])
        run([CACHE/'cpp-sanitize'],env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'))


def check_java():
    from build_language import build
    jar=build('java')
    f=json.loads((ROOT/'design/tree-navigation.json').read_text())
    lines=['import static io.tuivory.Tuivory.*;','import java.util.*;','public class Consumer {static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){var nodes=new ArrayList<Node>();']
    for n in f['nodes']:
        lines.append('{var n=new Node('+quote(n['id'])+','+quote(n.get('name',''))+','+quote(n.get('parent',''))+');n.branch='+str(n.get('branch',False)).lower()+';nodes.add(n);}')
    lines+=['var tree=new Tree(nodes);Event e;']
    for case in json.loads((ROOT/'design/language-unicode-cases.json').read_text())['cases']:
        lines.append(f'check(cells({quote(case["text"])})=={case["cells"]});')
    for s in f['steps']:
        call=f'tree.click({s["column"]},{s["row"]},{f["height"]})'if s['action']=='click'else f'tree.handle({quote(s["action"])},{f["height"]})'
        lines.append(f'e={call};check(tree.selected.equals({quote(s["selected"])}));check(tree.scroll=={s["scroll"]});check(tree.horizontal=={s["horizontal"]});check(e.kind().equals({quote(s.get("event",""))}));check(e.id().equals({quote(s.get("id",""))}));')
        lines.append('check(tree.expanded.equals(new HashSet<>(List.of('+','.join(map(quote,s['expanded']))+'))));')
        lines.append('check(tree.visible().stream().map(n->n.id).toList().equals(List.of('+','.join(map(quote,s['visible']))+')));')
    for case in json.loads((ROOT/'design/interaction-cases.json').read_text())['states']:
        lines.append('{var state=new State();'+''.join('state.'+('readOnly'if k=='read_only'else k)+'='+str(v).lower()+';'for k,v in case['state'].items())+'check(state.role().equals('+quote(case['role'])+'));check(state.markers().equals('+quote(case['markers'])+'));'+''.join('check(state.'+k+'()=='+str(case[k]).lower()+');'for k in ['focusable','activatable','editable'])+'}')
    lines+=['}}']
    with tempfile.TemporaryDirectory(prefix='tuivory-java-')as directory:
        base=Path(directory);shutil.copy2(jar,base/'tuivory.jar');(base/'Consumer.java').write_text('\n'.join(lines))
        run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp','tuivory.jar','Consumer.java'],cwd=base)
        run(['java','-cp','tuivory.jar'+os.pathsep+'.','Consumer'],cwd=base)
    tests=CACHE/'java-test-classes';tests.mkdir(exist_ok=True)
    run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',jar,'-d',tests,*sorted((ROOT/'java/src/test').rglob('*.java'))])
    run(['java','-cp',str(jar)+os.pathsep+str(tests),'io.tuivory.ComponentsTest'])
    print('java: isolated external JAR consumer/shared Tree cases and all palettes passed')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language',choices=['c','cpp','java'],required=True)
    args=parser.parse_args()
    if args.language=='java':check_java()
    else:check_native(args.language)
