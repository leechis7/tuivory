#!/usr/bin/env python3
"""Exercise the responsive Go compatibility Modal through actual terminal I/O."""
import argparse, fcntl, os, pty, re, select, signal, struct, subprocess, termios, time
from pathlib import Path
from smoke_focus import Screen

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('binary',type=Path);p.add_argument('--lang',choices=['ko','en'],default='ko');p.add_argument('--demo',default='controls')
a=p.parse_args();master,slave=pty.openpty()
fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',16,40,0,0))
def terminal():
    os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
env=dict(os.environ,TERM='xterm-256color');env.pop('NO_COLOR',None)
process=subprocess.Popen([str(a.binary.resolve()),'--demo',a.demo,'--modal','--lang',a.lang,'--theme','light','--colors','8'],stdin=slave,stdout=slave,stderr=slave,preexec_fn=terminal,env=env)
os.close(slave);screen=Screen();raw=bytearray();reports=0
def drain(seconds=.25):
    global reports
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if select.select([master],[],[],.02)[0]:
            try:data=os.read(master,65536)
            except OSError:return
            raw.extend(data);screen.feed(data)
            while reports<raw.count(b'\x1b[6n'):
                os.write(master,b'\x1b[1;1R');reports+=1
def plain():
    text=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]|\x1b[()][0-2A-Z]','',raw.decode(errors='replace'))
    return re.sub(r'[\x00-\x20]','',text)
def send(data):
    os.write(master,data);drain();assert process.poll() is None,raw[-1000:]
try:
    drain(.7)
    cancel='Cancel' if a.lang=='en' else '취소'
    assert cancel in plain(), plain()[-500:]
    for h,w in [(6,20),(16,40),(24,80),(16,40)]:
        fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',h,w,0,0));os.killpg(process.pid,signal.SIGWINCH);drain()
    send(b'\x1b[12~\x1b[13~')
    send(b'\x1b[Z\t\r')
    assert ('Requestdeliveredtohost:2/' if a.lang=='en' else '앱에전달한요청:2/') in plain(), plain()[-1000:]
    os.write(master,b'\x11');drain();process.wait(timeout=3)
    assert process.returncode==0 and b'\x1b[?1049l' in raw
    print(f'Modal PTY {a.lang}: narrow resize/recovery, default Cancel, theme/profile, focus/callback and restoration passed')
finally:
    if process.poll() is None:process.kill();process.wait()
    os.close(master)
