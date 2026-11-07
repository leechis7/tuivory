"""Exercise document model behavior through actual independent example PTYs."""
import fcntl,json,os,re,struct,termios,time
from pathlib import Path
from ansi_cells import complete_frame,read_cells
ROOT=Path(__file__).resolve().parents[1]
def check_document_example(language,lang,theme,colors,ascii,master,slave,process,captured,screen,drain):
    palette=json.loads((ROOT/'design/tokens/candidate.json').read_text())['palettes'][theme+'-'+colors]
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
        wait(lambda:complete_frame(captured)is not None,'complete document frame')
        return read_cells(complete_frame(captured).decode())
    def trailer():
        start=captured.rfind(b'\x1b[?25l');data=bytes(captured[start:])
        return data.split(b'\x1b[19;1H\x1b[K> ')[0]if language=='java'else data
    def cursor(x,y):wait(lambda:f'\x1b[{y+1};{x+1}H\x1b[?25h'.encode()in trailer(),('actual cursor',x,y))
    def send(command,raw):
        count=captured.count(b'\x1b[0m');os.write(master,(command+'\n').encode()if language=='java'else raw)
        wait(lambda:captured.count(b'\x1b[0m')>count,'command frame '+command);frame()
    def key(letter):send(letter,letter.encode())
    wait_text('Editor | Wrap on'if lang=='en'else'편집 | 줄바꿈 on');frame();cursor(3,1)
    wait_text('[error]Tags remain literal text.[/]'if lang=='en'else'[error]태그도 원문 그대로입니다.[/]')
    assert frame()[5,1][2]==palette['editor']['background'],(language,'editor background')
    key('s');wait(lambda:frame()[3,1][2]==palette['edited']['background'],'search background')
    key('v');wait_text('Viewer'if lang=='en'else'보기');assert b'\x1b[?25h'not in trailer(),(language,'viewer cursor leak')
    key('v');wait_text('Editor'if lang=='en'else'편집');cursor(3,1)
    key('x');wait_text('Disabled on'if lang=='en'else'비활성 on');wait(lambda:frame()[3,1][4],'disabled text Dim');assert b'\x1b[?25h'not in trailer(),(language,'disabled cursor leak')
    send('click 3 2',b'\x1b[<0;4;3M');send('insert Z',b'Z');assert 'Z'not in visible(),(language,'disabled insert accepted')
    key('x');wait_text('Disabled off'if lang=='en'else'비활성 off');cursor(3,1)
    if language!='java':
        fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0));key('w')
        wait(lambda:screen.rows[0][39]==('+'if ascii else'╗'),'40-column document resize');wait_text('Wrap off'if lang=='en'else'줄바꿈 off')
        key('w');wait_text('Wrap on'if lang=='en'else'줄바꿈 on')
    send('click 3 2',b'\x1b[<0;4;3M');cursor(3,2)
    send('select_all',b'\x01');send('insert Z',b'Z');wait_text('Z')
    key('m');wait_text('Explicit markup'if lang=='en'else'명시적 마크업');wait_text('[error] stays literal.'if lang=='en'else'[error]는 리터럴입니다.');cursor(3,1)
    key('n');wait_text('Numbers off'if lang=='en'else'줄 번호 off');cursor(1,1)
    wait(lambda:frame()[1,1][2]==palette['editor']['background'],'explicit markup retains editor background')
