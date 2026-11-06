#!/usr/bin/env python3
"""Validate independent menu hierarchy, spans, placement and requests externally."""
import argparse,json,os,shutil,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from build_language import build
F=json.loads((ROOT/'design/menu-cases.json').read_text())
TEXT=['id','parent','label','secondary','shortcut','mnemonic','icon','ascii_icon']
def source(lang):
 c=lang=='c';java=lang=='java'
 s=['import static io.tuivory.Tuivory.*;import java.util.*;public class MenuCases{static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){var items=new ArrayList<MenuItem>();']if java else['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <string.h>','int main(void){'if c else'int main(){using namespace tuivory;',f'TuiMenuItem items[{len(F["items"])}]={{0}};'if c else'std::vector<MenuItem>items;']
 def check(expr):return ('check('if java else'assert(')+expr+');'
 def eq(expr,v):return check(expr+'.equals('+quote(v)+')')if java else check('!strcmp('+expr+','+quote(v)+')')if c else check(expr+'=='+quote(v))
 for i,item in enumerate(F['items']):
  if c:
   for k in TEXT:s.append(f'items[{i}].{k}={quote(item.get(k,""))};')
   for k in ['disabled','separator']:s.append(f'items[{i}].{k}={int(item.get(k,False))};')
  else:
   s.append('{var v=new MenuItem('+quote(item['id'])+');'if java else'{MenuItem v;')
   for k in TEXT:s.append('v.'+('asciiIcon'if java and k=='ascii_icon'else k)+'='+quote(item.get(k,''))+';')
   for k in ['disabled','separator']:s.append(f'v.{k}={str(item.get(k,False)).lower()};')
   s.append('items.add(v);}'if java else'items.push_back(v);}')
 for case in F['scenarios']:
  s += ['{',f'TuiMenu*m=tui_menu_new(items,{len(F["items"])});assert(m);TuiMenuEvent e;'if c else'var m=new Menu(items);MenuEvent e;'if java else'Menu m(items);MenuEvent e;']
  s += ['e='+ (f'tui_menu_open(m,{quote(case["root"])},{quote(case["caller"])})'if c else f'm.open({quote(case["root"])},{quote(case["caller"])})')+';',eq('e.kind()'if java else'e.kind','open')]
  for step in case['steps']:
   s += ['e='+(f'tui_menu_handle(m,{quote(step["action"])},{quote(step.get("value",""))},5)'if c else f'm.handle({quote(step["action"])},{quote(step.get("value",""))},5)')+';',eq('e.kind()'if java else'e.kind',step['event']),eq('e.id()'if java else'e.id',step['id']),eq('e.return_id'if c else'e.returnId()'if java else'e.return_id',case['caller']),check(('tui_menu_opened(m)'if c else'm.opened()')+'=='+(str(int(not step.get('closed',False)))if c else str(not step.get('closed',False)).lower()))]
   if c:s.append(check('e.result==TUI_OK'))
   if not step.get('closed'):
    s += [eq('tui_menu_focused(m)'if c else'm.focusedId()'if java else'm.focused_id()',step.get('focus',''))]
    if c:s+=['{const char*path[32];'+check('tui_menu_path(m,path,32)=='+str(len(step.get('path',[]))))]
    else:s.append(check(('m.path().size()')+'=='+str(len(step.get('path',[])))))
    for n,id in enumerate(step.get('path',[])):s.append(eq(f'path[{n}]'if c else f'm.path().get({n})'if java else f'm.path()[{n}]',id))
    if c:s.append('}')
  if c:s.append('tui_menu_free(m);')
  s.append('}')
 if c:s += ['{TuiMenu*m=tui_menu_new(items,10);assert(m);tui_menu_open(m,"file","origin");tui_menu_handle(m,"next","",4);tui_menu_handle(m,"activate","",4);tui_menu_handle(m,"next","",4);TuiMenuItem bad[11];memcpy(bad,items,sizeof(items));bad[10]=items[0];assert(tui_menu_set_items(m,bad,11).result==TUI_INVALID);assert(!strcmp(tui_menu_focused(m),"deep"));assert(tui_menu_set_items(m,items,10).result==TUI_OK);assert(!strcmp(tui_menu_focused(m),"deep"));memcpy(bad,items,sizeof(items));bad[4].disabled=1;TuiMenuEvent e=tui_menu_set_items(m,bad,10);assert(!strcmp(e.kind,"close")&&!strcmp(e.return_id,"origin")&&!tui_menu_opened(m));tui_menu_free(m);}',
 '{TuiMenuItem bad[]={ {.id="@back"} };assert(!tui_menu_new(bad,1));TuiMenuItem cycle[]={{.id="a",.parent="b"},{.id="b",.parent="a"}};assert(!tui_menu_new(cycle,2));TuiMenuItem duplicate[]={{.id="a",.mnemonic="f"},{.id="b",.mnemonic="F"}};assert(!tui_menu_new(duplicate,2));}']
 elif java:s += ['{var m=new Menu(items);m.open("file","origin");m.handle("next");m.handle("activate");m.handle("next");var bad=new ArrayList<MenuItem>(items);bad.add(items.get(0));boolean invalid=false;try{m.setItems(bad);}catch(IllegalArgumentException e){invalid=true;}check(invalid&&m.focusedId().equals("deep"));m.setItems(items);check(m.focusedId().equals("deep"));var changed=m.items();changed.get(4).disabled=true;var e=m.setItems(changed);check(e.kind().equals("close")&&e.returnId().equals("origin")&&!m.opened());}']
 else:s += ['{Menu m(items);m.open("file","origin");m.handle("next");m.handle("activate");m.handle("next");auto bad=items;bad.push_back(items[0]);bool invalid=false;try{m.set_items(bad);}catch(const std::invalid_argument&){invalid=true;}assert(invalid&&m.focused_id()=="deep");m.set_items(items);assert(m.focused_id()=="deep");auto changed=items;changed[4].disabled=true;auto e=m.set_items(changed);assert(e.kind=="close"&&e.return_id=="origin"&&!m.opened());}']
 if c:s += ['{TuiMenu*m=tui_menu_new(items,10);assert(m);tui_menu_open(m,"file","editor");for(int ascii=0;ascii<2;ascii++)for(int w=0;w<90;w++)for(int h=0;h<12;h++){const TuiMenuRow*rows;size_t count;assert(tui_menu_layout(m,w,h,ascii,&rows,&count)==TUI_OK);assert(count<=(size_t)h);for(size_t i=0;i<count;i++){assert(tui_cells(rows[i].text)<=w);for(size_t j=0;j<rows[i].span_count;j++){assert(rows[i].spans[j].start+rows[i].spans[j].width<=w);assert(tui_cells(rows[i].spans[j].text)<=rows[i].spans[j].width);}}TuiMenuBarLayout bar;assert(tui_menu_bar_layout(m,w,&bar)==TUI_OK);for(size_t i=0;i<bar.count;i++){assert(bar.cells[i].start+bar.cells[i].width<=w);assert(tui_cells(bar.cells[i].text)<=bar.cells[i].width);}}for(int w=0;w<40;w++)for(int h=0;h<20;h++){TuiRect r=tui_menu_placement((TuiRect){70,18,1,1},(TuiRect){3,2,w,h},40,20);assert(r.x>=3&&r.x+r.width<=3+w&&r.y>=2&&r.y+r.height<=2+h);}const char*themes[]={"dark","light","blackwhite"},*colors[]={"8","16","256","truecolor"};for(int t=0;t<3;t++)for(int k=0;k<4;k++){TuiCanvas*c=tui_canvas_new(40,12,themes[t],colors[k]);assert(tui_menu_draw(m,c,(TuiRect){1,1,38,10},0)==TUI_OK);TuiRect content;assert(tui_menu_draw_popup(m,c,(TuiRect){1,1,38,10},"Popup",1,0,&content)==TUI_OK);assert(content.x==3&&content.y==3&&content.width==34&&content.height==6);for(int w=0;w<12;w++)for(int h=0;h<8;h++){assert(tui_menu_draw_popup(m,c,(TuiRect){0,0,w,h},"Popup",99999,1,&content)==TUI_OK);assert(content.width>=0&&content.width<=w&&content.height>=0&&content.height<=h);}char*ansi=tui_canvas_ansi(c);assert(!strstr(ansi,"\\033[?25h"));tui_string_free(ansi);assert(!strcmp(tui_menu_click_id(m,"off").kind,""));tui_canvas_free(c);}tui_menu_free(m);}return 0;}']
 elif java:s += ['{var m=new Menu(items);m.open("file","editor");for(boolean ascii:List.of(false,true))for(int w=0;w<90;w++)for(int h=0;h<12;h++){var rows=m.layout(w,h,ascii);check(rows.size()<=h);for(var r:rows){check(cells(r.text())<=w);for(var span:r.spans()){check(span.start()+span.width()<=w);check(cells(span.text())<=span.width());}}for(var cell:m.barLayout(w).cells()){check(cell.start()+cell.width()<=w);check(cells(cell.text())<=cell.width());}}for(int w=0;w<40;w++)for(int h=0;h<20;h++){var r=menuPlacement(new Rect(70,18,1,1),new Rect(3,2,w,h),40,20);check(r.x()>=3&&r.x()+r.width()<=3+w&&r.y()>=2&&r.y()+r.height()<=2+h);}for(String theme:List.of("dark","light","blackwhite"))for(String colors:List.of("8","16","256","truecolor")){var c=new Canvas(40,12,new Palette(theme,colors));m.draw(c,new Rect(1,1,38,10),false);var content=m.drawPopup(c,new Rect(1,1,38,10),"Popup",1,false);check(content.equals(new Rect(3,3,34,6)));for(int w=0;w<12;w++)for(int h=0;h<8;h++){var r=m.drawPopup(c,new Rect(0,0,w,h),"Popup",99999,true);check(r.width()>=0&&r.width()<=w&&r.height()>=0&&r.height()<=h);}check(c.cursorX<0);check(m.clickId("off").kind().isEmpty());}}}}']
 else:s += ['{Menu m(items);m.open("file","editor");for(bool ascii:{false,true})for(int w=0;w<90;w++)for(int h=0;h<12;h++){auto rows=m.layout(w,h,ascii);assert(rows.size()<=static_cast<std::size_t>(h));for(const auto&r:rows){assert(cells(r.text)<=w);for(const auto&span:r.spans){assert(span.start+span.width<=w);assert(cells(span.text)<=span.width);}}for(const auto&cell:m.bar_layout(w).cells){assert(cell.start+cell.width<=w);assert(cells(cell.text)<=cell.width);}}for(int w=0;w<40;w++)for(int h=0;h<20;h++){auto r=menu_placement({70,18,1,1},{3,2,w,h},40,20);assert(r.x>=3&&r.x+r.width<=3+w&&r.y>=2&&r.y+r.height<=2+h);}for(const auto&theme:{"dark","light","blackwhite"})for(const auto&colors:{"8","16","256","truecolor"}){Canvas c(40,12,Palette(theme,colors));m.draw(c,{1,1,38,10});auto content=m.draw_popup(c,{1,1,38,10},"Popup");assert(content.x==3&&content.y==3&&content.width==34&&content.height==6);for(int w=0;w<12;w++)for(int h=0;h<8;h++){auto r=m.draw_popup(c,{0,0,w,h},"Popup",99999,true);assert(r.width>=0&&r.width<=w&&r.height>=0&&r.height<=h);}assert(!c.cursor);for(const auto&row:c.data)for(const auto&cell:row)assert(!cell.style.underline);assert(m.click_id("off").kind.empty());}}return 0;}']
 return '\n'.join(s)
def main():
 p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
 with tempfile.TemporaryDirectory(prefix='tuivory-menu-')as d:
  base=Path(d)
  if lang=='java':
   shutil.copy2(artifact,base/'tuivory.jar');src=base/'MenuCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);run(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'MenuCases'],base)
  else:
   src=base/('menu.c'if lang=='c'else'menu.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
   run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);run([base/'checked'],base,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
   if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
   run(flags+['-static','-o',base/'isolated'],base);run([base/'isolated'],base)
 print(lang+': shared hierarchical menu requests/return IDs, atomic updates, spans/bar overflow, selection-only painting and popup geometry passed')
if __name__=='__main__':main()
