#!/usr/bin/env python3
"""Apply existing workspace fixtures to independent C/C++/Java consumers."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import tempfile
from check_languages import ROOT,quote,run
from build_language import build
import json
F=json.loads((ROOT/'design/components-cases.json').read_text())

def native(language):
    items=F['tabs']['items']
    if language=='c':
        lines=['#include "tuivory.h"','#include <assert.h>','#include <string.h>','int main(void){','TuiTab items[]={']
        for t in items:lines.append('{'+','.join('.'+k+'='+quote(t.get(k,''))for k in ['id','title'])+','+','.join('.'+k+'='+str(int(t.get(k,False)))for k in ['edited','closable','disabled'])+'},')
        lines+=['};TuiTabs*t=tui_tabs_new(items,4);assert(t);TuiEvent e;']
        for s in F['tabs']['steps']:lines.append('e=tui_tabs_handle(t,'+quote(s['action'])+');assert(!strcmp(e.kind,'+quote(s['event'])+'));assert(!strcmp(e.id,'+quote(s['id'])+'));assert(!strcmp(tui_tabs_active(t),'+quote(s['active'])+'));assert(!strcmp(tui_tabs_focused(t),'+quote(s['focused'])+'));')
        lines+=['tui_tabs_free(t);']
        for case in F['tabs']['layouts']:
            lines+=['{size_t n=0;TuiTabCell views[8];t=tui_tabs_new(items,4);assert(t);tui_tabs_handle(t,"last");',f'assert(tui_tabs_layout(t,{case["width"]},views,8,&n)==TUI_OK);assert(n=={len(case["ids"])});assert(tui_tabs_first(t)=={case["first"]});']
            for i,id in enumerate(case['ids']):lines.append(f'assert(!strcmp(views[{i}].id,{quote(id)}));assert(views[{i}].start+views[{i}].width<={case["width"]});assert(tui_cells(views[{i}].text)<=views[{i}].width);')
            lines+=['tui_tabs_free(t);}']
        lines+=['TuiPathItem path[]={{"r","root"},{"f","folder"},{"c","현재.sql"}};TuiLine*line;char*text;']
        for c in F['paths']:lines.append(f'line=tui_breadcrumbs(path,3,{c["width"]});assert(line);text=tui_line_text(line);assert(text);assert(!strcmp(text,{quote(c["text"])}));tui_string_free(text);tui_line_free(line);')
        lines+=['TuiStatusItem status[]={{"help","F1 Help","hint",1},{"err","Failure","error",100},{"draft","Draft","edited",30}};']
        for c in F['status']:lines.append(f'line=tui_status_line(status,3,{c["width"]});assert(line);text=tui_line_text(line);assert(text);assert(!strcmp(text,{quote(c["text"])}));assert(tui_line_omitted(line)=={c["omitted"]});tui_string_free(text);tui_line_free(line);')
        lines+=['TuiSplit split={7,3,4};for(int n=0;n<40;n++){TuiSplitLayout l=tui_split_layout(split,n);assert(l.first+l.divider+l.second==n);if(n<8){assert(l.compact);assert(l.first==0);}}assert(tui_split_resize(&split,30,10));assert(tui_split_layout(split,30).first==10);',
                '{TuiTab one={"one","ax",0,0,0};TuiTabCell cell;size_t n;t=tui_tabs_new(&one,1);assert(tui_tabs_layout(t,30,&cell,1,&n)==TUI_OK);e=tui_tabs_click(t,cell.start+tui_cells(cell.text)-2,30);assert(!strcmp(e.kind,"activate"));tui_tabs_free(t);}',
                '{TuiTab test[]={{"a","조회",0,1,0},{"b","Draft",0,0,0}};TuiTabCell v[2];size_t n;t=tui_tabs_new(test,2);TuiCanvas*c=tui_canvas_new(32,3,"light","8");assert(t&&c);tui_tabs_handle(t,"next");assert(tui_tabs_layout(t,32,v,2,&n)==TUI_OK&&n==2);int close=v[0].start+tui_cells(v[0].text)-2;assert(tui_tabs_draw_ascii(t,c,(TuiRect){0,0,32,3},1,1)==TUI_OK);char*rail=tui_canvas_line(c,2);assert(rail&&rail[v[0].start]==\'+\'&&rail[v[0].start+1]==\' \'&&rail[v[1].start]==\'-\');tui_string_free(rail);assert(!strcmp(tui_tabs_click(t,close,32).kind,"close"));tui_canvas_free(c);tui_tabs_free(t);}',
                'return 0;}']
    else:
        lines=['#include "tuivory.hpp"','#include <cassert>','int main(){using namespace tuivory;std::vector<Tab> items={']
        for t in items:lines.append('{'+quote(t['id'])+','+quote(t['title'])+','+','.join(str(t.get(k,False)).lower()for k in ['edited','closable','disabled'])+'},')
        lines+=['};Tabs tabs(items);Event e;']
        for s in F['tabs']['steps']:lines.append(f'e=tabs.handle({quote(s["action"])});assert(e.kind=={quote(s["event"])}&&e.id=={quote(s["id"])});assert(tabs.active=={quote(s["active"])}&&tabs.focused=={quote(s["focused"])});')
        for c in F['tabs']['layouts']:
            lines.append(f'{{Tabs t(items);t.focused="c";auto cells=t.layout({c["width"]});assert(t.first=={c["first"]});assert(cells.size()=={len(c["ids"])});')
            for i,id in enumerate(c['ids']):lines.append(f'assert(cells[{i}].id=={quote(id)});assert(cells[{i}].start+cells[{i}].width<={c["width"]});assert(tuivory::cells(cells[{i}].text)<=cells[{i}].width);')
            lines.append('}')
        lines+=['std::vector<PathItem>path={{"r","root"},{"f","folder"},{"c","현재.sql"}};']
        for c in F['paths']:lines.append(f'assert(breadcrumbs(path,{c["width"]}).text()=={quote(c["text"])});')
        lines+=['std::vector<StatusItem>status={{"help","F1 Help","hint",1},{"err","Failure","error",100},{"draft","Draft","edited",30}};']
        for c in F['status']:lines.append(f'{{auto line=status_line(status,{c["width"]});assert(line.text()=={quote(c["text"])});assert(line.omitted=={c["omitted"]});}}')
        lines+=['Split split(3,4,7);for(int n=0;n<40;n++){auto l=split.layout(n);assert(l.first+l.divider+l.second==n);if(n<8){assert(l.compact);assert(l.first==0);}}assert(split.resize(30,10));assert(split.layout(30).first==10);',
                '{Tabs t({{"one","ax",false,false,false}});auto cell=t.layout(30).front();assert(t.click(cell.start+cells(cell.text)-2,30).kind=="activate");}',
                '{Tabs t({{"a","조회",false,true,false},{"b","Draft"}});Canvas c(32,3);t.handle("next");auto v=t.layout(32);t.draw(c,{0,0,32,3},true,true);auto rail=c.lines().at(2);assert(rail.at(v[0].start)==43&&rail.at(v[0].start+1)==32&&rail.at(v[1].start)==45);assert(t.click(v[0].start+cells(v[0].text)-2,32).kind=="close");}',
                '}']
    return '\n'.join(lines)


def java():
    lines=['import static io.tuivory.Tuivory.*;','import java.util.*;','public class Workspace{static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[] args){var items=new ArrayList<Tab>();']
    for t in F['tabs']['items']:lines.append('{var t=new Tab('+quote(t['id'])+','+quote(t['title'])+');'+''.join('t.'+k+'='+str(t.get(k,False)).lower()+';'for k in ['edited','closable','disabled'])+'items.add(t);}')
    lines+=['var tabs=new Tabs(items);Event e;']
    for s in F['tabs']['steps']:lines.append(f'e=tabs.handle({quote(s["action"])});check(e.kind().equals({quote(s["event"])}));check(e.id().equals({quote(s["id"])}));check(tabs.active.equals({quote(s["active"])}));check(tabs.focused.equals({quote(s["focused"])}));')
    for c in F['tabs']['layouts']:
        lines.append(f'{{var t=new Tabs(items);t.focused="c";var views=t.layout({c["width"]});check(t.first=={c["first"]});check(views.size()=={len(c["ids"])});')
        for i,id in enumerate(c['ids']):lines.append(f'check(views.get({i}).id().equals({quote(id)}));check(views.get({i}).start()+views.get({i}).width()<={c["width"]});check(cells(views.get({i}).text())<=views.get({i}).width());')
        lines.append('}')
    lines+=['var path=List.of(new PathItem("r","root"),new PathItem("f","folder"),new PathItem("c","현재.sql"));']
    for c in F['paths']:lines.append(f'check(breadcrumbs(path,{c["width"]}).text().equals({quote(c["text"])}));')
    lines+=['var status=List.of(new StatusItem("help","F1 Help","hint",1),new StatusItem("err","Failure","error",100),new StatusItem("draft","Draft","edited",30));']
    for c in F['status']:lines.append(f'{{var line=statusLine(status,{c["width"]});check(line.text().equals({quote(c["text"])}));check(line.omitted=={c["omitted"]});}}')
    lines+=['var split=new Split(3,4,7);for(int n=0;n<40;n++){var l=split.layout(n);check(l.first()+l.divider()+l.second()==n);if(n<8){check(l.compact());check(l.first()==0);}}check(split.resize(30,10));check(split.layout(30).first()==10);',
            '{var t=new Tabs(List.of(new Tab("one","ax")));var cell=t.layout(30).get(0);check(t.click(cell.start()+cells(cell.text())-2,30).kind().equals("activate"));}',
            '{var a=new Tab("a","조회");a.closable=true;var t=new Tabs(List.of(a,new Tab("b","Draft")));var c=new Canvas(32,3);t.handle("next");var v=t.layout(32);t.draw(c,new Rect(0,0,32,3),true,true);var rail=c.lines().get(2);check(rail.charAt(v.get(0).start())==43&&rail.charAt(v.get(0).start()+1)==32&&rail.charAt(v.get(1).start())==45);check(t.click(v.get(0).start()+cells(v.get(0).text())-2,32).kind().equals("close"));}',
            '}}']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--language',choices=['c','cpp','java'],required=True);args=parser.parse_args();language=args.language
    artifact=build(language)
    with tempfile.TemporaryDirectory(prefix='tuivory-workspace-')as directory:
        base=Path(directory)
        if language=='java':
            shutil.copy2(artifact,base/'tuivory.jar');artifact=base/'tuivory.jar'
            source=base/'Workspace.java';source.write_text(java());run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',artifact,source],base);run(['java','-cp',str(artifact)+os.pathsep+str(base),'Workspace'],base)
        else:
            source=base/('workspace.c'if language=='c'else'workspace.cpp');source.write_text(native(language));cmd=['cc'if language=='c'else'c++','-std=c11'if language=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',ROOT/language/'include',source]
            if language=='c':cmd +=[ROOT/'c/src/tuivory.c']
            cmd+=['-o',base/'workspace'];run(cmd,base);run([base/'workspace'],base,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
            shutil.copytree(ROOT/language/'include',base/'include')
            isolated=['cc'if language=='c'else'c++','-std=c11'if language=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-static','-I',base/'include',source]
            if language=='c':
                shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');isolated.append(base/'libtuivory.a')
            isolated+=['-o',base/'isolated'];run(isolated,base);run([base/'isolated'],base)
    print(language+': shared tab navigation/layout/click, breadcrumbs, status priorities and compact split passed')

if __name__=='__main__':main()
