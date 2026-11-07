"""Actual public-session consumers: no framework, database or foreign engine."""
import fcntl,os,pty,select,signal,struct,subprocess,termios,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

SOURCES = {
    'python': r'''from tuivory import Terminal
import signal

def stop(*_):raise SystemExit(0)
signal.signal(signal.SIGTERM,stop)
with Terminal(mouse_motion=True)as t:
 t.write('READY\r\n');idle=False
 while True:
  e=t.read(.1)
  if e is None:
   if not idle:t.write('IDLE\r\n');idle=True
   continue
  if e.key in ('ctrl_q','eof'):break
  t.write('EV|'+e.key+'|'+e.text.encode().hex()+'|'+str(e.x)+'|'+str(e.y)+'|'+str(e.button)+'\r\n')
print('CLOSED')
''',
    'javascript': r'''import {Terminal} from '../../../javascript/dist/index.js';
const t=new Terminal({mouseMotion:true}).open();
const stop=()=>{t.close();process.exit(0);};process.on('SIGTERM',stop);
try{t.write('READY\r\n');let idle=false;while(true){const e=await t.read(100);if(e===null){if(!idle){t.write('IDLE\r\n');idle=true;}continue;}if(['ctrl_q','eof'].includes(e.key))break;t.write('EV|'+e.key+'|'+Buffer.from(e.text).toString('hex')+'|'+e.x+'|'+e.y+'|'+e.button+'\r\n');}}finally{t.close();process.removeListener('SIGTERM',stop);}console.log('CLOSED');
''',
    'c': r'''#include "tuivory.h"
#include <assert.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
static volatile sig_atomic_t stopped=0;
static void stop(int n){(void)n;stopped=1;}
int main(void){signal(SIGTERM,stop);setvbuf(stdout,NULL,_IONBF,0);TuiTerminalOptions o={1,1};TuiTerminal*t=tui_terminal_new(0,1,&o);assert(t&&tui_terminal_open(t)==TUI_OK);assert(tui_terminal_write(t,"READY\r\n")==TUI_OK);int idle=0;while(!stopped){TuiInputEvent*e=NULL;assert(tui_terminal_read(t,100,&e)==TUI_OK);if(!e){if(!idle){assert(tui_terminal_write(t,"IDLE\r\n")==TUI_OK);idle=1;}continue;}if(!strcmp(e->key,"ctrl_q")||!strcmp(e->key,"eof")){tui_input_event_free(e);break;}printf("EV|%s|",e->key);for(size_t i=0;i<e->text_length;i++)printf("%02x",(unsigned char)e->text[i]);printf("|%d|%d|%d\r\n",e->x,e->y,e->button);tui_input_event_free(e);}assert(tui_terminal_close(t)==TUI_OK);tui_terminal_free(t);puts("CLOSED");return 0;}
''',
    'cpp': r'''#include "tuivory.hpp"
#include <csignal>
#include <iomanip>
#include <iostream>
static volatile std::sig_atomic_t stopped=0;
static void stop(int){stopped=1;}
int main(){using namespace tuivory;std::signal(SIGTERM,stop);TerminalOptions o;o.mouse_motion=true;Terminal t(o);t.open();t.write("READY\r\n");bool idle=false;while(!stopped){auto e=t.read(100);if(!e){if(!idle){t.write("IDLE\r\n");idle=true;}continue;}if(e->key=="ctrl_q"||e->key=="eof")break;std::ostringstream line;line<<"EV|"<<e->key<<"|";for(unsigned char c:e->text)line<<std::hex<<std::setw(2)<<std::setfill('0')<<(unsigned)c;line<<std::dec<<"|"<<e->x<<"|"<<e->y<<"|"<<e->button<<"\r\n";t.write(line.str());}t.close();std::cout<<"CLOSED\n";}
''',
    'java': r'''import static io.tuivory.Tuivory.*;
import java.util.*;
public class TerminalSession {public static void main(String[] args)throws Exception{
 try(var terminal=new Terminal(true,true).open()){
  terminal.write("READY\r\n");boolean idle=false;
  while(true){terminal.size();var e=terminal.read(100);if(e==null){if(!idle){terminal.write("IDLE\r\n");idle=true;}continue;}if(e.key().equals("ctrl_q")||e.key().equals("eof"))break;
   terminal.write("EV|"+e.key()+"|"+HexFormat.of().formatHex(e.text().getBytes(java.nio.charset.StandardCharsets.UTF_8))+"|"+e.x()+"|"+e.y()+"|"+e.button()+"\r\n");
  }
 }System.out.println("CLOSED");}}
''',
}

def session_source(language):
    source=SOURCES[language]
    if language=='javascript':source=source.replace('../../../javascript/dist/index.js',(ROOT/'javascript/dist/index.js').as_uri())
    return source

