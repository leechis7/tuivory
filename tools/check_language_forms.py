#!/usr/bin/env python3
"""Apply shared form scenarios to independent external C/C++/Java consumers."""
from pathlib import Path
import argparse,json,os,shutil,tempfile
from check_languages import ROOT,quote,run
from build_language import build
F=json.loads((ROOT/'design/forms-cases.json').read_text())['scenarios']
camel=lambda s:''.join(v.title()if i else v for i,v in enumerate(s.split('_')))
SFLAGS=['disabled','read_only','busy','selected','edited','invalid']
TEXT=['id','kind','label','value','help','error','choice','action','pending']
BOOL=['required','checked','open']
def flag(v,language):return str(int(bool(v)))if language=='c'else str(bool(v)).lower()
def make(language):
 c=language=='c';java=language=='java'
 if java:s=['import static io.tuivory.Tuivory.*;import java.util.*;public class FormCases{static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){']
 else:s=['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <string.h>','int main(void){'if c else'int main(){using namespace tuivory;']
 def check(expr):return ('check('if java else'assert(')+expr+');'
 def eq(expr,v):return check(expr+'.equals('+quote(v)+')')if java else check('!strcmp('+expr+','+quote(v)+')')if c else check(expr+'=='+quote(v))
 def fexpr(id):return f'tui_form_field(f,{quote(id)})'if c else f'f.fields().stream().filter(v->v.id.equals({quote(id)})).findFirst().orElseThrow()'if java else f'(*std::find_if(f.fields().begin(),f.fields().end(),[](const Field&v){{return v.id=={quote(id)};}}))'
 for case in F:
  s+=['{']
  if c:s+=[f'TuiField fields[{len(case["fields"])}]={{0}};']
  elif java:s+=['var fields=new ArrayList<Field>();']
  else:s+=['std::vector<Field> fields;']
  for i,data in enumerate(case['fields']):
   if c:
    for key in TEXT:s += [f'fields[{i}].{key}={quote(data.get(key,"text"if key=="kind"else""))};']
    for key in BOOL:s += [f'fields[{i}].{key}={flag(data.get(key),language)};']
    for key in SFLAGS:s += [f'fields[{i}].state.{key}={flag(data.get("state",{}).get(key),language)};']
    if data.get('options'):
     s += [f'TuiFormOption options{i}[]={{'+','.join('{'+quote(o['id'])+','+quote(o.get('label',''))+','+flag(o.get('disabled'),language)+'}'for o in data['options'])+'};',f'fields[{i}].options=options{i};fields[{i}].option_count={len(data["options"])};']
   else:
    s += ['{var v=new Field('+quote(data['id'])+');'if java else'{Field v;']
    for key in TEXT:s += [f'v.{key}={quote(data.get(key,"text"if key=="kind"else""))};']
    for key in BOOL:s += [f'v.{key}={flag(data.get(key),language)};']
    for key in SFLAGS:s += [f'v.state.{camel(key)if java else key}={flag(data.get("state",{}).get(key),language)};']
    for o in data.get('options',[]):s += ['v.options.add(new FormOption('+quote(o['id'])+','+quote(o.get('label',''))+','+flag(o.get('disabled'),language)+'));'if java else'v.options.push_back({'+quote(o['id'])+','+quote(o.get('label',''))+','+flag(o.get('disabled'),language)+'});']
    s += ['fields.add(v);}'if java else'fields.push_back(v);}']
  s += [f'TuiForm*f=tui_form_new(fields,{len(case["fields"])});assert(f);TuiFormEvent e;'if c else'var f=new Form(fields);FormEvent e;'if java else'Form f(fields);FormEvent e;']
  for step in case['steps']:
   if 'focus'in step:s += [check(f'tui_form_focus(f,{quote(step["focus"])})'if c else f'f.focus({quote(step["focus"])})')];continue
   if 'feedback'in step:s += [check(f'tui_form_set_feedback(f,{quote(step["feedback"])},"",{quote(step["error"])})==TUI_OK'if c else f'f.setFeedback({quote(step["feedback"])},"",{quote(step["error"])})'if java else f'f.set_feedback({quote(step["feedback"])},"",{quote(step["error"])})')];continue
   if 'state'in step:
    s+=['{TuiState state={0};'if c else'{var state=new State();'if java else'{State state;']
    for key,value in step['value'].items():s += [f'state.{camel(key)if java else key}={flag(value,language)};']
    s += [check(f'tui_form_set_state(f,{quote(step["state"])},state)==TUI_OK'if c else f'f.setState({quote(step["state"])},state)'if java else f'f.set_state({quote(step["state"])},state)'),'}'];continue
   if 'click'in step:call=f'tui_form_click_field(f,{quote(step["click"])},{quote(step.get("option",""))})'if c else f'f.{"clickField"if java else"click_field"}({quote(step["click"])},{quote(step.get("option",""))})'
   else:call=f'tui_form_handle(f,{quote(step["action"])},{quote(step.get("text",""))})'if c else f'f.handle({quote(step["action"])},{quote(step.get("text",""))})'
   s += ['e='+call+';',eq('e.kind()'if java else'e.kind',step['kind']),eq('e.text()'if java else'e.text',step.get('event_text',''))]
   if c:s += [check('e.result==TUI_OK')]
   if 'focused'in step:s += [eq('tui_form_focused(f)'if c else'f.focused',step['focused'])]
   if 'missing'in step:
    s += [check(('e.missing_count'if c else'e.missing().size()'if java else'e.missing.size()')+'=='+str(len(step['missing'])))]
    for i,id in enumerate(step['missing']):s += [eq(f'e.missing().get({i})'if java else f'e.missing[{i}]',id)]
   for key,attr in [('choices','choice'),('pending','pending'),('open','open'),('checked','checked'),('display','value')]:
    for id,v in step.get(key,{}).items():
     expr=fexpr(id)+('->'if c else'.')+attr
     s += [check(expr+'=='+flag(v,language))if isinstance(v,bool)else eq(expr,v)]
   for id,value in step.get('values',{}).items():s += [eq(f'tui_form_value(f,{quote(id)})'if c else f'f.value({quote(id)})',value)]
  if c:s+=['tui_form_free(f);']
  s+=['}']
 # Constructor rejection and bounded all-palette output.
 if c:s += ['{TuiField fields[2]={{.id="same"},{.id="same"}};assert(!tui_form_new(fields,2));fields[1].id="";assert(!tui_form_new(fields,2));TuiField invalid={.id="a",.kind="bad"};assert(!tui_control_new(invalid));}',
 '{const char*themes[]={"dark","light","blackwhite"};const char*colors[]={"8","16","256","truecolor"};TuiField fields[]={{.id="p",.kind="password",.label="Password",.value="秘密😀"},{.id="off",.kind="checkbox",.state={.disabled=1}}};TuiForm*f=tui_form_new(fields,2);assert(f);for(int theme=0;theme<3;theme++)for(int color=0;color<4;color++)for(int w=0;w<20;w++){TuiCanvas*c=tui_canvas_new(24,8,themes[theme],colors[color]);assert(tui_form_draw(f,c,(TuiRect){2,1,w,6},1)==TUI_OK);for(int y=0;y<8;y++){char*line=tui_canvas_line(c,y);assert(!strstr(line,"秘密"));tui_string_free(line);}assert(!strcmp(tui_form_click_field(f,"off","").kind,""));assert(!tui_form_field(f,"off")->checked);tui_canvas_free(c);}tui_form_free(f);}']
 elif java:s += ['{boolean bad=false;try{new Form(List.of(new Field("same"),new Field("same")));}catch(IllegalArgumentException e){bad=true;}check(bad);}',
 '{var p=new Field("p","password");p.value="秘密😀";p.label="Password";var off=new Field("off","checkbox");off.state.disabled=true;var f=new Form(List.of(p,off));for(String theme:List.of("dark","light","blackwhite"))for(String colors:List.of("8","16","256","truecolor"))for(int w=0;w<20;w++){var c=new Canvas(24,8,new Palette(theme,colors));f.draw(c,new Rect(2,1,w,6),true);for(String line:c.lines())check(!line.contains("秘密"));check(f.clickField("off","").kind().isEmpty());}}']
 else:s += ['{bool bad=false;try{Field a;a.id="same";Form f({a,a});}catch(const std::invalid_argument&){bad=true;}assert(bad);}',
 '{Field p;p.id="p";p.kind="password";p.value="秘密😀";p.label="Password";Field off;off.id="off";off.kind="checkbox";off.state.disabled=true;Form f({p,off});for(const auto&theme:{"dark","light","blackwhite"})for(const auto&colors:{"8","16","256","truecolor"})for(int w=0;w<20;w++){Canvas c(24,8,Palette(theme,colors));f.draw(c,{2,1,w,6});for(const auto&line:c.lines())assert(line.find("秘密")==std::string::npos);assert(f.click_field("off").kind.empty());}}']
 if c:s += ['{TuiField a={.id="a",.kind="text",.value="한"};TuiForm*f=tui_control_new(a);TuiCanvas*c=tui_canvas_new(10,6,"light","8");assert(tui_form_draw(f,c,(TuiRect){1,1,8,4},1)==TUI_OK);assert(!strcmp(tui_form_click(f,-1,1,4).kind,""));assert(!strcmp(tui_form_click(f,8,1,4).kind,""));assert(!strcmp(tui_form_click(f,3,1,4).kind,"select"));tui_form_handle(f,"insert","X");assert(!strcmp(tui_form_value(f,"a"),"X한"));tui_canvas_free(c);tui_form_free(f);}',
 '{TuiFormOption options[]={{"a","A",0},{"a","B",0}};TuiField f={.id="s",.kind="select",.options=options,.option_count=2};assert(!tui_control_new(f));options[1].id="";assert(!tui_control_new(f));options[1].id="b";f.choice="missing";assert(!tui_control_new(f));f.choice="a";f.open=1;assert(!tui_control_new(f));}']
 elif java:s += ['{var a=new Field("a");a.value="한";var f=new Control(a);var c=new Canvas(10,6);f.draw(c,new Rect(1,1,8,4),true);check(f.click(-1,1,4).kind().isEmpty());check(f.click(8,1,4).kind().isEmpty());check(f.click(3,1,4).kind().equals("select"));f.handle("insert","X");check(f.value("a").equals("X한"));}',
 '{var a=new Field("s","select");a.options=List.of(new FormOption("a","A"),new FormOption("a","B"));boolean bad=false;try{new Control(a);}catch(IllegalArgumentException e){bad=true;}check(bad);a.options=List.of(new FormOption("","A"));bad=false;try{new Control(a);}catch(IllegalArgumentException e){bad=true;}check(bad);a.options=List.of(new FormOption("a","A"));a.choice="missing";bad=false;try{new Control(a);}catch(IllegalArgumentException e){bad=true;}check(bad);a.choice="a";a.open=true;bad=false;try{new Control(a);}catch(IllegalArgumentException e){bad=true;}check(bad);}']
 else:s += ['{Field a;a.id="a";a.value="한";Control f(a);Canvas c(10,6);f.draw(c,{1,1,8,4});assert(f.click(-1,1,4).kind.empty());assert(f.click(8,1,4).kind.empty());assert(f.click(3,1,4).kind=="select");f.handle("insert","X");assert(f.value("a")=="X한");}',
 '{Field a;a.id="s";a.kind="select";a.options={{"a","A",false},{"a","B",false}};bool bad=false;try{Control f(a);}catch(const std::invalid_argument&){bad=true;}assert(bad);a.options={{"","A",false}};bad=false;try{Control f(a);}catch(const std::invalid_argument&){bad=true;}assert(bad);a.options={{"a","A",false}};a.choice="missing";bad=false;try{Control f(a);}catch(const std::invalid_argument&){bad=true;}assert(bad);a.choice="a";a.open=true;bad=false;try{Control f(a);}catch(const std::invalid_argument&){bad=true;}assert(bad);}']
 s += ['}}'if java else'return 0;}'];return '\n'.join(s)
def main():
 p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
 with tempfile.TemporaryDirectory(prefix='tuivory-form-')as d:
  base=Path(d)
  if lang=='java':
   shutil.copy2(artifact,base/'tuivory.jar');src=base/'FormCases.java';src.write_text(make(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);run(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'FormCases'],base)
  else:
   src=base/('form.c'if lang=='c'else'form.cpp');src.write_text(make(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
   run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);run([base/'checked'],base,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
   if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
   run(flags+['-static','-o',base/'isolated'],base);run([base/'isolated'],base)
 print(lang+': shared form validation, editing, pending choices, secret/state handling and all-palette bounded rendering passed')
if __name__=='__main__':main()
