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
        if demo=='drag':
            from check_drag_example import check_drag_example
            check_drag_example(language,lang,theme,colors,ascii,master,slave,process,captured,screen,drain)
        elif demo=='grid':
            from check_grid_example import check_grid_example
            check_grid_example(language,lang,theme,colors,ascii,master,slave,process,captured,screen,drain)
        elif demo=='syntax':
            from check_syntax_example import check_syntax_example
            check_syntax_example(language,lang,theme,colors,ascii,master,slave,process,captured,screen,drain)
        elif demo=='document':
            from check_document_example import check_document_example
            check_document_example(language,lang,theme,colors,ascii,master,slave,process,captured,screen,drain)
        elif demo in ('shadow','dialog'):
            from check_popup_example import check_popup_example
            check_popup_example(language,demo,lang,ascii,master,slave,process,captured,screen,drain)
        elif demo=='surface':
            from ansi_cells import read_cells,complete_frame
            palettes=json.loads((ROOT/'design/tokens/candidate.json').read_text())['palettes'];palette=palettes[theme+'-'+colors]
            def visible():return '\n'.join(''.join(row)for row in screen.rows[:24])
            def wait_text(value):
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    drain(.02)
                    if value.replace(' ','')in visible().replace(' ',''):return
                    if process.poll()is not None:break
                raise AssertionError((language,demo,value,visible()))
            def send(command,raw):
                frames=captured.count(b'\x1b[0m');os.write(master,(command+'\n').encode()if language=='java'else raw)
                deadline=time.monotonic()+5
                while captured.count(b'\x1b[0m')<=frames and time.monotonic()<deadline:drain(.02)
                assert captured.count(b'\x1b[0m')>frames,(language,'surface frame',visible())
            def styles(role):
                deadline=time.monotonic()+5
                frame=complete_frame(captured)
                while frame is None and time.monotonic()<deadline:
                    drain(.02);frame=complete_frame(captured)
                assert frame is not None,(language,'incomplete surface frame',bytes(captured[-400:]))
                current=read_cells(frame.decode())
                for yy in [1,2,3,4,7,9]:assert current[1,yy][2]==palette[role]['background'],(language,theme,colors,role,yy,current[1,yy])
                assert current[1,4][4],(language,'disabled Dim absent')
                assert current[1,5][2]==palette['selection']['background'],(language,'selection background lost')
                assert current[1,6][2]==palette['edited']['background'],(language,'edited background lost')
            wait_text('Surface: editor'if lang=='en'else'바탕: 편집');styles('editor')
            for role,label in [('field','field'if lang=='en'else'입력'),('button.focus','focused button'if lang=='en'else'포커스 버튼'),('surface','panel'if lang=='en'else'패널'),('editor','editor'if lang=='en'else'편집')]:
                send('s',b's');wait_text(('Surface: 'if lang=='en'else'바탕: ')+label);styles(role)
            send('insert Z',b'Z');assert 'Z'not in ''.join(screen.rows[7]),(language,'read-only value changed')
            if language!='java':
                fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0));send('s',b's');wait_text('Surface: field'if lang=='en'else'바탕: 입력');styles('field')
                deadline=time.monotonic()+5
                while screen.rows[0][39]!=('+'if ascii else'╗')and time.monotonic()<deadline:drain(.02)
                assert screen.rows[0][39]==('+'if ascii else'╗'),(language,'surface narrow frame',visible())
        elif demo=='container':
            def visible():return '\n'.join(''.join(row)for row in screen.rows[:24])
            def wait_text(value):
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    drain(.02)
                    if value.replace(' ','')in visible().replace(' ',''):return
                    if process.poll()is not None:break
                raise AssertionError((language,demo,value,visible()))
            def send(command,raw):
                frames=captured.count(b'\x1b[0m');os.write(master,(command+'\n').encode()if language=='java'else raw)
                deadline=time.monotonic()+5
                while captured.count(b'\x1b[0m')<=frames and time.monotonic()<deadline:drain(.02)
                assert captured.count(b'\x1b[0m')>frames,(language,'container frame',visible())
            def cursor_visible():
                frame=captured.rsplit(b'\x1b[?25l',1)[-1]
                if language=='java':frame=frame.split(b'\x1b[19;1H',1)[0]
                return b'\x1b[?25h'in frame
            wait_text('Navigator'if lang=='en'else'탐색')
            deadline=time.monotonic()+5
            while not captured.count(b'\x1b[0m')and time.monotonic()<deadline:drain(.02)
            assert cursor_visible(),(language,'editor cursor missing')
            send('m',b'm');wait_text('Popup open'if lang=='en'else'팝업 열림');wait_text('Background input blocked'if lang=='en'else'배경 입력 차단')
            assert not cursor_visible(),(language,'modal leaked background cursor')
            send('insert Z',b'Z');assert not cursor_visible(),(language,'modal leaked editor input/cursor')
            send('m',b'm');wait_text('Popup closed'if lang=='en'else'팝업 닫힘');assert cursor_visible(),(language,'editor cursor not restored')
            assert 'Z'not in ''.join(screen.rows[2]),(language,'background text changed while modal open')
            send('l',b'l');wait_text('Scroll: 4'if lang=='en'else'스크롤: 4');assert cursor_visible(),(language,'scroll cursor lost')
            send('next',b'\t');assert not cursor_visible(),(language,'unfocused editor cursor visible')
            # The host translates terminal coordinates into the nested child viewport.
            send('click 26 2',b'\x1b[<0;27;3M');assert cursor_visible(),(language,'translated editor click failed')
            if language!='java':
                fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0));send('h',b'h');wait_text('Scroll: 0'if lang=='en'else'스크롤: 0')
                deadline=time.monotonic()+5
                while screen.rows[0][39]!=('+'if ascii else'╗')and time.monotonic()<deadline:drain(.02)
                assert screen.rows[0][39]==('+'if ascii else'╗'),(language,'container resize frame',visible())
                send('m',b'm');wait_text('Popup open'if lang=='en'else'팝업 열림');assert not cursor_visible()
                for yy in range(1,16):assert screen.rows[yy][0]==('|'if ascii else'║')and screen.rows[yy][39]==('|'if ascii else'║'),(language,'container clipped bounds',yy,visible())
        elif demo=='layout':
            def visible():return '\n'.join(''.join(row)for row in screen.rows[:24])
            def wait_text(value):
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    drain(.02)
                    if value.replace(' ','')in visible().replace(' ',''):return
                    if process.poll()is not None:break
                raise AssertionError((language,demo,value,visible()))
            def send(command,raw):
                frames=captured.count(b'\x1b[0m');os.write(master,(command+'\n').encode()if language=='java'else raw)
                deadline=time.monotonic()+5
                while captured.count(b'\x1b[0m')<=frames and time.monotonic()<deadline:drain(.02)
                assert captured.count(b'\x1b[0m')>frames,(language,'layout frame acknowledgment',visible())
            def click_x(row):
                x=''.join(screen.rows[row]).rfind(' x')+1;assert x>20,(language,'chip close target',row,visible())
                send('click '+str(x)+' '+str(row),('\x1b[<0;'+str(x+1)+';'+str(row+1)+'M').encode())
            wait_text('Items [99+]'if lang=='en'else'항목 [99+]')
            deadline=time.monotonic()+5
            while not captured.count(b'\x1b[0m')and time.monotonic()<deadline:drain(.02)
            label='Recent'if lang=='en'else'최근'
            click_x(6);assert label in ''.join(screen.rows[2]).replace(' ',''),(language,'disabled chip removed active filter')
            click_x(4);assert label in ''.join(screen.rows[2]).replace(' ',''),(language,'read-only chip removed active filter')
            click_x(2);wait_text('Filter removed.'if lang=='en'else'필터를 제거했습니다.')
            assert label not in visible().replace(' ',''),(language,'stale filter after host approval')
            send('x',b'x');assert label not in visible().replace(' ',''),(language,'removed filter reappeared')
            send('d',b'd');wait_text('Density: comfortable'if lang=='en'else'밀도: 여유')
            if language!='java':
                fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0))
                send('d',b'd');wait_text('Density: compact'if lang=='en'else'밀도: 촘촘')
                deadline=time.monotonic()+5
                while screen.rows[0][39]!=('+'if ascii else'╗')and time.monotonic()<deadline:drain(.02)
                assert screen.rows[0][39]==('+'if ascii else'╗'),(language,'narrow frame',visible())
                for y in range(1,16):assert screen.rows[y][0]==('|'if ascii else'║')and screen.rows[y][39]==('|'if ascii else'║'),(language,'narrow bounds',y,visible())
                assert b'\x1b[?25h'not in captured,(language,'supporting component registered a cursor')
        elif demo=='feedback':
            def visible():return '\n'.join(''.join(row)for row in screen.rows[:24])
            def wait_text(value):
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    drain(.02)
                    if value.replace(' ','')in visible().replace(' ',''):return
                    if process.poll()is not None:break
                raise AssertionError((language,demo,value,visible()))
            def send(command,raw):
                frames=captured.count(b'\x1b[0m')
                os.write(master,(command+'\n').encode()if language=='java'else raw)
                deadline=time.monotonic()+5
                while captured.count(b'\x1b[0m')<=frames and time.monotonic()<deadline:
                    drain(.02)
                assert captured.count(b'\x1b[0m')>frames,(language,'feedback frame acknowledgment',visible())
            def click(x,y):send('click '+str(x)+' '+str(y),('\x1b[<0;'+str(x+1)+';'+str(y+1)+'M').encode())
            wait_text('Demo operation failed'if lang=='en'else'예제 작업 실패');wait_text('40%')
            send('down',b'\x1b[B');send('down',b'\x1b[B')
            assert screen.rows[4][2]=='>',(language,'notice navigation')
            word='Unavailable'if lang=='en'else'사용 불가'
            pattern=r'\[\s*'+r'\s*'.join(re.escape(ch)for ch in word if ch!=' ')+r'\s*\]'
            off=re.search(pattern,''.join(screen.rows[2]));assert off,(language,'missing disabled action')
            click(off.start(),2)
            assert screen.rows[4][2]=='>',(language,'disabled action changed parent focus')
            word='Retry'if lang=='en'else'재시도'
            pattern=r'\[\s*'+r'\s*'.join(re.escape(ch)for ch in word)+r'\s*\]'
            retry=re.search(pattern,''.join(screen.rows[2]));assert retry,(language,'missing retry action')
            click(retry.start(),2);wait_text('Retry accepted'if lang=='en'else'재시도 요청 처리')
            send('delete',b'\x1b[3~');wait_text('Notice dismissed.'if lang=='en'else'알림을 닫았습니다.')
            send('t',b't');wait_text('Expired notices: 1'if lang=='en'else'만료한 알림: 1')
            click(3,9);wait_text('Export cancelled'if lang=='en'else'내보내기 취소됨')
            assert '40%'not in visible(),(language,'stale progress after cancellation')
            if language!='java':assert b'\x1b[?25h'not in captured,(language,'feedback unexpectedly registered a cursor')
        elif demo in ('menu','context-menu'):
            def visible():return '\n'.join(''.join(row) for row in screen.rows[:17])
            def wait_text(value):
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    drain(.02)
                    if value.replace(' ','') in visible().replace(' ',''):return
                    if process.poll()is not None:break
                raise AssertionError((language,demo,value,visible(),bytes(captured[-500:])))
            def send(command,raw):
                os.write(master,(command+'\n').encode()if language=='java'else raw);drain(.10)
            wait_text(('Context menu'if lang=='en'else'문맥 메뉴')if demo=='context-menu'else('New document'if lang=='en'else'새 문서'))
            send('insert Z',b'Z')
            assert 'Z'not in ''.join(''.join(row)for row in screen.rows[1:3]),(language,'popup leaked text to editor')
            if demo=='menu':
                send('down',b'\x1b[B');send('activate',b'\r');wait_text('Example A'if lang=='en'else'예제 A')
                send('cancel',b'\x1b')
                wait_text('New document'if lang=='en'else'새 문서')
            else:
                send('activate',b'\r');wait_text('New document'if lang=='en'else'새 문서')
                send('cancel',b'\x1b');wait_text('Context menu'if lang=='en'else'문맥 메뉴')
            send('cancel',b'\x1b')
            send('home',b'\x1b[H');send('insert Z',b'Z')
            deadline=time.monotonic()+5
            while 'Z'not in ''.join(''.join(row)for row in screen.rows[1:3]) and time.monotonic()<deadline:
                drain(.02)
            assert 'Z'in ''.join(''.join(row)for row in screen.rows[1:3]),(language,'editor not restored',visible())
            send('context 52 14',b'\x1b[<2;53;15M')
            wait_text('Context menu'if lang=='en'else'문맥 메뉴')
            # Read actual VT output after the popup overlays two-cell background text.
            title='Context menu'if lang=='en'else'문맥 메뉴'
            rows=[''.join(row)for row in screen.rows]
            pattern='\\s*'.join(re.escape(ch)for ch in title if ch!=' ')
            top=next(y for y,row in enumerate(rows)if re.search(pattern,row))
            match=re.search(pattern,rows[top])
            left=rows[top].rfind('+'if ascii else'┌',0,match.start())
            right=rows[top].find('+'if ascii else'┐',match.end())
            assert 1<=left<right<79,(language,'popup columns',rows[top])
            bottom=next(y for y in range(top+1,len(rows))if rows[y][left:left+1]==('+'if ascii else'└'))
            assert bottom<23,(language,'popup escaped viewport')
            for y in range(top+1,bottom):
                assert rows[y][left]==('|'if ascii else'│')and rows[y][right]==('|'if ascii else'│'),(language,'wide text damaged popup border',y,rows[y])
            send('cancel',b'\x1b')
        elif demo=='picker':
            drain(.25)
            def wait_text(value):
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    drain(.02)
                    visible='\n'.join(''.join(row)for row in screen.rows[1:17])
                    if value in visible:return
                    if process.poll()is not None:break
                raise AssertionError((language,'picker',value,visible))
            os.write(master,b'insert Rust\n'if language=='java'else b'Rust');drain(.08)
            os.write(master,b'activate\n'if language=='java'else b'\r');wait_text('v Rust')
            os.write(master,b'activate\n'if language=='java'else b'\r');drain(.08)
            os.write(master,b'insert Go\n'if language=='java'else b'Go');drain(.08)
            os.write(master,b'cancel\n'if language=='java'else b'\x1b');wait_text('v Rust')
            assert b'\x1b[?25h'in captured,(language,'picker query cursor absent')
        elif demo=='form':
            drain(.25)
            os.write(master,b'select_all\n'if language=='java'else b'\x01');drain(.05)
            os.write(master,b'insert Z\n'if language=='java'else b'Z');drain(.08)
            visible='\n'.join(''.join(row)for row in screen.rows[1:17])
            assert 'Z'in visible,(language,'form text edit',visible)
            # Disabled checkbox is skipped while tabbing to the select.
            for _ in range(2):os.write(master,b'tab\n'if language=='java'else b'\t');drain(.06)
            os.write(master,b'activate\n'if language=='java'else b'\r');drain(.05)
            os.write(master,b'down\n'if language=='java'else b'\x1b[B');drain(.05)
            os.write(master,b'activate\n'if language=='java'else b'\r');drain(.08)
            visible='\n'.join(''.join(row)for row in screen.rows[1:17]).replace(' ','')
            assert ('Alternative'if lang=='en'else'다른값')in visible,(language,'form select commit',visible)
            assert 'example'not in visible,(language,'raw password in output')
            assert b'\x1b[?25h'in captured,(language,'real form cursor absent')
        elif demo=='text':
            from ansi_cells import complete_frame
            def wait_text_frame(previous, expected=None):
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    drain(.02)
                    visible='\n'.join(''.join(r)for r in screen.rows[1:17])
                    trailer=bytes(captured).rsplit(b'\x1b[?25l',1)[-1]
                    if language=='java':trailer=trailer.split(b'\x1b[19;1H',1)[0]
                    cursor=re.search(rb'\x1b\[(\d+);(\d+)H\x1b\[\?25h',trailer)
                    if captured.count(b'\x1b[?25l')>previous and complete_frame(captured)is not None and cursor and (expected is None or ('Z'in visible)==expected):return
                    if process.poll()is not None:break
                raise AssertionError((language,'text frame/cursor',expected,visible,bytes(captured[-600:])))
            wait_text_frame(0)
            for command,raw,expected in [('home',b'\x1b[H',None),('insert Z',b'Z',True),('backspace',b'\x7f',False)]:
                frames=captured.count(b'\x1b[?25l')
                os.write(master,(command+'\n').encode()if language=='java'else raw)
                wait_text_frame(frames,expected)
        else:
            # Row one contains the selected root. The actual VT buffer is inspected.
            root=4 if demo=='workspace' else 2 if demo=='list' else 1
            wait_row(root,True)
            down=b'down\n'if language=='java'else b's'if language in ['c','cpp']else b'\x1b[B'
            up=b'up\n'if language=='java'else b'w'if language in ['c','cpp']else b'\x1b[A'
            os.write(master,down);wait_row(5 if demo=='list'else root+1,True);wait_row(root,False)
            os.write(master,up);wait_row(root,True)
            if language in ['python','javascript']:
                os.write(master,b'\x1bOP\x1bOQ');drain(.05);wait_row(root,True)
            if demo=='workspace':
                os.write(master,b'tab\n'if language=='java'else b'\t');drain(.05)
                os.write(master,b'right\n'if language=='java'else b'd'if language in ['c','cpp']else b'\x1b[C');drain(.05)
                os.write(master,b'activate\n'if language=='java'else b'\r');drain(.1)
                visible='\n'.join(''.join(row)for row in screen.rows)
                assert ('Draft'if lang=='en'else'초안')in visible.replace(' ',''),(language,'tab activation',visible)
        os.write(master,b'quit\n'if language=='java'else b'\x1b\x11'if demo in ('menu','context-menu')else b'\x11')
        deadline=time.monotonic()+5
        while process.poll()is None and time.monotonic()<deadline:drain(.02)
        process.wait(timeout=.1);drain(.02)
        assert process.returncode==0,(language,process.returncode,bytes(captured[-1000:]))
        assert termios.tcgetattr(slave)==original,(language,'terminal not restored')
        assert not re.search(rb'\x1b\[[0-9;]* q',captured)
        assert not re.search(rb'\x1b\[\?12[hl]',captured)
        if language!='java':
            assert b'\x1b[?1049h'in captured and b'\x1b[?1049l'in captured
            if demo=='drag':assert b'\x1b[?1002h'in captured and b'\x1b[?1002l'in captured,(language,'drag motion mode not restored')
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
    p.add_argument('--demo',choices=['drag','tree','workspace','text','form','list','picker','menu','context-menu','feedback','layout','container','surface','shadow','dialog','document','syntax','grid'],default='tree')
    args=p.parse_args()
    arch={'aarch64':'arm64','x86_64':'x86_64'}[platform.machine()]
    commands={'python':[args.python,'-m','tuivory'],'javascript':['node',ROOT/'javascript/examples/catalog.mjs'],'c':[ROOT/'bin/c'/f'tuivory-linux-{arch}'],'cpp':[ROOT/'bin/cpp'/f'tuivory-linux-{arch}'],'java':['java','-jar',ROOT/'.cache/packages/java'/f'tuivory-{(ROOT/"VERSION").read_text().strip()}.jar']}
    results=[]
    for language,cmd in commands.items():
        if args.language and args.language!=language:continue
        help_env=dict(os.environ)
        if language=='python':help_env['PYTHONPATH']=str(ROOT/'python/src')
        help_text=subprocess.check_output([*map(str,cmd),'--help'],cwd=ROOT,env=help_env,text=True)
        assert re.search(r'(?<![\w-])'+re.escape(args.demo)+r'(?![\w-])',help_text),(language,'demo missing from help',args.demo,help_text)
        for lang in ['ko','en']:
            for theme in ['dark','light','blackwhite']if args.matrix else['dark']:
                for colors in ['8','16','256','truecolor']if args.matrix else['256']:
                    for ascii in [False,True]if args.matrix else[False]:
                        r=check(language,cmd,lang,theme,colors,ascii,args.demo);results.append(r)
                        print('PASS',language,lang,theme,colors,'ascii='+str(ascii),args.demo,flush=True)
    name='pty'+(''if args.demo=='tree'else'-'+args.demo)+('-'+args.language if args.language else'')+(''if args.matrix else'-smoke')+'-results.json'
    out=ROOT/'.cache/validation/languages'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
