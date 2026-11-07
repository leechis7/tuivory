"""Actual independent Grid example: host approval, source data and real cursors."""
import fcntl,json,os,re,struct,termios,time
from pathlib import Path
from ansi_cells import complete_frame,read_cells
ROOT=Path(__file__).resolve().parents[1]
def check_grid_example(language,lang,theme,colors,ascii,master,slave,process,captured,screen,drain):
    def visible():return '\n'.join(''.join(row)for row in screen.rows[:24])
    def wait(predicate,message):
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            drain(.02)
            if predicate():return
            if process.poll()is not None:break
        raise AssertionError((language,lang,theme,colors,ascii,message,visible()))
    def wait_text(text):wait(lambda:text.replace(' ','')in visible().replace(' ',''),text)
    def frame():
        wait(lambda:complete_frame(captured)is not None,'complete grid frame')
        return read_cells(complete_frame(captured).decode())
    def trailer():
        start=captured.rfind(b'\x1b[?25l');data=bytes(captured[start:])
        return data.split(b'\x1b[19;1H\x1b[K> ')[0]if language=='java'else data
    def shown():return b'\x1b[?25h'in trailer()
    def send(command,raw):
        count=captured.count(b'\x1b[0m');os.write(master,(command+'\n').encode()if language=='java'else raw)
        wait(lambda:captured.count(b'\x1b[0m')>count,'command frame '+command);frame()
    def key(value):send(value,value.encode())
    def activate():send('activate',b'\r')
    def cancel():send('cancel',b'\x1b')
    def submit():
        activate();wait_text('Pending approval'if lang=='en'else'승인 대기');wait(lambda:not shown(),'submitted editor hides cursor')
    def approve():
        key('y');wait_text('Host approved'if lang=='en'else'앱이 요청을 승인');wait(lambda:not shown(),'approved editor closes cursor')
    def select_all():send('select_all',b'\x01')
    def click(x,y):send(f'click {x-1} {y-1}',f'\x1b[<0;{x+1};{y+1}M'.encode())
    def status(number):wait_text(f'{number}/8')
    wait_text('Name'if lang=='en'else'이름');wait_text('1,234');status(1);frame()
    assert not shown(),(language,'non-editing grid cursor')
    assert frame()[10,4][4],(language,'disabled row must be Dim')
    activate();wait(shown,'real grid edit cursor')
    select_all();send('insert EDITED',b'EDITED')
    wait(lambda:b'\x1b[3;17H\x1b[?25h'in trailer(),'grapheme cursor after ASCII edit')
    submit()
    key('r');wait_text('Host rejected'if lang=='en'else'앱이 요청을 거절');wait(shown,'rejected edit returns real cursor')
    submit();approve()
    key('c');wait_text('Raw copy: EDITED'if lang=='en'else'복사 원문: EDITED')
    key('/');wait(shown,'find field cursor');send('insert target',b'target');wait_text('target');activate()
    wait_text('Match found'if lang=='en'else'검색 일치');status(7);assert not shown()
    click(12,4);status(7) # Disabled row is not selectable.
    click(12,5);status(4);activate();wait_text('cannot be edited'if lang=='en'else'편집할 수 없는');assert not shown()
    send('home',b'\x1b[H');status(1);send('down',b'\x1b[B');status(2);send('right',b'\x1b[C')
    activate();assert not shown(),(language,'NULL editor cursor')
    send('null',b'\x0e');wait(shown,'NULL toggled to empty text')
    send('insert NULLTEST',b'NULLTEST');wait_text('NULLTEST');submit();approve();wait_text('NULLTEST')
    activate();send('null',b'\x0e');wait(lambda:not shown(),'NULL editor hides cursor');submit();approve();key('c')
    wait_text('Raw copy: NULL'if lang=='en'else'복사 원문: NULL')
    send('left',b'\x1b[D');key('p');wait_text('Pending approval'if lang=='en'else'승인 대기');key('r')
    key('p');wait_text('Pending approval'if lang=='en'else'승인 대기');approve();wait_text('paste name');wait_text('raw value')
    send('right',b'\x1b[C');key('d');wait_text('Raw cell details'if lang=='en'else'원문 상세')
    assert not shown();wait_text('raw');wait_text('value');cancel();status(2)
    key('b');wait_text('View saved'if lang=='en'else'보기 저장됨');send('down',b'\x1b[B');status(4)
    key('b');wait_text('View restored'if lang=='en'else'보기 복원됨');status(2)
    key('v')
    if language!='java':
        fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0));key('v')
        wait(lambda:screen.rows[0][39]==('+'if ascii else'╗'),'40-column grid')
    send('home',b'\x1b[H');send('left',b'\x1b[D');activate();select_all()
    wide='ascii_grapheme_abcdefghijklmnopqrst'if lang=='en'and ascii else'한글👩‍💻éabcdefghijklmnopqrst'
    send('insert '+wide,wide.encode())
    wait_text('qrst');wait(shown,'whole-grapheme cursor in clipped cell')
    found=re.findall(rb'\x1b\[(\d+);(\d+)H\x1b\[\?25h',trailer());assert found,(language,'missing hardware cursor')
    y,x=map(int,found[-1]);assert 0<x<=(72 if language=='java'else 40)and 0<y<18
    submit();approve()
