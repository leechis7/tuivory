#!/usr/bin/env python3
"""Check independent Tree demos in PTYs, including actual output and restoration."""
from pathlib import Path
import argparse
import fcntl
import json
import os
import platform
import pty
import re
import select
import struct
import subprocess
import sys
import termios
import time
from smoke_focus import Screen

ROOT=Path(__file__).resolve().parents[1]

def check(language,command,lang,theme,colors,ascii,demo="tree"):
    master,slave=pty.openpty()
    fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',24,80,0,0))
    original=termios.tcgetattr(slave)
    def terminal():
        os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
    env=dict(os.environ,TERM='xterm-256color',LC_ALL='C.UTF-8')
    if language=='python':env['PYTHONPATH']=str(ROOT/'python/src')
    args=[*command,'--demo',demo,'--lang',lang,'--theme',theme,'--colors',colors]+(['--ascii']if ascii else[])
    process=subprocess.Popen(list(map(str,args)),cwd=ROOT,stdin=slave,stdout=slave,stderr=slave,preexec_fn=terminal,env=env)
    screen=Screen();captured=bytearray()
    def drain(seconds):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            if select.select([master],[],[],.01)[0]:
                try:data=os.read(master,65536)
                except OSError:return
                captured.extend(data);screen.feed(data)
    def wait_row(row,selected,timeout=5):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            drain(.02)
            current=''.join(screen.rows[row])
            column=2 if demo=='workspace' else 1
            if (current[column:column+1]=='>')==selected:return
            if process.poll()is not None:break
        raise AssertionError((language,lang,theme,colors,ascii,'row',row,selected,bytes(captured[-1000:])))
    try:
        if demo=='text':
            drain(.25)
            # Move to line start and insert a sentinel; backspace must restore it.
            os.write(master,b'home\n'if language=='java'else b'\x1b[H');drain(.06)
            os.write(master,b'insert Z\n'if language=='java'else b'Z');drain(.08)
            visible='\n'.join(''.join(r)for r in screen.rows[1:17])
            assert 'Z'in visible,(language,'text insert',visible)
            os.write(master,b'backspace\n'if language=='java'else b'\x7f');drain(.08)
            visible='\n'.join(''.join(r)for r in screen.rows[1:17])
            assert 'Z'not in visible,(language,'text deletion',visible)
            assert b'\x1b[?25h'in captured,(language,'real cursor absent')
        else:
            # Row one contains the selected root. The actual VT buffer is inspected.
            root=4 if demo=='workspace' else 1
            wait_row(root,True)
            down=b'down\n'if language=='java'else b's'if language in ['c','cpp']else b'\x1b[B'
            up=b'up\n'if language=='java'else b'w'if language in ['c','cpp']else b'\x1b[A'
            os.write(master,down);wait_row(root+1,True);wait_row(root,False)
            os.write(master,up);wait_row(root,True)
            if language in ['python','javascript']:
                os.write(master,b'\x1bOP\x1bOQ');drain(.05);wait_row(root,True)
            if demo=='workspace':
                os.write(master,b'tab\n'if language=='java'else b'\t');drain(.05)
                os.write(master,b'right\n'if language=='java'else b'd'if language in ['c','cpp']else b'\x1b[C');drain(.05)
                os.write(master,b'activate\n'if language=='java'else b'\r');drain(.1)
                visible='\n'.join(''.join(row)for row in screen.rows)
                assert ('Draft'if lang=='en'else'초안')in visible.replace(' ',''),(language,'tab activation',visible)
        os.write(master,b'quit\n'if language=='java'else b'\x11')
        process.wait(timeout=5);drain(.02)
        assert process.returncode==0,(language,process.returncode,bytes(captured[-1000:]))
        assert termios.tcgetattr(slave)==original,(language,'terminal not restored')
        assert not re.search(rb'\x1b\[[0-9;]* q',captured)
        assert not re.search(rb'\x1b\[\?12[hl]',captured)
        if language!='java':
            assert b'\x1b[?1049h'in captured and b'\x1b[?1049l'in captured
        assert b'\x1b[?25h'in captured
        if lang=='en' and ascii:captured.decode('ascii')
        return dict(language=language,demo=demo,lang=lang,theme=theme,colors=colors,ascii=ascii,passed=True)
    finally:
        if process.poll()is None:process.kill();process.wait()
        os.close(master);os.close(slave)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--python',default=sys.executable)
    p.add_argument('--language',choices=['python','javascript','c','cpp','java'])
    p.add_argument('--matrix',action='store_true')
    p.add_argument('--demo',choices=['tree','workspace','text'],default='tree')
    args=p.parse_args()
    arch={'aarch64':'arm64','x86_64':'x86_64'}[platform.machine()]
    commands={'python':[args.python,'-m','tuivory'],'javascript':['node',ROOT/'javascript/examples/catalog.mjs'],'c':[ROOT/'bin/c'/f'tuivory-linux-{arch}'],'cpp':[ROOT/'bin/cpp'/f'tuivory-linux-{arch}'],'java':['java','-jar',ROOT/'.cache/packages/java'/f'tuivory-{(ROOT/"VERSION").read_text().strip()}.jar']}
    results=[]
    for language,cmd in commands.items():
        if args.language and args.language!=language:continue
        for lang in ['ko','en']:
            for theme in ['dark','light','blackwhite']if args.matrix else['dark']:
                for colors in ['8','16','256','truecolor']if args.matrix else['256']:
                    for ascii in [False,True]if args.matrix else[False]:
                        r=check(language,cmd,lang,theme,colors,ascii,args.demo);results.append(r)
                        print('PASS',language,lang,theme,colors,'ascii='+str(ascii),args.demo,flush=True)
    out=ROOT/'.cache/validation/languages'/('pty-results.json'if args.demo=='tree'else'pty-'+args.demo+'-results.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
