#!/usr/bin/env python3
"""Exercise public catalog widgets through real PTY input and terminal restore."""
import argparse,fcntl,os,pty,select,signal,struct,subprocess,termios,time
from pathlib import Path
from smoke_focus import Screen
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('binary',type=Path);parser.add_argument('--mode',default='forms');parser.add_argument('--lang',choices=['ko','en'],default='en');args=parser.parse_args()
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',36,120,0,0))
def terminal():
 os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
p=subprocess.Popen([str(args.binary.resolve()),'--mode',args.mode,'--lang',args.lang],stdin=slave,stdout=slave,stderr=slave,preexec_fn=terminal,env=dict(os.environ,TERM='xterm-256color'));os.close(slave);screen=Screen();captured=bytearray();reports=0
def drain(seconds=.25):
 global reports
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if select.select([master],[],[],.02)[0]:
   try:data=os.read(master,65536)
   except OSError:return
   captured.extend(data);screen.feed(data)
   while reports<captured.count(b'\x1b[6n'):os.write(master,b'\x1b[1;1R');reports+=1
def send(data):os.write(master,data);drain()
def visible():return '\n'.join(''.join(row) for row in screen.rows)
try:
 drain(.8)
 if args.mode=='forms':
  send(b'\r');assert 'invalid:' in visible(),visible()
  send(b'Agent');assert 'Agent|' in visible(),visible()
  send(b'\t\t');send(b'bad');assert 'Tuivory|' in visible() and 'Tuivorybad' not in visible(),visible()
  send(b'\t ');send(b'\t');send(b'\x1b[C');send(b'\t');send(b'\r');send(b'\x1b[B');send(b'\r');send(b'\t\r');assert 'submit:' in visible(),visible()
  send(b'\x1b');assert 'cancel:' in visible(),visible()
 if args.mode=='collections':
  send(b'Rust');assert 'Rust|' in visible() and 'Go [' not in visible(),visible()
  send(b'\r');assert 'change: rust' in visible(),visible()
  send(b'\r');send(b'Go');send(b'\x1b');assert 'v Rust' in visible(),visible()
  send(b'\r');send(b'NoSuchItem');assert ('No results' in visible() or '결과없음' in visible().replace(' ','')),visible()
 if args.mode=='grid':
  send(b'\x1b[B');send(b'\r');assert 'edit: row-2' in visible(),visible()
  send(b' ');send(b'\x03');assert 'copy: row-2' in visible(),visible()
  send(b'\x1b[20~');assert 'sort:' in visible(),visible()
  send(b'\x1b[6~');send(b'\x1b[F');assert 'row-99999' in visible(),visible()
  send(b'\x1b[<0;7;4M\x1b[<0;7;4m');assert 'sort:' in visible(),visible()
 for height,width in ((16,40),(36,120)):
  fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',height,width,0,0));os.killpg(p.pid,signal.SIGWINCH);drain(.25)
 send(b'\x11');p.wait(timeout=3);assert p.returncode==0 and b'\x1b[?1049l' in captured
 korean=any('\uac00'<=c<='\ud7a3' for c in captured.decode(errors='replace'));assert korean==(args.lang=='ko')
 print(f'{args.mode} PTY {args.lang}: actions, resize and terminal restoration passed')
finally:
 if p.poll() is None:p.kill();p.wait()
 os.close(master)
