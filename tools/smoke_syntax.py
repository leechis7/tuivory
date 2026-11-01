#!/usr/bin/env python3
"""Check optional SQL analyzer/editor hosts through real terminal input."""
import argparse,fcntl,os,pty,select,signal,struct,subprocess,termios,time
from pathlib import Path
from smoke_focus import Screen
p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary',type=Path);p.add_argument('--lang',choices=['ko','en'],default='en');p.add_argument('--ascii',action='store_true');a=p.parse_args()
master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',26,100,0,0))
def terminal():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
process=subprocess.Popen([str(a.binary.resolve()),'--lang',a.lang]+(['--ascii'] if a.ascii else []),stdin=slave,stdout=slave,stderr=slave,preexec_fn=terminal,env=dict(os.environ,TERM='xterm-256color'));os.close(slave)
screen=Screen();captured=bytearray();reports=0
def drain(seconds=.2):
    global reports
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        if select.select([master],[],[],.02)[0]:
            try:data=os.read(master,65536)
            except OSError:return
            captured.extend(data);screen.feed(data)
            while reports<captured.count(b'\x1b[6n'):os.write(master,b'\x1b[1;1R');reports+=1
def visible():return ''.join(''.join(row) for row in screen.rows)
def send(data):os.write(master,data);drain();assert process.poll() is None,captured[-1000:]
try:
    drain(.7);assert 'SELECT' in visible() and 'NVL' in visible(),visible()
    send(b'\x01');send(b'\x1b[200~SELECT NVL(:id, q\'[SYNTAX_EDIT]\') FROM dual;\n-- literal\x1b[201~');assert 'SYNTAX_EDIT' in visible(),visible()
    send(b'\x1b[12~\x1b[13~');assert 'SYNTAX_EDIT' in visible(),visible()
    send(b'\x1a');assert 'SYNTAX_EDIT' not in visible(),visible()
    send(b'\x19');assert 'SYNTAX_EDIT' in visible(),visible()
    send(b'\x01\x03');assert 'copy' in visible(),visible()
    for height,width in ((12,30),(26,100)):
        fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',height,width,0,0));os.killpg(process.pid,signal.SIGWINCH);drain()
    assert 'SYNTAX_EDIT' in visible(),visible()
    send(b'\x1b[<0;8;3M\x1b[<32;15;3M\x1b[<0;100;25m')
    os.write(master,b'\x11');drain();process.wait(timeout=3)
    assert process.returncode==0 and b'\x1b[?1049l' in captured,captured[-1000:]
    if a.lang=='en':assert not any('\uac00'<=c<='\ud7a3' for c in captured.decode(errors='replace'))
    print(f'SQL syntax PTY {a.lang}: literal paste, undo/redo, copy, theme/profile, resize, captured mouse and terminal restore passed')
finally:
    if process.poll() is None:process.kill();process.wait()
    os.close(master)
