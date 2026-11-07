#!/usr/bin/env python3
"""Verify independent optional terminal codecs and actual session restoration."""
import argparse,json,os,shutil,subprocess,tempfile,sys,platform
from datetime import datetime,timezone
from terminal_sessions import session_source,check_session,check_example
from pathlib import Path
from check_languages import ROOT,quote,run
F=json.loads((ROOT/'design/terminal-input-cases.json').read_text())

def cpp_source():
    lines=['#include "tuivory.hpp"','#include <cassert>','int main(){using namespace tuivory;']
    for case in F['cases']:
        lines.append('{InputDecoder d;std::vector<InputEvent> events;')
        for chunk in case['chunks']:
            data=bytes.fromhex(chunk)
            lines.append('d.feed(std::string({'+','.join('char('+str(b)+')'for b in data)+'}));while(auto e=d.next())events.push_back(*e);')
        if case.get('flush_escape'):lines.append('while(auto e=d.next(true))events.push_back(*e);')
        lines.append('assert(events.size()=='+str(len(case['events']))+');')
        for i,e in enumerate(case['events']):
            lines.append('assert(events['+str(i)+'].key=='+quote(e['key'])+'&&events['+str(i)+'].text=='+quote(e['text'])+'&&events['+str(i)+'].x=='+str(e['x'])+'&&events['+str(i)+'].y=='+str(e['y'])+'&&events['+str(i)+'].button=='+str(e['button'])+');')
        lines.append('}')
    lines.append('return 0;}');return '\n'.join(lines)

def java_source():
    out=['import static io.tuivory.Tuivory.*;','import java.util.*;','public class TerminalCases {public static void main(String[] args){']
    for case in F['cases']:
        out.append('{var d=new InputDecoder();var events=new ArrayList<InputEvent>();')
        for chunk in case['chunks']:
            out.append('d.feed(HexFormat.of().parseHex('+quote(chunk)+'));for(InputEvent e;(e=d.next())!=null;)events.add(e);')
        if case.get('flush_escape'):out.append('for(InputEvent e;(e=d.next(true))!=null;)events.add(e);')
        out.append('assert events.size()=='+str(len(case['events']))+':'+quote(case['name'])+';')
        for i,e in enumerate(case['events']):
            out.append('assert events.get('+str(i)+').equals(new InputEvent('+','.join([quote(e['key']),quote(e['text']),str(e['x']),str(e['y']),str(e['button'])])+')):'+quote(case['name'])+';')
        out.append('}')
    out.append('}}');return '\n'.join(out)

def c_source():
    out=['#include "tuivory.h"','#include <assert.h>','#include <string.h>','int main(void){']
    for case in F['cases']:
        out.append('{TuiInputDecoder*d=tui_input_decoder_new();assert(d);TuiInputEvent*events[100]={0};size_t count=0;TuiInputEvent*e=NULL;')
        for i,chunk in enumerate(case['chunks']):
            data=bytes.fromhex(chunk)
            out.append('{const unsigned char bytes[]={'+(','.join(str(b)for b in data)if data else'0')+'};assert(tui_input_feed(d,bytes,'+str(len(data))+')==TUI_OK);for(;;){assert(tui_input_next(d,0,&e)==TUI_OK);if(!e)break;assert(count<100);events[count++]=e;}}')
        if case.get('flush_escape'):out.append('for(;;){assert(tui_input_next(d,1,&e)==TUI_OK);if(!e)break;assert(count<100);events[count++]=e;}')
        out.append('assert(count=='+str(len(case['events']))+');')
        for i,e in enumerate(case['events']):
            out.append('assert(!strcmp(events['+str(i)+']->key,'+quote(e['key'])+')&&!strcmp(events['+str(i)+']->text,'+quote(e['text'])+')&&events['+str(i)+']->text_length=='+str(len(e['text'].encode()))+'&&events['+str(i)+']->x=='+str(e['x'])+'&&events['+str(i)+']->y=='+str(e['y'])+'&&events['+str(i)+']->button=='+str(e['button'])+');')
        out.append('for(size_t i=0;i<count;i++){tui_input_event_free(events[i]);}tui_input_decoder_free(d);}')
    out.append('return 0;}');return '\n'.join(out)

