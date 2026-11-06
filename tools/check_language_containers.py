#!/usr/bin/env python3
"""Check configured containers, scoped routing and clipped painting in external apps."""
import argparse,json,os,shutil,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from check_language_feedback import statements
from build_language import build
F=json.loads((ROOT/'design/controls-cases.json').read_text())['layout']
def source(lang):
 c=lang=='c';java=lang=='java'
 out=['import static io.tuivory.Tuivory.*;import java.util.*;public class ContainerCases{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){']if java else['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <string.h>']
 if c:out.append('''static TuiResult paint(void*context,const char*id,TuiCanvas*child,int focused){(void)context;(void)id;(void)focused;TuiResult r=tui_canvas_write(child,-1,0,"界a界b한c","selection",0,9);tui_canvas_cursor(child,3,0,2);return r;}int main(void){''')
 elif not java:out.append('int main(){using namespace tuivory;')
 def check(e):out.append(('check('if java else'assert(')+e+');')
 def eq(e,v):check(e+'.equals('+quote(v)+')'if java else'!strcmp('+e+','+quote(v)+')'if c else e+'=='+quote(v))
 def assign(base,key,value):
  key=''.join([key.split('_')[0],*map(str.capitalize,key.split('_')[1:])])if java else key
  out.append(base+'.'+key+'='+ (quote(value)if isinstance(value,str)else str(int(value)if c and isinstance(value,bool)else value).lower())+';')
 def rect(values):return ('new Rect('if java else'(TuiRect){'if c else'Rect{')+','.join(str(values.get(k,0))for k in ['x','y','width','height'])+(')'if java else'}')
 for case in F:
  out.append('{TuiContainerOptions o={0};'if c else'{var o=new ContainerOptions();'if java else'{ContainerOptions o;')
  for k,v in case['options'].items():
   if k not in ['rows','columns']:assign('o',k,v)
   else:
    tracks=[]
    for t in v:tracks.append(('new Track('if java else'{')+','.join(str(t.get(k,0))for k in ['min','max','fixed','weight'])+(')'if java else'}'))
    if c:out.append('TuiTrack '+k+'[]={'+','.join(tracks)+'};o.'+k+'='+k+';o.'+('row_count'if k=='rows'else'column_count')+'='+str(len(v))+';')
    elif java:out.append('o.'+k+'=List.of('+','.join(tracks)+');')
    else:out.append('o.'+k+'={'+','.join(tracks)+'};')
  for n,i in enumerate(case['items']):
   base='i'+str(n);out.append('TuiLayoutItem '+base+'={0};'if c else'var '+base+'=new LayoutItem('+quote(i['id'])+');'if java else'LayoutItem '+base+';')
   for k,v in i.items():
    if k=='track':
     for tk,tv in v.items():assign(base+'.track',tk,tv)
    elif k=='area':out.append(base+'.area='+rect(v)+';')
    else:assign(base,k,v)
  names=','.join('i'+str(n)for n in range(len(case['items'])))
  out.append('TuiLayoutItem items[]={'+names+'};TuiLayoutResult*r=NULL;assert(tui_compute_container('+rect(case['bounds'])+',items,'+str(len(case['items']))+',&o,&r)==TUI_OK);'if c else'var items=List.of('+names+');var r=computeContainer('+rect(case['bounds'])+',items,o);'if java else'std::vector<LayoutItem>items{'+names+'};auto r=compute_container('+rect(case['bounds'])+',items,o);')
  for n,(id,x,y,w,h)in enumerate(case['expected']):
   b='tui_layout_rect_at(r,'+str(n)+')->'if c else'r.get('+str(n)+').'if java else'r['+str(n)+'].'
   eq(b+'id'+('()'if java else''),id)
   for k,v in [('x',x),('y',y),('width',w),('height',h)]:check(b+('rect().'+k+'()'if java else'rect.'+k)+'=='+str(v))
  if c:out.append('tui_layout_free(r);for(int w=0;w<25;w++)for(int h=0;h<10;h++){assert(tui_compute_container((TuiRect){2,3,w,h},items,'+str(len(case['items']))+',&o,&r)==TUI_OK);for(size_t n=0;n<tui_layout_rect_count(r);n++){TuiRect b=tui_layout_rect_at(r,n)->rect;assert(b.x>=2&&b.x+b.width<=2+w&&b.y>=3&&b.y+b.height<=3+h);}tui_layout_free(r);}')
  elif java:out.append('for(int w=0;w<25;w++)for(int h=0;h<10;h++)for(var n:computeContainer(new Rect(2,3,w,h),items,o)){var b=n.rect();check(b.x()>=2&&b.x()+b.width()<=2+w&&b.y()>=3&&b.y()+b.height()<=3+h);}')
  else:out.append('for(int w=0;w<25;w++)for(int h=0;h<10;h++)for(const auto&n:compute_container({2,3,w,h},items,o)){auto b=n.rect;assert(b.x>=2&&b.x+b.width<=2+w&&b.y>=3&&b.y+b.height<=3+h);}')
  out.append('}')
 if c:out.append('''{TuiLayoutItem items[]={{.id="a"},{.id="b"},{.id="popup",.modal=1},{.id="nested",.modal=1}};TuiContainerState*s=tui_container_state_new();assert(tui_container_reconcile(s,items,2)==TUI_OK);assert(tui_container_move_focus(s,items,2,0)==TUI_OK);assert(!strcmp(tui_container_focused(s),"b"));assert(tui_container_reconcile(s,items,3)==TUI_OK);assert(!strcmp(tui_container_focused(s),"popup"));assert(tui_container_reconcile(s,items,4)==TUI_OK);assert(tui_container_reconcile(s,items,2)==TUI_OK);assert(!strcmp(tui_container_focused(s),"b"));tui_container_state_free(s);}
 {TuiLayoutItem items[]={{.id="top",.track={.fixed=1}},{.id="editor",.track={.fixed=1}}};TuiContainerOptions o={.kind="column",.virtual_width=8,.virtual_height=3};TuiContainer*c=tui_container_new(items,2,&o);assert(c);assert(tui_container_move_focus(tui_container_state(c),items,2,0)==TUI_OK);assert(tui_container_scroll(c,2,1)==TUI_OK);TuiCanvas*canvas=tui_canvas_new(9,4,"dark","8");assert(tui_canvas_write(canvas,0,0,"Outside","body",0,9)==TUI_OK);assert(tui_container_draw(c,canvas,(TuiRect){1,1,5,1},paint,NULL)==TUI_OK);char*s=tui_canvas_ansi(canvas);assert(strstr(s,"\\033[2;3H\\033[?25h"));tui_string_free(s);const char*id=NULL;assert(tui_container_pointer(c,2,1,1,0,&id)==TUI_OK&&!strcmp(id,"editor"));assert(tui_container_pointer(c,50,50,0,1,&id)==TUI_OK&&!strcmp(id,"editor"));assert(!*tui_container_captured(tui_container_state(c)));s=tui_canvas_line(canvas,0);assert(!strcmp(s,"Outside  "));tui_string_free(s);s=tui_canvas_line(canvas,2);assert(!strcmp(s,"         "));tui_string_free(s);items[0].id="mutated";TuiLayoutItem invalid[]={{.id="same"},{.id="same"}};assert(tui_container_set_items(c,invalid,2,NULL)==TUI_INVALID);assert(tui_container_draw(c,canvas,(TuiRect){1,1,5,1},paint,NULL)==TUI_OK);tui_container_free(c);tui_canvas_free(canvas);}''')
 elif java:out.append('''{var a=new LayoutItem("a");var b=new LayoutItem("b");var popup=new LayoutItem("popup");popup.modal=true;var nested=new LayoutItem("nested");nested.modal=true;var s=new ContainerState();s.reconcile(List.of(a,b));check(s.moveFocus(List.of(a,b),false).equals("b"));s.reconcile(List.of(a,b,popup));check(s.focused.equals("popup"));s.reconcile(List.of(a,b,popup,nested));s.reconcile(List.of(a,b));check(s.focused.equals("b"));}
 {var top=new LayoutItem("top");top.track.fixed=1;var editor=new LayoutItem("editor");editor.track.fixed=1;var o=new ContainerOptions();o.kind="column";o.virtualWidth=8;o.virtualHeight=3;var c=new Container(List.of(top,editor),o);c.state.focused="editor";c.scrollX=2;c.scrollY=1;var canvas=new Canvas(9,4);canvas.write(0,0,"Outside","body");ChildPainter paint=(id,child,focused)->{child.write(-1,0,"界a界b한c","selection");child.write(0,99,"overflow","body");child.setCursor(3,0,2);};c.draw(canvas,new Rect(1,1,5,1),paint);check(canvas.cursorX==2&&canvas.cursorY==1);check(c.pointer(2,1,true,false).equals("editor"));check(c.pointer(50,50,false,true).equals("editor"));check(c.state.captured.isEmpty());check(canvas.lines().get(0).equals("Outside  "));check(canvas.lines().get(2).equals("         "));top.id="mutated";check(c.items().get(0).id.equals("top"));String before=canvas.ansi();boolean failed=false;try{c.draw(canvas,new Rect(1,1,5,1),(id,child,focused)->{throw new IllegalArgumentException("host");});}catch(IllegalArgumentException e){failed=true;}check(failed&&canvas.ansi().equals(before));}''')
 else:out.append('''{LayoutItem a,b,popup,nested;a.id="a";b.id="b";popup.id="popup";popup.modal=true;nested.id="nested";nested.modal=true;ContainerState s;s.reconcile({a,b});assert(s.move_focus({a,b})=="b");s.reconcile({a,b,popup});assert(s.focused=="popup");s.reconcile({a,b,popup,nested});s.reconcile({a,b});assert(s.focused=="b");}
 {LayoutItem top,editor;top.id="top";top.track.fixed=1;editor.id="editor";editor.track.fixed=1;ContainerOptions o;o.kind="column";o.virtual_width=8;o.virtual_height=3;Container c({top,editor},o);c.state.focused="editor";c.scroll_x=2;c.scroll_y=1;Canvas canvas(9,4);canvas.write(0,0,"Outside");auto paint=[](const std::string&,Canvas&child,bool){child.write(-1,0,"界a界b한c","selection");child.write(0,99,"overflow");child.set_cursor(3,0,2);};c.draw(canvas,{1,1,5,1},paint);assert(canvas.cursor&&canvas.cursor->first==2&&canvas.cursor->second==1);assert(c.pointer(2,1,true)=="editor");assert(c.pointer(50,50,false,true)=="editor");assert(c.state.captured.empty());assert(canvas.lines()[0]=="Outside  ");assert(canvas.lines()[2]=="         ");auto before=canvas.ansi();bool failed=false;try{c.draw(canvas,{1,1,5,1},[](const std::string&,Canvas&,bool){throw std::invalid_argument("host");});}catch(const std::invalid_argument&){failed=true;}assert(failed&&canvas.ansi()==before);}''')
 out.append('}}'if java else'return 0;}');return statements('\n'.join(out))

def main():
 p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
 with tempfile.TemporaryDirectory(prefix='tuivory-container-')as directory:
  base=Path(directory)
  if lang=='java':
   shutil.copy2(artifact,base/'tuivory.jar');src=base/'ContainerCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);run(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'ContainerCases'],base)
  else:
   src=base/('container.c'if lang=='c'else'container.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
   run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);run([base/'checked'],base,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
   if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
   run(flags+['-static','-o',base/'isolated'],base);run([base/'isolated'],base)
 print(lang+': configured geometry, scoped focus, virtual clipping and cursor projection passed')
if __name__=='__main__':main()
