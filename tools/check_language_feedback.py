#!/usr/bin/env python3
"""Compile independent external feedback consumers against shared host-clock cases."""
import argparse,json,os,shutil,tempfile
from pathlib import Path
from check_languages import ROOT,quote,run
from build_language import build
F=json.loads((ROOT/'design/feedback-cases.json').read_text())

def statements(code):
 # Separate generated statements without changing quoted fixture text.
 out=[];quoted='';escaped=False
 for char in code:
  out.append(char)
  if quoted:
   if escaped:escaped=False
   elif char=='\\':escaped=True
   elif char==quoted:quoted=''
  elif char in ('"', "'"):quoted=char
  elif char in ';{}':out.append('\n')
 return ''.join(out)

def source(lang):
 c=lang=='c';java=lang=='java';serial=0
 out=['import static io.tuivory.Tuivory.*;import java.util.*;public class FeedbackCases{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){']if java else['#include "tuivory.h"'if c else'#include "tuivory.hpp"','#include <assert.h>','#include <string.h>','int main(void){'if c else'int main(){using namespace tuivory;']
 def check(e):out.append('check('+e+');'if java else'assert(('+e+'));')
 def eq(e,v):check(e+'.equals('+quote(v)+')'if java else'!strcmp('+e+','+quote(v)+')'if c else e+'=='+quote(v))
 def string(e,v):eq(e,v)
 def item(n):
  nonlocal serial
  serial+=1;name='n'+str(serial);actions=n.get('actions',[])
  if c:
   if actions:
    out.append('TuiNoticeAction a'+str(serial)+'[]={'+','.join('{'+quote(a['id'])+','+quote(a.get('label',''))+','+str(int(a.get('disabled',False)))+'}'for a in actions)+'};')
   out.append('TuiNotice '+name+'={0};')
  else:out.append('var '+name+'=new Notice('+quote(n['id'])+');'if java else'Notice '+name+';')
  for k in ['id','text','detail','severity']:
   out.append(name+'.'+k+'='+quote(n.get(k,'info'if k=='severity'else''))+';')
  for k in ['priority','expires_at','persistent']:
   value=n.get(k,False if k=='persistent'else 0);field='expiresAt'if java and k=='expires_at'else k
   out.append(name+'.'+field+'='+((str(int(value))if c else str(value).lower())if k=='persistent'else str(value)+('L'if java and k=='expires_at'else''))+';')
  if c and actions:out.append(name+'.actions=a'+str(serial)+';'+name+'.action_count='+str(len(actions))+';')
  elif not c:
   for i,a in enumerate(actions):
    an='a'+str(serial)+'_'+str(i)
    out.append('var '+an+'=new NoticeAction('+quote(a['id'])+','+quote(a.get('label',''))+');'+an+'.disabled='+str(a.get('disabled',False)).lower()+';'+name+'.actions.add('+an+');'if java else name+'.actions.push_back({'+quote(a['id'])+','+quote(a.get('label',''))+','+str(a.get('disabled',False)).lower()+'});')
  return name
 def queue(cap):out.append('{TuiNoticeQueue*q=tui_notice_queue_new('+str(cap)+');assert(q);'if c else'{var q=new NoticeQueue('+str(cap)+');'if java else'{NoticeQueue q('+str(cap)+');')
 def close():out.append('tui_notice_queue_free(q);}'if c else'}')
 def push(n,accepted=True):
  name=item(n)
  if c:check('tui_notice_queue_push(q,&'+name+')=='+('TUI_OK'if accepted else'TUI_INVALID'))
  elif accepted:out.append('q.push('+name+');')
  else:out.append('boolean failed=false;try{q.push('+name+');}catch(IllegalArgumentException e){failed=true;}check(failed);'if java else'bool failed=false;try{q.push('+name+');}catch(const std::invalid_argument&){failed=true;}assert(failed);')
 def visible(now,ids):
  out.append('{const TuiNotice*values;size_t count;assert(tui_notice_queue_visible(q,'+str(now)+',&values,&count)==TUI_OK);'if c else'{var values=q.visible('+str(now)+');'if java else'{auto values=q.visible('+str(now)+');')
  check(('count'if c else'values.size()')+'=='+str(len(ids)))
  for i,id in enumerate(ids):eq('values['+str(i)+'].id'if not java else'values.get('+str(i)+').id',id)
  out.append('}')
 queue(3)
 for n in F['notice_items']:push(n)
 for s in F['notice_steps']:
  op=s['operation']
  if op=='visible':visible(s['now'],s['ids'])
  elif op=='dismiss':check(('tui_notice_queue_dismiss(q,'if c else'q.dismiss(')+quote(s['id'])+')=='+(str(int(s['result']))if c else str(s['result']).lower()))
  elif op=='expire':
   out.append('{TuiNoticeEvents*batch=NULL;assert(tui_notice_queue_expire(q,'+str(s['now'])+',&batch)==TUI_OK);'if c else'{var batch=q.expire('+str(s['now'])+');'if java else'{auto batch=q.expire('+str(s['now'])+');')
   check(('tui_notice_events_count(batch)'if c else'batch.size()')+'=='+str(len(s['ids'])))
   for i,id in enumerate(s['ids']):eq('tui_notice_events_at(batch,'+str(i)+').id'if c else'batch.get('+str(i)+').id()'if java else'batch['+str(i)+'].id',id)
   out.append('tui_notice_events_free(batch);}'if c else'}')
  else:
   out.append('{TuiNoticeEvent e=tui_notice_queue_handle(q,'if c else'{var e=q.handle('if java else'{auto e=q.handle(')
   out[-1]+=quote(s['action'])+','+str(s['now'])+','+str(s['height'])+');'
   if c:check('e.result==TUI_OK')
   for k,v in s['event'].items():eq('e.'+k+('()'if java else''),v)
   out.append('}')
 close()
 for s in F['evictions']:
  queue(s['capacity'])
  for n in s['initial']:push(n)
  push(s['incoming'],s['accepted']);visible(0,s['ids']);eq('tui_notice_queue_focused(q)'if c else'q.focused',s['ids'][0]);close()
 for s in F['progress']:
  out.append('{TuiProgress p={0};'if c else'{var p=new Progress();'if java else'{Progress p;')
  for k,v in s.items():
   if k in ['cancel','role','contains']:continue
   value=quote(v)if isinstance(v,str)else str(int(v))if c and isinstance(v,bool)else str(v).lower()
   out.append('p.'+k+'='+value+';')
  out.append('TuiFeedbackView*v=NULL;assert(tui_progress_layout(&p,40,0,&v)==TUI_OK);const TuiFeedbackRow*label=tui_feedback_row(v,0),*value=tui_feedback_row(v,1);'if c else'var rows=p.layout(40,0);var label=rows.get(0);var value=rows.get(1);'if java else'auto rows=p.layout(40);auto label=rows[0],value=rows[1];')
  eq('label->role'if c else'label.role()'if java else'label.role',s['role'])
  check('strstr(value->text,'+quote(s['contains'])+')!=NULL'if c else'value.text().contains('+quote(s['contains'])+')'if java else'value.text.find('+quote(s['contains'])+')!=std::string::npos')
  eq('tui_progress_request_cancel(&p).kind'if c else'p.requestCancel().kind()'if java else'p.request_cancel().kind','cancel'if s['cancel']else'')
  out.append('tui_feedback_free(v);}'if c else'}')
 queue(3)
 for n in F['notice_items']:push(n)
 if c:out.append('''for(int w=0;w<80;w++)for(int h=0;h<6;h++){const TuiFeedbackRow*rows;size_t count;assert(tui_notice_queue_layout(q,w,h,0,&rows,&count)==TUI_OK);assert(count<=(size_t)h);for(size_t i=0;i<count;i++){assert(tui_cells(rows[i].text)<=w);for(size_t j=0;j<rows[i].span_count;j++){const TuiFeedbackSpan*s=&rows[i].spans[j];assert(s->start+s->width<=w&&tui_cells(s->text)==s->width);}}}assert(tui_notice_queue_focus(q,"info",0));const TuiFeedbackRow*rows;size_t count;assert(tui_notice_queue_layout(q,80,5,0,&rows,&count)==TUI_OK);assert(rows[0].span_count==2);assert(!strcmp(tui_notice_queue_click(q,rows[0].spans[0].start,0,0).kind,""));assert(!strcmp(tui_notice_queue_focused(q),"info"));assert(!strcmp(tui_notice_queue_click(q,rows[0].spans[1].start,0,0).action,"retry"));assert(tui_notice_queue_items(q,&count)&&count==3);''')
 elif java:out.append('''for(int w=0;w<80;w++)for(int h=0;h<6;h++){var rows=q.layout(w,h,0);check(rows.size()<=h);for(var row:rows){check(cells(row.text())<=w);for(var s:row.spans())check(s.start()+s.width()<=w&&cells(s.text())==s.width());}}q.focused="info";var rows=q.layout(80,5,0);check(rows.get(0).spans().size()==2);check(q.click(rows.get(0).spans().get(0).start(),0,0).kind().isEmpty());check(q.focused.equals("info"));check(q.click(rows.get(0).spans().get(1).start(),0,0).action().equals("retry"));check(q.items().size()==3);''')
 else:out.append('''for(int w=0;w<80;w++)for(int h=0;h<6;h++){auto rows=q.layout(w,h);assert(rows.size()<=static_cast<std::size_t>(h));for(const auto&row:rows){assert(cells(row.text)<=w);for(const auto&s:row.spans)assert(s.start+s.width<=w&&cells(s.text)==s.width);}}q.focused="info";auto rows=q.layout(80,5);assert(rows[0].spans.size()==2);assert(q.click(rows[0].spans[0].start,0).kind.empty());assert(q.focused=="info");assert(q.click(rows[0].spans[1].start,0).action=="retry");assert(q.items().size()==3);''')
 # Every palette, narrow allocations, progress/data state roles and no synthetic cursor.
 for kind,role in F['data_states'].items():
  if c:out.append('{TuiDataState s={'+quote(kind)+',"State","Detail"};TuiFeedbackView*v=NULL;assert(tui_data_state_layout(&s,10,&v)==TUI_OK);assert(!strcmp(tui_feedback_row(v,0)->role,'+quote(role)+'));tui_feedback_free(v);}')
  else:eq('new DataState('+quote(kind)+',"State","Detail").layout(10).get(0).role()'if java else'DataState{'+quote(kind)+',"State","Detail"}.layout(10)[0].role',role)
 if c:out.append('''TuiProgress p={.id="p",.label="Job 한글",.cancel_label="Cancel",.cancellable=1};const char*themes[]={"dark","light","blackwhite"},*colors[]={"8","16","256","truecolor"};for(int t=0;t<3;t++)for(int k=0;k<4;k++)for(int w=0;w<20;w++){TuiCanvas*c=tui_canvas_new(w,12,themes[t],colors[k]);assert(c);assert(tui_notice_queue_draw(q,c,(TuiRect){0,0,w,4},0)==TUI_OK);assert(tui_progress_draw(&p,c,(TuiRect){0,4,w,4},0)==TUI_OK);TuiDataState s={"error","Error","Detail"};assert(tui_data_state_draw(&s,c,(TuiRect){0,8,w,4})==TUI_OK);char*ansi=tui_canvas_ansi(c);assert(ansi&&!strstr(ansi,"\\033[?25h"));tui_string_free(ansi);tui_canvas_free(c);}p.current=9007199254740992ULL;TuiFeedbackView*v=NULL;assert(tui_progress_layout(&p,10,0,&v)==TUI_INVALID);''')
 elif java:out.append('''var p=new Progress("p");p.label="Job 한글";p.cancelLabel="Cancel";p.cancellable=true;var frames=new HashSet<String>();for(int i=0;i<4;i++)frames.add(p.layout(40,i).get(1).text());check(frames.size()==4);for(String theme:List.of("dark","light","blackwhite"))for(String colors:List.of("8","16","256","truecolor"))for(int w=0;w<20;w++){var c=new Canvas(w,12,new Palette(theme,colors));q.draw(c,new Rect(0,0,w,4),0);p.draw(c,new Rect(0,4,w,4),0);new DataState("error","Error","Detail").draw(c,new Rect(0,8,w,4));check(c.cursorX<0);}''')
 else:out.append('''Progress p;p.id="p";p.label="Job 한글";p.cancel_label="Cancel";p.cancellable=true;std::map<std::string,bool>frames;for(int i=0;i<4;i++)frames[p.layout(40,i)[1].text]=true;assert(frames.size()==4);for(const auto&theme:{"dark","light","blackwhite"})for(const auto&colors:{"8","16","256","truecolor"})for(int w=0;w<20;w++){Canvas c(w,12,Palette(theme,colors));q.draw(c,{0,0,w,4});p.draw(c,{0,4,w,4});DataState{"error","Error","Detail"}.draw(c,{0,8,w,4});assert(!c.cursor);}''')
 close()
 if c:out.append('''{TuiNoticeQueue*q=tui_notice_queue_new(1);char text[]="Owned";TuiNoticeAction actions[]={{"go","Action",1}};TuiNotice n={.id="own",.text=text,.actions=actions,.action_count=1};assert(tui_notice_queue_push(q,&n)==TUI_OK);text[0]='X';actions[0].disabled=0;const TuiNotice*items;size_t count;assert(tui_notice_queue_visible(q,100,&items,&count)==TUI_OK&&count==1);assert(!strcmp(items[0].text,"Owned")&&items[0].actions[0].disabled);TuiNoticeAction invalid[]={{"same","A",0},{"same","B",0}};n.actions=invalid;n.action_count=2;assert(tui_notice_queue_push(q,&n)==TUI_INVALID);assert(tui_notice_queue_visible(q,0,&items,&count)==TUI_OK&&!strcmp(items[0].text,"Owned"));tui_notice_queue_free(q);q=tui_notice_queue_new(1);TuiNotice transient={.id="transient",.expires_at=1};assert(tui_notice_queue_push(q,&transient)==TUI_OK);const TuiFeedbackRow*rows;assert(tui_notice_queue_layout(q,40,2,0,&rows,&count)==TUI_OK);assert(!*tui_notice_queue_click(q,0,0,2).kind);TuiNoticeEvents*events=NULL;assert(tui_notice_queue_expire(q,2,&events)==TUI_OK);tui_notice_queue_free(q);assert(tui_notice_events_count(events)==1&&!strcmp(tui_notice_events_at(events,0).id,"transient"));tui_notice_events_free(events);}''')
 elif java:out.append('''{var q=new NoticeQueue(1);var n=new Notice("own","Owned");var a=new NoticeAction("go","Action");a.disabled=true;n.actions.add(a);q.push(n);n.text="Changed";a.disabled=false;check(q.visible(100).get(0).text.equals("Owned")&&q.visible(100).get(0).actions.get(0).disabled);var snapshot=q.items();snapshot.get(0).text="Changed";check(q.items().get(0).text.equals("Owned"));n.actions=List.of(new NoticeAction("same"),new NoticeAction("same"));boolean failed=false;try{q.push(n);}catch(IllegalArgumentException e){failed=true;}check(failed&&q.items().get(0).text.equals("Owned"));}''')
 else:out.append('''{NoticeQueue q(1);Notice n;n.id="own";n.text="Owned";n.actions.push_back({"go","Action",true});q.push(n);n.text="Changed";n.actions[0].disabled=false;assert(q.visible(100)[0].text=="Owned"&&q.visible(100)[0].actions[0].disabled);auto snapshot=q.items();snapshot[0].text="Changed";assert(q.items()[0].text=="Owned");n.actions={{"same","A",false},{"same","B",false}};bool failed=false;try{q.push(n);}catch(const std::invalid_argument&){failed=true;}assert(failed&&q.items()[0].text=="Owned");}''')
 queue(3)
 for id in ['z','a','m']:push({'id':id})
 visible(0,['z','a','m']);push({'id':'z','text':'Updated'});visible(0,['z','a','m']);close()
 out.append('}}'if java else'return 0;}');return statements('\n'.join(out))

def main():
 p=argparse.ArgumentParser();p.add_argument('--language',choices=['c','cpp','java'],required=True);lang=p.parse_args().language;artifact=build(lang)
 with tempfile.TemporaryDirectory(prefix='tuivory-feedback-')as directory:
  base=Path(directory)
  if lang=='java':
   shutil.copy2(artifact,base/'tuivory.jar');src=base/'FeedbackCases.java';src.write_text(source(lang));run(['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar',src],base);run(['java','-cp',str(base/'tuivory.jar')+os.pathsep+str(base),'FeedbackCases'],base)
  else:
   src=base/('feedback.c'if lang=='c'else'feedback.cpp');src.write_text(source(lang));shutil.copytree(ROOT/lang/'include',base/'include');flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include',src]
   run(flags+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base);run([base/'checked'],base,env=dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
   if lang=='c':shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');flags+=[base/'libtuivory.a']
   run(flags+['-static','-o',base/'isolated'],base);run([base/'isolated'],base)
 print(lang+': shared feedback lifetimes, retained important notices, host requests, action clipping, progress/data states and palette checks passed')
if __name__=='__main__':main()
