#!/usr/bin/env python3
"""Exercise an external SDK-only host: cleanup, nesting, unwind and init failure."""
import argparse
import fcntl
import os
from pathlib import Path
import pty
import select
import subprocess
import termios
import time

p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary',type=Path);a=p.parse_args()
binary=str(a.binary.resolve())
no_tty=subprocess.run([binary],env=dict(os.environ,TUIVORY_SESSION_TEST='no-tty'),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
assert no_tty.returncode==0 and no_tty.stdout==b'NO_TTY_OK\n',(no_tty.stdout,no_tty.stderr)
for mode in ('normal','panic','foreign-raw'):
    master,slave=pty.openpty();before=termios.tcgetattr(slave)
    def setup():
        os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
    child=subprocess.Popen([binary],stdin=slave,stdout=slave,stderr=slave,preexec_fn=setup,env=dict(os.environ,TERM='xterm-256color',TUIVORY_SESSION_TEST=mode))
    captured=bytearray();deadline=time.monotonic()+10
    try:
        while time.monotonic()<deadline:
            if select.select([master],[],[],.05)[0]:captured.extend(os.read(master,65536))
            if child.poll() is not None:break
        code=child.wait(timeout=1)
        assert (code==0)==(mode!='panic'),(mode,code,captured)
        assert termios.tcgetattr(slave)==before,mode
        if mode!='foreign-raw':
            assert b'\x1b[?1049h' in captured and b'\x1b[?1049l' in captured,(mode,captured)
            assert b'\x1b[?2004h' in captured and b'\x1b[?2004l' in captured,(mode,captured)
        else:assert b'FOREIGN_RAW_OK' in captured and b'\x1b[?1049h' not in captured,captured
        if mode=='normal':assert b'SESSION_OK' in captured,captured
    finally:
        if child.poll() is None:child.kill();child.wait()
        os.close(master);os.close(slave)
print('SDK-only session: finish/re-entry, nested rejection, foreign raw ownership, panic restoration and two init failures passed.')
