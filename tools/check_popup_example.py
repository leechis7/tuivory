"""Actual PTY interaction checks for the independent popup example hosts."""
import fcntl,os,re,struct,termios,time
from ansi_cells import complete_frame,read_cells

def check_popup_example(language,demo,lang,ascii,master,slave,process,captured,screen,drain):
    def visible():return '\n'.join(''.join(row)for row in screen.rows[:24])
    def frame():
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            drain(.02);f=complete_frame(captured)
            if f is not None:return read_cells(f.decode())
            if process.poll()is not None:break
        raise AssertionError((language,demo,'incomplete frame',bytes(captured[-400:])))
    def wait_text(value):
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            drain(.02)
            if value.replace(' ','')in visible().replace(' ',''):return
            if process.poll()is not None:break
        raise AssertionError((language,demo,value,visible()))
    def send(command,raw):
        count=captured.count(b'\x1b[0m');os.write(master,(command+'\n').encode()if language=='java'else raw)
        deadline=time.monotonic()+5
        while captured.count(b'\x1b[0m')<=count and time.monotonic()<deadline:drain(.02)
        assert captured.count(b'\x1b[0m')>count,(language,demo,'no response',visible())
        frame()
    def mouse(x,y,button=0):send(f'click {x} {y}',f'\x1b[<{button};{x+1};{y+1}M'.encode())
    def cancel():send('cancel',b'\x1b')
    if demo=='shadow':
        wait_text('Shadow: auto'if lang=='en'else'그림자: 자동')
        cells=frame()
        if not ascii:assert any(c[0]=='▀'for c in cells.values()),(language,'missing half-row shadow')
        for command,label in [('s','solid'if lang=='en'else'검정'),('s','off'if lang=='en'else'끄기'),('s','auto'if lang=='en'else'자동'),('d','dim'if lang=='en'else'Dim')]:
            send(command,command.encode());wait_text(('Shadow: 'if lang=='en'else'그림자: ')+label)
            if label in ('off','끄기','dim','Dim'):assert not any(c[0]in('▀','▄')for c in frame().values()),(language,'stale half shadow',label)
        send('s',b's');wait_text('Shadow: auto'if lang=='en'else'그림자: 자동')
        # Pointer on visual shadow never dispatches an item or changes editor focus.
        cells=frame();halves=[xy for xy,c in cells.items()if c[0]in('▀','▄')]
        if halves:mouse(*halves[-1]);assert not any('Selected:'in ''.join(row)for row in screen.rows)
        cancel()
        send('insert Z',b'Z');wait_text('Z')
        send('context 67 12',b'\x1b[<2;68;13M')
        wait_text('Context menu'if lang=='en'else'문맥 메뉴')
        if language!='java':
            fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0));send('s',b's')
            deadline=time.monotonic()+5
            while screen.rows[0][39]!=('+'if ascii else'╗')and time.monotonic()<deadline:drain(.02)
            assert screen.rows[0][39]==('+'if ascii else'╗'),(language,'shadow resize',visible())
        cancel()
    else:
        wait_text('Reconnect'if lang=='en'else'다시 연결');frame()
        send('x',b'x')
        cells=frame();needle='Cancel'if lang=='en'else'취소'
        def locate():
            for y,row in enumerate(screen.rows[:18]):
                positions=[(x,ch)for x,ch in enumerate(row)if ch!=' ']
                text=''.join(ch for x,ch in positions);at=text.find(needle)
                if at>=0:return positions[at][0],y
            raise AssertionError((language,'Cancel invisible',visible()))
        deadline=time.monotonic()+5
        while True:
            cells=frame();x,y=locate()
            if cells.get((x,y),('',None,None,None,False))[4]:break
            assert time.monotonic()<deadline,(language,'disabled Cancel has no Dim',cells.get((x,y)))
        mouse(x,y);assert 'Host accepted:'not in visible()and'앱이 수락한 요청:'not in visible(),(language,'disabled click accepted')
        cancel();assert 'Host accepted:'not in visible()and'앱이 수락한 요청:'not in visible(),(language,'disabled cancel accepted')
        send('x',b'x')
        if language!='java':
            fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0));send('m',b'm')
            deadline=time.monotonic()+5
            while screen.rows[0][39]!=('+'if ascii else'╗')and time.monotonic()<deadline:drain(.02)
            assert screen.rows[0][39]==('+'if ascii else'╗'),(language,'dialog resize',visible())
            frame()
            x,y=locate();assert x+len(needle)<39,(language,'Cancel clipped',visible())
        cancel();wait_text('Host accepted: cancel'if lang=='en'else'앱이 수락한 요청: cancel')
        start=len(captured);send('insert Z',b'Z');wait_text('Z')
        if language!='java':assert b'\x1b[?25h'in captured[start:],(language,'editor cursor not restored')
        send('m',b'm');send('activate',b'\r');wait_text('Host accepted: cancel'if lang=='en'else'앱이 수락한 요청: cancel')
        send('m',b'm');send('home',b'\x1b[H');send('activate',b'\r');wait_text('Host accepted: retry'if lang=='en'else'앱이 수락한 요청: retry')
