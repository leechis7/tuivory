#!/usr/bin/env python3
"""Verify cell-stack geometry and supporting components in external native/JAR apps."""
import argparse,json,os,shutil,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from check_language_feedback import statements
from build_language import build
F=json.loads((ROOT/'design/layout-cases.json').read_text())

def source(lang):
 c=lang=='c';java=lang=='java'
 out=['import static io.tuivory.Tuivory.*;import java.util.*;public class LayoutCases{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){']if java else['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <string.h>','int main(void){'if c else'int main(){using namespace tuivory;']
 def check(e):out.append('check('+e+');'if java else'assert(('+e+'));')
 def eq(e,v):check(e+'.equals('+quote(v)+')'if java else'!strcmp('+e+','+quote(v)+')'if c else e+'=='+quote(v))
 def state(base,values):
  for k,v in values.items():out.append(base+'.'+('readOnly'if java and k=='read_only'else k)+'='+str(int(v)if c else v).lower()+';')
 def items(values,name):
  fields=lambda i:','.join([quote(i['id']),str(i.get('min',1)),str(i.get('preferred',0)),str(i.get('weight',1))])
  out.append('TuiStackItem '+name+'[]={'+','.join('{'+fields(i)+'}'for i in values)+'};'if c else'var '+name+'=List.of('+','.join('new StackItem('+fields(i)+')'for i in values)+');'if java else'std::vector<StackItem>'+name+'{'+','.join('{'+fields(i)+'}'for i in values)+'};')
 for s in F['spacing']:
  out.append('{TuiSpacingTokens t;assert(tui_spacing_tokens('+quote(s['density'])+','+str(s['columns'])+',&t)==TUI_OK);'if c else'{var t=SpacingTokens.forWidth('+quote(s['density'])+','+str(s['columns'])+');'if java else'{auto t=SpacingTokens::for_width('+quote(s['density'])+','+str(s['columns'])+');')
  for k in ['gap','padding','control_gap']:check(('t.'+('controlGap'if k=='control_gap'else k)+'()'if java else't.'+k)+'=='+str(s[k]))
  out.append('}')
 for s in F['stacks']:
  out.append('{');data=s.get('items',F['items']);items(data,'items')
  out.append('TuiStackResult*r=NULL;assert(tui_stack_layout(items,'+str(len(data))+','+str(s['total'])+','+str(s['gap'])+',&r)==TUI_OK);'if c else'var r=stackLayout(items,'+str(s['total'])+','+str(s['gap'])+');'if java else'auto r=stack_layout(items,'+str(s['total'])+','+str(s['gap'])+');')
  check(('tui_stack_slot_count(r)'if c else'r.slots().size()'if java else'r.slots.size()')+'=='+str(len(data)))
  check(('tui_stack_gap(r)'if c else'r.gap()'if java else'r.gap')+'=='+str(s['actual_gap']))
  for i,(id,start,size)in enumerate(s['slots']):
   base='tui_stack_slot_at(r,'+str(i)+')->'if c else'r.slots().get('+str(i)+').'if java else'r.slots['+str(i)+'].'
   eq(base+'id'+('()'if java else''),id)
   for k,v in [('start',start),('size',size)]:check(base+k+('()'if java else'')+'=='+str(v))
  check(('tui_stack_hidden_count(r)'if c else'r.hidden().size()'if java else'r.hidden.size()')+'=='+str(len(s['hidden'])))
  for i,id in enumerate(s['hidden']):eq('tui_stack_hidden_at(r,'+str(i)+')'if c else'r.hidden().get('+str(i)+')'if java else'r.hidden['+str(i)+']',id)
  out.append('tui_stack_free(r);}'if c else'}')
 for s in F['badges']:
  out.append('{TuiBadge b={0};'if c else'{var b=new Badge();'if java else'{Badge b;')
  out.append('b.label='+quote(s['label'])+';');state('b.state',s.get('state',{}))
  if 'count'in s:out.append(('b.has_count=1;'if c else'')+'b.count='+str(s['count'])+('ULL'if c or not java else'L')+';')
  if 'limit'in s:out.append('b.limit='+str(s['limit'])+('L'if java else'ULL')+';')
  out.append('TuiFeedbackView*v=NULL;assert(tui_badge_line(&b,40,&v)==TUI_OK);const TuiFeedbackRow*r=tui_feedback_row(v,0);'if c else'var r=b.line(40);'if java else'auto r=b.line(40);')
  eq('r->text'if c else'r.text()'if java else'r.text',s['text']);eq('r->role'if c else'r.role()'if java else'r.role',s['role'])
  out.append('tui_feedback_free(v);}'if c else'}')
 for s in F['chips']:
  out.append('{TuiChip chip={0};'if c else'{var chip=new Chip();'if java else'{Chip chip;')
  for k in ['id','label']:out.append('chip.'+k+'='+quote(s[k])+';')
  out.append('chip.removable='+str(int(s['removable'])if c else s['removable']).lower()+';');state('chip.state',s['state'])
  eq('tui_chip_request_remove(&chip).kind'if c else'chip.requestRemove().kind()'if java else'chip.request_remove().kind',s['request'])
  if c:out.append('for(int w=0;w<40;w++){TuiFeedbackView*v=NULL;assert(tui_chip_line(&chip,w,&v)==TUI_OK);const TuiFeedbackRow*r=tui_feedback_row(v,0);assert(tui_cells(r->text)<=w);for(size_t i=0;i<r->span_count;i++)assert(r->spans[i].start+r->spans[i].width<=w);tui_feedback_free(v);}')
  elif java:out.append('for(int w=0;w<40;w++){var r=chip.line(w);check(cells(r.text())<=w);for(var s:r.spans())check(s.start()+s.width()<=w);}')
  else:out.append('for(int w=0;w<40;w++){auto r=chip.line(w);assert(cells(r.text)<=w);for(const auto&s:r.spans)assert(s.start+s.width<=w);}')
  out.append('}')
 for keys in F['duplicate_keys']+[ [' 　'] ]:
  if c:out.append('{TuiShortcut items[]={'+','.join('{'+quote(k)+',"",0,0}'for k in keys)+'};assert(!tui_help_new(items,'+str(len(keys))+'));}')
  elif java:out.append('{boolean invalid=false;try{new Help(List.of('+','.join('new Shortcut('+quote(k)+',"")'for k in keys)+'));}catch(IllegalArgumentException e){invalid=true;}check(invalid);}')
  else:out.append('{bool invalid=false;try{Help h({'+','.join('{'+quote(k)+',"",0,false}'for k in keys)+'});}catch(const std::invalid_argument&){invalid=true;}assert(invalid);}')
 out.append('{');items(F['items'],'base_items')
 if c:out.append('''TuiShortcut hints[]={{"x","Remove",1,1},{"F1","Help",10,0}};TuiHelp*h=tui_help_new(hints,2);assert(h);hints[1].text="Changed";TuiFeedbackView*v=NULL;assert(tui_help_layout(h,40,1,&v)==TUI_OK);assert(!strcmp(tui_feedback_row(v,0)->text,"[F1] Help"));tui_feedback_free(v);assert(tui_help_layout(h,40,2,&v)==TUI_OK);assert(!strcmp(tui_feedback_row(v,1)->role,"disabled"));tui_feedback_free(v);for(int width=0;width<241;width++){TuiStackResult*r=NULL;assert(tui_stack_layout(base_items,2,width,2,&r)==TUI_OK);int end=0;for(size_t i=0;i<tui_stack_slot_count(r);i++){const TuiStackSlot*s=tui_stack_slot_at(r,i);assert(s->start>=end&&s->start+s->size<=width);if(s->size)end=s->start+s->size;}tui_stack_free(r);for(int vertical=0;vertical<2;vertical++){TuiLayoutResult*layout=NULL;assert(tui_stack_rects((TuiRect){2,3,width,20},base_items,2,(TuiSpacingTokens){2,1,2,80},vertical,&layout)==TUI_OK);for(size_t i=0;i<tui_layout_rect_count(layout);i++){TuiRect r=tui_layout_rect_at(layout,i)->rect;assert(r.x>=2&&r.x+r.width<=2+width&&r.y>=3&&r.y+r.height<=23);}tui_layout_free(layout);}}TuiDrawerPlacement drawer;assert(tui_drawer_layout((TuiRect){0,0,30,10},24,40,&drawer)==TUI_OK&&drawer.overlay);assert(tui_drawer_layout((TuiRect){0,0,100,10},24,40,&drawer)==TUI_OK&&!drawer.overlay);const char*themes[]={"dark","light","blackwhite"},*colors[]={"8","16","256","truecolor"};for(int t=0;t<3;t++)for(int k=0;k<4;k++)for(int w=0;w<20;w++){TuiCanvas*c=tui_canvas_new(w,6,themes[t],colors[k]);TuiBadge b={.label="Selected",.has_count=1,.count=123,.state={.selected=1}};TuiChip chip={.id="tag",.label="한글",.state={.disabled=1},.removable=1};assert(tui_badge_draw(&b,c,(TuiRect){0,0,w,1})==TUI_OK);assert(tui_chip_draw(&chip,c,(TuiRect){0,1,w,1})==TUI_OK);assert(tui_help_draw(h,c,(TuiRect){0,2,w,4})==TUI_OK);char*ansi=tui_canvas_ansi(c);assert(ansi&&!strstr(ansi,"\\033[?25h"));tui_string_free(ansi);tui_canvas_free(c);}tui_help_free(h);''')
 elif java:out.append('''var remove=new Shortcut("x","Remove");remove.priority=1;remove.disabled=true;var help=new Shortcut("F1","Help");help.priority=10;var h=new Help(List.of(remove,help));help.text="Changed";check(h.layout(40,1).get(0).text().equals("[F1] Help"));check(h.layout(40,2).get(1).role().equals("disabled"));for(int width=0;width<241;width++){var r=stackLayout(base_items,width,2);int end=0;for(var s:r.slots()){check(s.start()>=end&&s.start()+s.size()<=width);if(s.size()>0)end=s.start()+s.size();}for(boolean vertical:List.of(false,true))for(var n:stackRects(new Rect(2,3,width,20),base_items,new SpacingTokens(2,1,2),vertical).rects()){var box=n.rect();check(box.x()>=2&&box.x()+box.width()<=2+width&&box.y()>=3&&box.y()+box.height()<=23);}}check(drawerLayout(new Rect(0,0,30,10),24,40).overlay());check(!drawerLayout(new Rect(0,0,100,10),24,40).overlay());for(String theme:List.of("dark","light","blackwhite"))for(String colors:List.of("8","16","256","truecolor"))for(int w=0;w<20;w++){var palette=new Palette(theme,colors);var c=new Canvas(w,6,palette);var b=new Badge();b.label="Selected";b.count=123L;b.state.selected=true;b.draw(c,new Rect(0,0,w,1));var chip=new Chip("tag","한글");chip.state.disabled=true;chip.removable=true;chip.draw(c,new Rect(0,1,w,1));h.draw(c,new Rect(0,2,w,4));check(c.cursorX<0);if(w>0)check(c.data[0][0].style.background()==palette.style("selection").background());}''')
 else:out.append('''std::vector<Shortcut>hints{{"x","Remove",1,true},{"F1","Help",10,false}};Help h(hints);hints[1].text="Changed";assert(h.layout(40,1)[0].text=="[F1] Help");assert(h.layout(40,2)[1].role=="disabled");for(int width=0;width<241;width++){auto r=stack_layout(base_items,width,2);int end=0;for(const auto&s:r.slots){assert(s.start>=end&&s.start+s.size<=width);if(s.size)end=s.start+s.size;}for(bool vertical:{false,true})for(const auto&n:stack_rects({2,3,width,20},base_items,{2,1,2,80},vertical).rects){auto box=n.rect;assert(box.x>=2&&box.x+box.width<=2+width&&box.y>=3&&box.y+box.height<=23);}}assert(drawer_layout({0,0,30,10},24,40).overlay);assert(!drawer_layout({0,0,100,10},24,40).overlay);for(const auto&theme:{"dark","light","blackwhite"})for(const auto&colors:{"8","16","256","truecolor"})for(int w=0;w<20;w++){Palette palette(theme,colors);Canvas c(w,6,palette);Badge b;b.label="Selected";b.count=123;b.state.selected=true;b.draw(c,{0,0,w,1});Chip chip;chip.id="tag";chip.label="한글";chip.state.disabled=true;chip.removable=true;chip.draw(c,{0,1,w,1});h.draw(c,{0,2,w,4});assert(!c.cursor);if(w)assert(c.data[0][0].style.background==palette.style("selection").background);}''')
 out.append('}')
 if c:out.append('''{char id[]="owned";TuiStackItem items[]={{id,1,1,0}};TuiStackResult*r=NULL;assert(tui_stack_layout(items,1,4,0,&r)==TUI_OK);id[0]='X';assert(!strcmp(tui_stack_slot_at(r,0)->id,"owned"));tui_stack_free(r);TuiStackItem invalid[]={{"same",1,0,1},{"same",1,0,1}};assert(tui_stack_layout(invalid,2,10,1,&r)==TUI_INVALID);TuiBadge bad={.count=9007199254740992ULL,.has_count=1};TuiFeedbackView*v=NULL;assert(tui_badge_line(&bad,10,&v)==TUI_INVALID);}''')
 elif java:out.append('''{boolean invalid=false;try{stackLayout(List.of(new StackItem("same"),new StackItem("same")),10,1);}catch(IllegalArgumentException e){invalid=true;}check(invalid);}''')
 else:out.append('''{bool invalid=false;try{stack_layout({{"same"},{"same"}},10,1);}catch(const std::invalid_argument&){invalid=true;}assert(invalid);}''')
 out.append('}}'if java else'return 0;}');return statements('\n'.join(out))

def main():
 p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
 with tempfile.TemporaryDirectory(prefix='tuivory-layout-')as directory:
  base=Path(directory)
  if lang=='java':
   shutil.copy2(artifact,base/'tuivory.jar');src=base/'LayoutCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);run(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'LayoutCases'],base)
  else:
   src=base/('layout.c'if lang=='c'else'layout.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
   run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);run([base/'checked'],base,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
   if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
   run(flags+['-static','-o',base/'isolated'],base);run([base/'isolated'],base)
 print(lang+': shared spacing/weighted geometry, hidden IDs, badge/chip requests, Unicode hint keys and palette checks passed')
if __name__=='__main__':main()
