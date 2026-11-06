#!/usr/bin/env python3
"""Check literal editing against shared fixtures and isolated package consumers."""
from pathlib import Path
import argparse,json,os,shutil,tempfile
from check_languages import ROOT,quote,run
from build_language import build
F=json.loads((ROOT/'design/controls-cases.json').read_text())['text']
def native(lang):
    c=lang=='c'
    s=['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <string.h>','int main(void){'if c else'int main(){using namespace tuivory;']
    for f in F:
        s+=['{']
        if c:
            s += [f'TuiText*t=tui_text_new({quote(f["text"])});assert(t);TuiState state={{0}};state.read_only={int(f.get("read_only",False))};tui_text_options(t,state,{int(f.get("secret",False))},{int(not f.get("single_line",False))});TuiTextEvent e;']
        else:s += [f'Text t({quote(f["text"])});t.state.read_only={str(f.get("read_only",False)).lower()};t.secret={str(f.get("secret",False)).lower()};t.multiline={str(not f.get("single_line",False)).lower()};Event e;']
        for op in f['ops']:
            call=f'tui_text_handle(t,{quote(op["action"])},{quote(op.get("text",""))})'if c else f't.handle({quote(op["action"])},{quote(op.get("text",""))})'
            s += [f'e={call};assert(!strcmp(e.kind{ "" if c else ".c_str()"},{quote(op["kind"])}));assert(!strcmp(e.text{ "" if c else ".c_str()"},{quote(op.get("event_text",""))}));']
            if c:s+=['assert(e.result==TUI_OK);']
        if c:s += [f'assert(!strcmp(tui_text_value(t),{quote(f["expected"])}));assert(tui_text_cursor(t)=={f["cursor"]});tui_text_free(t);']
        else:s += [f'assert(t.value=={quote(f["expected"])});assert(t.cursor=={f["cursor"]});']
        s+=['}']
    if c:
        s += ['{TuiText*t=tui_text_new("a\\r\\n한é😀");assert(tui_text_select_bytes(t,3,9)==TUI_OK);size_t a,b;assert(tui_text_selection_bytes(t,&a,&b)==TUI_OK&&a==3&&b==9);assert(tui_text_replace_bytes(t,4,9,"bad").result==TUI_INVALID);assert(!strcmp(tui_text_value(t),"a\\r\\n한é😀"));assert(tui_text_replace_bytes(t,3,9,"[red]\\r\\n").result==TUI_OK);assert(!strcmp(tui_text_value(t),"a\\r\\n[red]\\r\\n😀"));tui_text_handle(t,"undo","");assert(!strcmp(tui_text_value(t),"a\\r\\n한é😀"));tui_text_free(t);}',
        '{TuiText*t=tui_text_new("한😀x");TuiState st={0};tui_text_options(t,st,0,0);for(int w=1;w<9;w++){TuiCanvas*c=tui_canvas_new(12,4,"light","8");tui_canvas_write(c,0,0,"OUTSIDE","body",0,12);assert(tui_text_draw(t,c,(TuiRect){3,1,w,1},1)==TUI_OK);char*line=tui_canvas_line(c,0);assert(!strncmp(line,"OUTSIDE",7));free(line);tui_canvas_free(c);}tui_text_free(t);}',
        'assert(!tui_text_new("\\xf8\\x90\\x80\\x80"));']
        s.insert(3,'#include <stdlib.h>')
    else:
        s += ['{Text t("a\\r\\n한é😀");t.select_bytes(3,9);auto bytes=t.selection_bytes();assert(bytes.first==3&&bytes.second==9);bool bad=false;try{t.replace_bytes(4,9,"bad");}catch(const std::invalid_argument&){bad=true;}assert(bad&&t.value=="a\\r\\n한é😀");t.replace_bytes(3,9,"[red]\\r\\n");assert(t.value=="a\\r\\n[red]\\r\\n😀");t.handle("undo");assert(t.value=="a\\r\\n한é😀");}',
        '{Text t("한😀x");t.multiline=false;for(int w=1;w<9;w++){Canvas c(12,4,Palette("light","8"));c.write(0,0,"OUTSIDE");t.draw(c,{3,1,w,1});assert(c.lines()[0].substr(0,7)=="OUTSIDE");}}']
    s+=['return 0;}'];return '\n'.join(s)
def java():
    s=['import static io.tuivory.Tuivory.*;','public class TextCases{static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){']
    for f in F:
        s += ['{var t=new Text('+quote(f['text'])+');',f't.state.readOnly={str(f.get("read_only",False)).lower()};t.secret={str(f.get("secret",False)).lower()};t.multiline={str(not f.get("single_line",False)).lower()};Event e;']
        for op in f['ops']:s += [f'e=t.handle({quote(op["action"])},{quote(op.get("text",""))});check(e.kind().equals({quote(op["kind"])}));check(e.text().equals({quote(op.get("event_text",""))}));']
        s += [f'check(t.value().equals({quote(f["expected"])}));check(t.cursor=={f["cursor"]});','}']
    s += ['{var t=new Text("a\\r\\n한é😀");t.selectBytes(3,9);check(t.selectionBytes()[0]==3&&t.selectionBytes()[1]==9);boolean bad=false;try{t.replaceBytes(4,9,"bad");}catch(IllegalArgumentException e){bad=true;}check(bad&&t.value().equals("a\\r\\n한é😀"));t.replaceBytes(3,9,"[red]\\r\\n");check(t.value().equals("a\\r\\n[red]\\r\\n😀"));t.handle("undo");check(t.value().equals("a\\r\\n한é😀"));}',
    '{var t=new Text("한😀x");t.multiline=false;for(int w=1;w<9;w++){var c=new Canvas(12,4,new Palette("light","8"));c.write(0,0,"OUTSIDE","body");t.draw(c,new Rect(3,1,w,1),true);check(c.lines().get(0).startsWith("OUTSIDE"));}}','}}']
    return '\n'.join(s)
def main():
    p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
    with tempfile.TemporaryDirectory(prefix='tuivory-text-')as d:
        base=Path(d)
        if lang=='java':
            shutil.copy2(artifact,base/'tuivory.jar');src=base/'TextCases.java';src.write_text(java());run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);run(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'TextCases'],base)
        else:
            src=base/('text.c'if lang=='c'else'text.cpp');src.write_text(native(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
            checked=flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'];run(checked,base);run([base/'checked'],base,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
            if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
            run(flags+['-static','-o',base/'isolated'],base);run([base/'isolated'],base)
    print(lang+': shared literal grapheme editing, UTF-8 atomic ranges, secret/read-only behavior and bounded drawing passed')
if __name__=='__main__':main()
