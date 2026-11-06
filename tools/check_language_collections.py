#!/usr/bin/env python3
"""Validate independent list/picker/search data using isolated native SDK/JARs."""
import argparse,json,os,shutil,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from build_language import build
F=json.loads((ROOT/'design/collections-cases.json').read_text())
M=json.loads((ROOT/'design/casefold.json').read_text())['mappings']
TEXT=['id','label','secondary','shortcut','icon','ascii_icon','parent']
def source(lang):
 c=lang=='c';java=lang=='java';s=[]
 def check(expr):return ('check('if java else'assert(')+expr+');'
 def eq(expr,v):return check(expr+'.equals('+quote(v)+')')if java else check('!strcmp('+expr+','+quote(v)+')')if c else check(expr+'=='+quote(v))
 pairs=[(chr(int(key)),v)for key,v in M.items()]+[(i['text'],i['expected'])for i in F['fold']]
 if java:
  s=['import static io.tuivory.Tuivory.*;import java.util.*;public class CollectionCases{static void check(boolean v){if(!v)throw new AssertionError();}static void folds(){', 'String[]inputs={'+','.join(quote(a)for a,_ in pairs)+'};','String[]expected={'+','.join(quote(b)for _,b in pairs)+'};','for(int i=0;i<inputs.length;i++){check(fold(inputs[i]).equals(expected[i]));check(fold(fold(inputs[i])).equals(expected[i]));}}public static void main(String[]args){folds();var items=new ArrayList<Item>();']
 else:
  s=['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <string.h>','static const char*folds[][2]={'+','.join('{'+quote(a)+','+quote(b)+'}'for a,b in pairs)+'};','int main(void){'if c else'int main(){using namespace tuivory;']
  if c:s += ['for(size_t i=0;i<sizeof(folds)/sizeof(folds[0]);i++){char*value=tui_casefold(folds[i][0]);assert(value&&!strcmp(value,folds[i][1]));char*again=tui_casefold(value);assert(again&&!strcmp(again,value));tui_string_free(value);tui_string_free(again);}assert(!tui_casefold("\xf8\x90\x80\x80"));'.replace('"\xf8\x90\x80\x80"','"\\xf8\\x90\\x80\\x80"'),f'TuiItem items[{len(F["items"])}]={{0}};']
  else:s += ['for(const auto&row:folds){assert(fold(row[0])==row[1]);assert(fold(fold(row[0]))==row[1]);}bool invalid=false;try{fold("\\xf8\\x90\\x80\\x80");}catch(const std::invalid_argument&){invalid=true;}assert(invalid);std::vector<Item>items;']
 for i,item in enumerate(F['items']):
  if c:
   for k in TEXT:s.append(f'items[{i}].{k}={quote(item.get(k,""))};')
   for k in ['disabled','separator']:s.append(f'items[{i}].{k}={int(item.get(k,False))};')
  else:
   s.append('{var v=new Item('+quote(item['id'])+');'if java else'{Item v;')
   for k in TEXT:s.append('v.'+('asciiIcon'if java and k=='ascii_icon'else k)+'='+quote(item.get(k,''))+';')
   for k in ['disabled','separator']:s.append(f'v.{k}={str(item.get(k,False)).lower()};')
   s.append('items.add(v);}'if java else'items.push_back(v);}')
 s.append(f'TuiList*m=tui_list_new(items,{len(F["items"])});assert(m);TuiCollectionEvent e;'if c else'var m=new ListModel(items);Event e;'if java else'List m(items);Event e;')
 for step in F['list']:
  if 'query'in step:call=f'tui_list_set_query(m,{quote(step["query"])})'if c else f'm.{"setQuery"if java else"set_query"}({quote(step["query"])})'
  elif 'click'in step:call=f'tui_list_click_id(m,{quote(step["click"])})'if c else f'm.{"clickId"if java else"click_id"}({quote(step["click"])})'
  else:call=f'tui_list_handle(m,{quote(step["action"])},{step.get("height",3)})'if c else f'm.handle({quote(step["action"])},{step.get("height",3)})'
  s += ['e='+call+';',eq('e.kind()'if java else'e.kind',step['kind']),eq('e.id()'if java else'e.id',step.get('id','')),eq('e.query'if c else'e.text()'if java else'e.text',step.get('text',''))]
  if c:s.append(check('e.result==TUI_OK'))
  for key in ['focused','selected']:
   if key in step:s.append(eq(f'tui_list_{key}(m)'if c else'm.'+key,step[key]))
 if c:s += ['tui_list_free(m);',f'TuiSearchPicker*p=tui_picker_new(items,{len(F["items"])});assert(p);']
 else:s.append('var p=new SearchPicker(items);'if java else'SearchPicker p(items);')
 for step in F['picker']:
  if 'click'in step:call=f'tui_picker_click_id(p,{quote(step["click"])})'if c else f'p.{"clickId"if java else"click_id"}({quote(step["click"])})'
  else:call=f'tui_picker_handle(p,{quote(step["action"])},{quote(step.get("text",""))},4)'if c else f'p.handle({quote(step["action"])},{quote(step.get("text",""))},4)'
  s += ['e='+call+';',eq('e.kind()'if java else'e.kind',step['kind']),eq('e.id()'if java else'e.id',step.get('id','')),eq('e.query'if c else'e.text()'if java else'e.text',step.get('event_text',''))]
  if c:s.append(check('e.result==TUI_OK'))
  if 'open'in step:s.append(check(('tui_picker_opened(p)'if c else'p.open')+'=='+(str(int(step['open']))if c else str(step['open']).lower())))
  if 'value'in step:s.append(eq('tui_picker_value(p)'if c else'p.value',step['value']))
  if 'focused'in step:s.append(eq('tui_list_focused(tui_picker_list(p))'if c else'p.list.focused',step['focused']))
 if c:s += ['tui_picker_free(p);',
 '{TuiItem duplicate[]={{.id="same"},{.id="same"}};TuiList*m=tui_list_new(items,7);assert(tui_list_set_items(m,duplicate,2)==TUI_INVALID);assert(!strcmp(tui_list_focused(m),"go"));const TuiCollectionRow*rows;size_t n;assert(tui_list_layout(m,40,20,0,&rows,&n)==TUI_OK);assert(!strcmp(tui_list_click(m,-1,1,20).kind,""));assert(!strcmp(tui_list_click(m,40,1,20).kind,""));for(size_t i=0;i<n;i++){if(!strcmp(rows[i].id,"x"))assert(!strcmp(tui_list_click(m,2,(int)i,20).kind,""));}tui_list_free(m);}',
 '{const char*themes[]={"dark","light","blackwhite"},*colors[]={"8","16","256","truecolor"};TuiSearchPicker*p=tui_picker_new(items,7);tui_picker_handle(p,"open","",4);tui_picker_handle(p,"insert","한한한한한한한한한한한한한한한한한한한한",4);for(int t=0;t<3;t++)for(int k=0;k<4;k++)for(int w=0;w<20;w++){TuiCanvas*c=tui_canvas_new(24,8,themes[t],colors[k]);assert(tui_picker_draw(p,c,(TuiRect){2,1,w,6},1,0)==TUI_OK);const TuiCollectionRow*rows;size_t n;assert(tui_picker_layout(p,w,6,0,&rows,&n)==TUI_OK);for(size_t i=0;i<n;i++)assert(tui_cells(rows[i].text)<=w);tui_canvas_free(c);}tui_picker_free(p);}', 'return 0;}']
 elif java:s += ['{boolean bad=false;try{m.setItems(List.of(new Item("same"),new Item("same")));}catch(IllegalArgumentException e2){bad=true;}check(bad);p.handle("open");p.handle("insert","한".repeat(40),4);for(String theme:List.of("dark","light","blackwhite"))for(String colors:List.of("8","16","256","truecolor"))for(int w=0;w<20;w++){var c=new Canvas(24,8,new Palette(theme,colors));p.draw(c,new Rect(2,1,w,6),true,false);for(var row:p.layout(w,6,false))check(cells(row.text())<=w);}}}}']
 else:s += ['{Item a;a.id="same";bool bad=false;try{m.set_items({a,a});}catch(const std::invalid_argument&){bad=true;}assert(bad);p.handle("open");std::string query;for(int i=0;i<40;i++)query+="한";p.handle("insert",query,4);for(const auto&theme:{"dark","light","blackwhite"})for(const auto&colors:{"8","16","256","truecolor"})for(int w=0;w<20;w++){Canvas c(24,8,Palette(theme,colors));p.draw(c,{2,1,w,6});for(const auto&row:p.layout(w,6))assert(cells(row.text)<=w);}}return 0;}']
 return '\n'.join(s)
def main():
 p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
 with tempfile.TemporaryDirectory(prefix='tuivory-collections-')as d:
  base=Path(d)
  if lang=='java':
   shutil.copy2(artifact,base/'tuivory.jar');src=base/'CollectionCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);run(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'CollectionCases'],base)
  else:
   src=base/('collection.c'if lang=='c'else'collection.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
   run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);run([base/'checked'],base,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
   if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
   run(flags+['-static','-o',base/'isolated'],base);run([base/'isolated'],base)
 print(lang+': exhaustive Unicode folding, shared list/pending picker, atomic ID updates and all-palette narrow rendering passed')
if __name__=='__main__':main()
