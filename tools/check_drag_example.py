"""Actual independent drag hosts: captured events, host approvals and restoration."""
import fcntl,json,os,struct,termios,time
from pathlib import Path
from ansi_cells import read_cells,complete_frame
ROOT=Path(__file__).resolve().parents[1]

def check_drag_example(language,lang,theme,colors,ascii,master,slave,process,captured,screen,drain):
    def visible():return '\n'.join(''.join(row)for row in screen.rows[:24])
    def wait(value,present=True):
        end=time.monotonic()+5
        while time.monotonic()<end:
            drain(.02)
            if (value.replace(' ','')in visible().replace(' ',''))==present:return
            if process.poll()is not None:break
        raise AssertionError((language,lang,theme,colors,ascii,value,present,visible()))
    def send(command,raw):
        frames=captured.count(b'\x1b[0m');os.write(master,(command+'\n').encode()if language=='java'else raw)
        end=time.monotonic()+5
        while time.monotonic()<end:
            drain(.02)
            if captured.count(b'\x1b[0m')>frames and complete_frame(captured)is not None:return
            if process.poll()is not None:break
        raise AssertionError((language,'drag frame missing',command,visible()))
    def pointer(action,x,y):
        button=32 if action=='move'else 0;ending='m'if action=='up'else'M'
        send('pointer '+action+' '+str(x)+' '+str(y),('\x1b[<'+str(button)+';'+str(x+1)+';'+str(y+1)+ending).encode())
    def row(label):
        for i,r in enumerate(screen.rows[:18]):
            if label.replace(' ','')in ''.join(r).replace(' ',''):return i
        raise AssertionError((label,visible()))
    archive='Archive'if lang=='en'else'보관함';notes='Notes'if lang=='en'else'메모';pending='Pending approval:'if lang=='en'else'승인 대기:'
    approved='Host approved the move.'if lang=='en'else'앱이 이동을 승인했습니다.'
    rejected='Host rejected the move.'if lang=='en'else'앱이 이동을 거절했습니다.'
    wait('Dragging: ON | idle'if lang=='en'else'드래그: ON | idle');assert row(archive)==6 and row(notes)==7,visible()
    if language!='java':assert b'\x1b[?1002h'in captured,(language,'motion reporting not enabled')
    # A sub-threshold click must select once and produce no approval request.
    pointer('down',10,7);pointer('up',10,7);wait(pending,False)
    pointer('down',10,7);pointer('move',12,6)
    wait('dragging');assert row(notes)==8,(language,'preview expansion absent',visible())
    frame=complete_frame(captured);assert frame is not None
    cell=read_cells(frame.decode())[1,6]
    assert cell[0]==('+'if ascii else'↳')and cell[3]and cell[5],(language,'drag feedback missing',cell)
    pointer('up',12,6);wait(pending);assert row(notes)==7,(language,'unapproved data changed',visible())
    send('r',b'r');wait(rejected);assert row(notes)==7
    pointer('down',10,7);pointer('move',12,6);pointer('up',12,6);wait(pending)
    send('y',b'y');wait(approved);wait(notes,False)
    # Open the approved target; the moved node follows its existing child.
    for command,raw in [('home',b'\x1b[H'),('down',b'\x1b[B'),('down',b'\x1b[B'),('down',b'\x1b[B'),('right',b'\x1b[C')]:send(command,raw)
    wait(notes);assert row(notes)==8,(language,'approved subtree order',visible())
    # Keyboard move inside and outside uses the same app approval path.
    send('next',b'\t');send(']',b']');wait(pending);send('y',b'y');wait(approved)
    send('d',b'd');wait('Dragging: OFF'if lang=='en'else'드래그: OFF')
    pointer('down',3,1);pointer('move',20,1);pointer('up',20,1);wait(pending,False)
    send('d',b'd');wait('Dragging: ON'if lang=='en'else'드래그: ON')
    # Capture outside release rejects without mutating tabs.
    pointer('down',3,1);pointer('move',79,23);pointer('up',79,23);wait(pending,False)
    if language!='java':
        # Changing palette invalidates capture; no drop may leak across contexts.
        pointer('down',3,1);send('theme',b'\x1bOP');wait('idle');pointer('up',20,1);wait(pending,False)
        fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',18,40,0,0));send('d',b'd');wait('Dragging: OFF'if lang=='en'else'드래그: OFF')
        assert screen.rows[0][39]==('+'if ascii else'╗'),(language,'narrow drag border',visible())
