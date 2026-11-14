#!/usr/bin/env python3
"""Exercise opt-in tab/tree drag and drop through actual terminal mouse input."""
import argparse,fcntl,os,pty,select,signal,struct,subprocess,termios,time
from pathlib import Path
from smoke_focus import Screen
p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary',type=Path);p.add_argument('--demo',default='workspace');p.add_argument('--lang',choices=['ko','en'],default='en');p.add_argument('--ascii',action='store_true');a=p.parse_args()
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',32,120,0,0))
def terminal():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
env=dict(os.environ,TERM='xterm-256color');env.pop('NO_COLOR',None)
process=subprocess.Popen([str(a.binary.resolve()),'--demo',a.demo,'--lang',a.lang,'--drag']+(['--ascii'] if a.ascii else []),stdin=slave,stdout=slave,stderr=slave,preexec_fn=terminal,env=env);os.close(slave)
screen=Screen();raw=bytearray();reports=0
def drain(seconds=.2):
    global reports
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if select.select([master],[],[],.02)[0]:
            try:data=os.read(master,65536)
            except OSError:return
            raw.extend(data);screen.feed(data)
            while reports<raw.count(b'\x1b[6n'):os.write(master,b'\x1b[1;1R');reports+=1
def send(data):os.write(master,data);drain();assert process.poll() is None,raw[-1000:]
def mouse(code,x,y,up=False):send(f'\x1b[<{code};{x+1};{y+1}{"m" if up else "M"}'.encode())
def visible():return ''.join(''.join(row) for row in screen.rows).replace(' ','')
def check(text):assert text.replace(' ','') in visible(),visible()
try:
    drain(.7)
    drop_x=46 if a.lang=='en' else 42
    mouse(0,3,2);mouse(32,drop_x,2);mouse(0,drop_x,2,True)
    check('drop tabs: overview after logs')
    # Captured release outside the strip rejects without activating another tab.
    mouse(0,36,2);mouse(32,110,20);mouse(0,110,20,True)
    check('drop tabs: overview after logs')
    send(b'\x1b[1;4D')
    check('drop tabs: overview before logs')
    # Reparent a leaf, then use the same library request through keyboard input.
    mouse(0,12,10);mouse(32,12,7);mouse(0,12,7,True)
    check('drop tree: notes inside src')
    mouse(0,12,8);mouse(0,12,8,True)
    send(b'\x1b[1;4B');check('drop tree: go after rust')
    # The src -> descendant cycle must not produce a move request.
    mouse(0,12,7);mouse(32,18,8);mouse(0,18,8,True)
    check('drop tree: go after rust')
    mouse(0,12,9);mouse(32,110,20);send(b'\x1b');mouse(0,110,20,True)
    check('drop tree: go after rust')
    # Theme/resize invalidation must not synthesize a later click or drop.
    mouse(0,12,9);mouse(32,20,10);send(b'\x1b[12~');mouse(0,20,10,True)
    assert 'droptree:goafternotes' not in visible(),visible()
    mouse(0,12,9);mouse(32,20,10)
    for h,w in [(16,32),(32,120)]:
        fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',h,w,0,0));os.killpg(process.pid,signal.SIGWINCH);drain(.3)
    mouse(0,20,10,True);assert 'droptree:goafternotes' not in visible(),visible()
    send(b'\x1b[13~');os.write(master,b'\x11');drain();process.wait(timeout=3)
    assert process.returncode==0 and b'\x1b[?1049l' in raw
    if a.lang=='en':assert not any('\uac00'<=c<='\ud7a3' for c in raw.decode(errors='replace'))
    print(f'Drag PTY {a.lang} ascii={a.ascii}: tabs/tree reorder/reparent, keyboard, captured outside release, cycle rejection, Esc, theme/resize invalidation and restoration passed')
finally:
    if process.poll() is None:process.kill();process.wait()
    os.close(master)
