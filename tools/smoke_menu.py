#!/usr/bin/env python3
"""Exercise public menus through a PTY; hosts own global keys and original focus."""
import argparse,fcntl,os,pty,select,signal,struct,subprocess,termios,time
from pathlib import Path
from smoke_focus import Screen
p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary',type=Path);p.add_argument('--lang',choices=['ko','en'],default='en');p.add_argument('--ascii',action='store_true');args=p.parse_args()
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',32,120,0,0))
def terminal():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
process=subprocess.Popen([str(args.binary.resolve()),'--lang',args.lang]+(['--ascii']if args.ascii else []),stdin=slave,stdout=slave,stderr=slave,preexec_fn=terminal,env=dict(os.environ,TERM='xterm-256color'));os.close(slave);screen=Screen();captured=bytearray();reports=0
def drain(seconds=.25):
 global reports
 until=time.monotonic()+seconds
 while time.monotonic()<until:
  if select.select([master],[],[],.02)[0]:
   try:data=os.read(master,65536)
   except OSError:return
   captured.extend(data);screen.feed(data)
   while reports<captured.count(b'\x1b[6n'):os.write(master,b'\x1b[1;1R');reports+=1
def send(data):os.write(master,data);drain();assert process.poll() is None, captured[-500:]
def visible():return ''.join(''.join(r) for r in screen.rows).replace(' ','')
def has(s):assert s.replace(' ','') in visible(),visible()
try:
 drain(.8)
 send(b'\x1b[21~');has('open:file/origin=editor')
 send(b'Z');assert 'Z' not in visible(),visible()
 send(b'\x1b[200~nPASTE\x1b[201~');has('open:file/origin=editor');assert 'PASTE' not in visible(),visible()  # Host F10.
 send(b'\x1b[B');has('focus:recent/origin=editor') # Disabled save/separator skipped.
 send(b'\r');has('open:recent/origin=editor')
 send(b'\x1b[B');send(b'\x1b[C');has('open:more/origin=editor')
 for key in (b'\x1b[12~',b'\x1b[13~',b'\x1b[14~'):send(key)
 for h,w in ((16,36),(32,120)):
  fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',h,w,0,0));os.killpg(process.pid,signal.SIGWINCH);drain()
 send(b'b');has('activate:beta/origin=editor')
 send(b'Z');has('Z') # Returned to the editor, not a menu command.
 send(b'\t');send(b'\x1b[21~');has('origin=preview')
 send(b'\x1b');has('close:/origin=preview')
 send(b'\x1bf');has('open:file/origin=preview') # Host Alt+F.
 send(b'\x1b[C');has('open:recent/origin=preview')
 send(b'\x1b');has('back:file/origin=preview')
 send(b'\x1b');send(b'\x1b[21;2~');has('open:/origin=preview')
 send(b'f');has('open:file/origin=preview');send(b'\x1b');has('back:/origin=preview');send(b'\x1b')
 send(b'\x1b[21~');send(b'\x1b[15~');send(b's');has('activate:save/origin=preview')
 # Click menubar then outside: close without forwarding the click to the background.
 send(b'\x1b[<0;4;2M\x1b[<0;4;2m');has('open:file/origin=preview')
 send(b'\x1b[<0;110;20M\x1b[<0;110;20m');has('close:/origin=preview')
 send(b'\x1b[<0;10;5M\x1b[<0;10;5m');send(b'\x1b[21~');has('open:file/origin=editor');send(b'\x1b')
 os.write(master,b'\x11');drain();process.wait(timeout=3);assert process.returncode==0 and b'\x1b[?1049l' in captured
 if args.lang=='en':assert not any('\uac00'<=c<='\ud7a3' for c in captured.decode(errors='replace'))
 print(f'Menu PTY {args.lang}: nested/back, original focus, keys/mouse, eligibility, theme/profile/ASCII, resize and restore passed')
finally:
 if process.poll() is None:process.kill();process.wait()
 os.close(master)