def source(language):
    return {'c':c_source,'cpp':cpp_source,'java':java_source}[language]()

def main():
    p=argparse.ArgumentParser();p.add_argument('--language',choices=['python','javascript','c','cpp','java'],required=True);p.add_argument('--python',default=sys.executable);p.add_argument('--use-built',action='store_true',help='reuse artifacts built in the same checkout');args=p.parse_args();lang=args.language;args.python=os.path.abspath(shutil.which(args.python)or args.python)
    with tempfile.TemporaryDirectory(prefix='tuivory-terminal-')as directory:
        base=Path(directory)
        if lang in ('python','javascript'):
            env=dict(os.environ,PYTHONPATH=str(ROOT/'python/src'))
            if lang=='python':
                run([args.python,'-m','unittest','discover','-s',ROOT/'python/tests','-p','test_terminal.py'],ROOT,env)
                program=base/'session.py';program.write_text(session_source(lang));command=[args.python,program]
            else:
                run(['node',ROOT/'javascript/tests/terminal.mjs'],ROOT)
                program=base/'session.mjs';program.write_text(session_source(lang));command=['node',program]
            results=check_session(lang,command,base,env)
            example=[args.python,'-m','tuivory']if lang=='python'else['node',ROOT/'javascript/examples/catalog.mjs']
            results+=check_example(lang,example)
        elif lang=='java':
            from build_language import build
            artifact=(ROOT/'.cache/packages/java'/('tuivory-'+(ROOT/'VERSION').read_text().strip()+'.jar'))if args.use_built else build(lang);shutil.copy2(artifact,base/'tuivory.jar');src=base/'TerminalCases.java';src.write_text(java_source())
            flags=['javac','--release','17','-encoding','UTF-8','-Xlint:all','-Werror','-cp',base/'tuivory.jar']
            run(flags+[src],base);classpath=str(base/'tuivory.jar')+os.pathsep+str(base)
            run(['java','-ea','-cp',classpath,'TerminalCases'],base)
            program=base/'TerminalSession.java';program.write_text(session_source(lang));run(flags+[program],base)
            results=check_session(lang,['java','-cp',classpath,'TerminalSession'],base)
        else:
            shutil.copytree(ROOT/lang/'include',base/'include');src=base/('terminal.c'if lang=='c'else'terminal.cpp');src.write_text(source(lang))
            flags=['cc'if lang=='c'else'c++','-std=c11'if lang=='c'else'-std=c++17','-Wall','-Wextra','-Werror','-I',base/'include']
            run(flags+[src]+([ROOT/'c/src/tuivory.c']if lang=='c'else[])+['-fsanitize=address,undefined','-o',base/'checked'],base)
            run([base/'checked'],base,dict(os.environ,ASAN_OPTIONS=os.environ.get('ASAN_OPTIONS','detect_leaks=0')))
            if lang=='c':
                from build_language import build
                if not args.use_built:build(lang)
                shutil.copy2(ROOT/'.cache/native/c/libtuivory.a',base/'libtuivory.a');link=[base/'libtuivory.a']
            else:link=[]
            run(flags+[src]+link+['-static','-o',base/'consumer'],base);run([base/'consumer'],base)
            program=base/('session.c'if lang=='c'else'session.cpp');program.write_text(session_source(lang))
            run(flags+[program]+link+['-static','-o',base/'session'],base)
            results=check_session(lang,[base/'session'],base)
            if lang=='cpp'and not args.use_built:
                from build_language import build
                example=build(lang)
            else:
                arch={'aarch64':'arm64','x86_64':'x86_64'}[platform.machine()];example=ROOT/'bin'/lang/('tuivory-linux-'+arch)
            results+=check_example(lang,[example])
    result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'language':lang,'shared_input_cases':len(F['cases']),'sessions':results,'passed':True}
    output=ROOT/'.cache/validation/languages'/('terminal-'+lang+'-results.json');output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
    print(lang+':'+str(len(F['cases']))+' shared incremental UTF-8/key/mouse/paste cases and actual POSIX input/resize/close/SIGTERM restoration passed')
if __name__=='__main__':main()
