#!/usr/bin/env python3
"""Check independent Canvas copies in isolated SDK/JAR apps."""
import argparse,json,os,shutil,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from check_language_feedback import statements
from build_language import build
F=json.loads((ROOT/'design/canvas-copy-cases.json').read_text())
def source(lang):
 c=lang=='c';java=lang=='java'
 out=['import static io.tuivory.Tuivory.*;import java.util.*;public class CanvasCopyCases{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){']if java else['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <string.h>','int main(void){'if c else'int main(){using namespace tuivory;']
 def check(e):out.append(('check('if java else'assert(')+e+');')
 def eq(e,v):check(e+'.equals('+quote(v)+')'if java else'!strcmp('+e+','+quote(v)+')'if c else e+'=='+quote(v))
 for theme in ['dark','light','blackwhite']:
  for colors in ['8','16','256','truecolor']:
   for case in F['cases']:
    r=','.join(map(str,case['region']));x,y=case['at'];w=case['width']
    if c:
     out.append('{TuiCanvas*s=tui_canvas_new(8,1,'+quote(theme)+','+quote(colors)+'),*d=tui_canvas_new('+str(w)+',1,'+quote(theme)+','+quote(colors)+');assert(s&&d);assert(tui_canvas_write(s,0,0,'+quote(F['text'])+',"selection",0,8)==TUI_OK);tui_canvas_cursor(s,4,0,2);assert(tui_canvas_blit(d,s,(TuiRect){'+r+'},'+str(x)+','+str(y)+')==TUI_OK);char*line=tui_canvas_line(d,0),*ansi=tui_canvas_ansi(d);')
     eq('line',case['expected']);check(('strstr(ansi,"\\033[?25h")!=NULL'if case['cursor']else'strstr(ansi,"\\033[?25h")==NULL'))
     if case['cursor']:check('strstr(ansi,"\\033[1;'+str(case['cursor'][0]+1)+'H\\033[?25h")!=NULL')
     out.append('tui_string_free(line);tui_string_free(ansi);tui_canvas_free(s);tui_canvas_free(d);}')
    elif java:
     out.append('{var palette=new Palette('+quote(theme)+','+quote(colors)+');var s=new Canvas(8,1,palette);var d=new Canvas('+str(w)+',1,palette);s.write(0,0,'+quote(F['text'])+',"selection");s.setCursor(4,0,2);d.blit(s,new Rect('+r+'),'+str(x)+','+str(y)+');')
     eq('d.lines().get(0)',case['expected']);check('d.cursorX=='+str(case['cursor'][0]if case['cursor']else -1));check('d.ansi().contains("\\033[?25h")=='+str(bool(case['cursor'])).lower());out.append('for(var cell:d.data[0])if(!cell.text.equals(" ")&&!cell.text.isEmpty())check(cell.style.equals(palette.style("selection")));}')
    else:
     out.append('{Palette palette('+quote(theme)+','+quote(colors)+');Canvas s(8,1,palette),d('+str(w)+',1,palette);s.write(0,0,'+quote(F['text'])+',"selection");s.set_cursor(4,0,2);d.blit(s,{'+r+'},'+str(x)+','+str(y)+');')
     eq('d.lines()[0]',case['expected']);check('d.cursor&&d.cursor->first=='+str(case['cursor'][0])if case['cursor']else'!d.cursor');check('(d.ansi().find("\\033[?25h")!=std::string::npos)=='+str(bool(case['cursor'])).lower());out.append('for(const auto&cell:d.data[0])if(cell.text!=" "&&!cell.text.empty())assert(cell.style.sgr()==palette.style("selection").sgr());}')
 if c:out.append('''{TuiCanvas*c=tui_canvas_new(8,1,"dark","8");assert(tui_canvas_write(c,0,0,"a界b한c","body",0,8)==TUI_OK);tui_canvas_cursor(c,4,0,2);assert(tui_canvas_blit(c,c,(TuiRect){0,0,6,1},2,0)==TUI_OK);char*s=tui_canvas_line(c,0);assert(!strcmp(s,"a a界b한"));tui_string_free(s);s=tui_canvas_ansi(c);assert(strstr(s,"\\033[1;7H\\033[?25h"));tui_string_free(s);assert(tui_canvas_fill(c,(TuiRect){7,0,1,1},"surface")==TUI_OK);s=tui_canvas_line(c,0);assert(!strcmp(s,"a a界b  "));tui_string_free(s);s=tui_canvas_ansi(c);assert(!strstr(s,"\\033[?25h"));tui_string_free(s);assert(tui_canvas_blit(c,c,(TuiRect){0,0,-1,1},0,0)==TUI_INVALID);tui_canvas_free(c);}''')
 elif java:out.append('''{var c=new Canvas(8,1);c.write(0,0,"a界b한c","body");c.setCursor(4,0,2);c.blit(c,new Rect(0,0,6,1),2,0);check(c.lines().get(0).equals("a a界b한"));check(c.cursorX==6);c.fill(new Rect(7,0,1,1),"surface");check(c.cursorX<0);check(c.lines().get(0).equals("a a界b  "));}''')
 else:out.append('''{Canvas c(8,1);c.write(0,0,"a界b한c");c.set_cursor(4,0,2);c.blit(c,{0,0,6,1},2,0);assert(c.lines()[0]=="a a界b한");assert(c.cursor&&c.cursor->first==6);c.fill({7,0,1,1});assert(!c.cursor);assert(c.lines()[0]=="a a界b  ");}''')
 out.append('}}'if java else'return 0;}');return statements('\n'.join(out))
def main():
 p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
 with tempfile.TemporaryDirectory(prefix='tuivory-canvas-copy-')as directory:
  base=Path(directory)
  if lang=='java':
   shutil.copy2(artifact,base/'tuivory.jar');src=base/'CanvasCopyCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);run(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'CanvasCopyCases'],base)
  else:
   src=base/('copy.c'if lang=='c'else'copy.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
   run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);run([base/'checked'],base,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
   if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
   run(flags+['-static','-o',base/'isolated'],base);run([base/'isolated'],base)
 print(lang+': cell copying, both wide edges, self-copy, styles and cursor occlusion passed')
if __name__=='__main__':main()