def check_session(language,command,cwd,extra_env=None):
    results=[]
    for stop in [False,True]:
     master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',24,80,0,0));original=termios.tcgetattr(slave)
     def terminal():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
     env=dict(os.environ,TERM='xterm-256color',LC_ALL='C.UTF-8')
     if extra_env:env.update(extra_env)
     p=subprocess.Popen(list(map(str,command)),stdin=slave,stdout=slave,stderr=slave,cwd=cwd,preexec_fn=terminal,env=env);output=bytearray()
     def drain():
      if select.select([master],[],[],.02)[0]:
       try:output.extend(os.read(master,65536))
       except OSError:pass
     def wait(text):
      end=time.monotonic()+8
      while text not in output and time.monotonic()<end:
       drain()
       if p.poll()is not None:break
      assert text in output,(language,stop,text,output[-2000:])
     try:
      wait(b'READY');wait(b'IDLE');assert termios.tcgetattr(slave)!=original
      if stop:p.send_signal(signal.SIGTERM)
      else:
       os.write(master,b'\x1b[B');wait(b'EV|down||0|0|0')
       b='한'.encode()
       for part in b:os.write(master,bytes([part]));time.sleep(.02)
       wait(b'EV|text|'+b.hex().encode()+b'|0|0|0')
       os.write(master,b'\x1b[<32;3;4M\x1b[<0;3;4m');wait(b'EV|mouse_move||2|3|32');wait(b'EV|mouse_release||2|3|0')
       os.write(master,'\x1b[200~한\ntext\x1b[201~'.encode());wait(b'EV|paste|'+ '한\ntext'.encode().hex().encode()+b'|0|0|0')
       fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0));wait(b'EV|resize||40|18|0')
       os.write(master,b'\x11')
      end=time.monotonic()+8
      while p.poll()is None and time.monotonic()<end:drain()
      p.wait(timeout=.1)
      for _ in range(5):drain()
      assert p.returncode==(143 if language=='java'and stop else 0),(language,p.returncode,output[-1000:])
      assert termios.tcgetattr(slave)==original,(language,stop,'terminal not restored',termios.tcgetattr(slave),original)
      for mode in [b'1049',b'1002',b'1006',b'2004']:assert b'\x1b[?'+mode+b'h'in output and b'\x1b[?'+mode+b'l'in output,(language,stop,mode,output[-1000:])
      print('PASS',language,'SIGTERM'if stop else'input/resize/close',flush=True);results.append({'language':language,'signal':stop,'passed':True})
     finally:
      if p.poll()is None:p.kill();p.wait()
      os.close(master);os.close(slave)
    return results

def check_example(language, command):
    """Existing native catalogs must resize/stop even during a partial UTF-8 key."""
    from ansi_cells import complete_frame,read_cells
    results=[]
    for partial in (False,True):
        master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',24,80,0,0));original=termios.tcgetattr(slave)
        def terminal():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
        process=subprocess.Popen([*map(str,command),'--demo','text','--lang','en'],stdin=slave,stdout=slave,stderr=slave,cwd=ROOT,preexec_fn=terminal,env=dict(os.environ,TERM='xterm-256color',LC_ALL='C.UTF-8',PYTHONPATH=str(ROOT/'python/src')));output=bytearray()
        def drain():
            if select.select([master],[],[],.02)[0]:
                try:output.extend(os.read(master,65536))
                except OSError:pass
        def wait_frame(width):
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                drain();frame=complete_frame(output)
                if frame is not None and read_cells(frame.decode()).get((width-1,0),('',))[0]=='╗':return
                if process.poll()is not None:break
            raise AssertionError((language,partial,'example resize/frame',output[-1500:]))
        try:
            wait_frame(80);fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0));wait_frame(40)
            if partial:os.write(master,b'\xed');time.sleep(.05)
            process.send_signal(signal.SIGTERM);deadline=time.monotonic()+5
            while process.poll()is None and time.monotonic()<deadline:drain()
            process.wait(timeout=.1)
            for _ in range(3):drain()
            assert process.returncode==0,(language,partial,process.returncode,output[-1000:])
            assert termios.tcgetattr(slave)==original,(language,partial,'catalog terminal not restored')
            assert b'\x1b[?1049l'in output and b'\x1b[?25h'in output
            results.append({'language':language,'example':'text','partial_utf8':partial,'resize_without_key':True,'signal_restored':True,'passed':True})
            print('PASS',language,'catalog resize/idle-SIGTERM'if not partial else'catalog resize/partial-UTF8-SIGTERM',flush=True)
        finally:
            if process.poll()is None:process.kill();process.wait()
            os.close(master);os.close(slave)
    return results
