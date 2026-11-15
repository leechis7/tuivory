#!/usr/bin/env python3
"""Exercise the English public workspace in a PTY, including reflow and input."""
import argparse
import fcntl
import os
import pty
import select
import signal
import struct
import subprocess
import termios
import time
from pathlib import Path
from smoke_focus import Screen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path); parser.add_argument('--demo', help='select an example from the unified executable')
parser.add_argument('--host-policy', choices=['default','alternate'], default='default')
parser.add_argument('--tab-rows', type=int, choices=[1,3], help='test the explicit demo tab height')
parser.add_argument('--lang', choices=['ko','en'], default='en')
args = parser.parse_args()
# Invalid app policy must fail before any terminal setup, not just fail for a missing TTY.
for option,value in [('--tab-rows','2'),('--layout','diagonal'),('--quit-key','ctrl-c'),('--focus-order','tabs,tree'),('--focus-order','tabs,tabs,content'),('--focus-order','tabs,tree,unknown')]:
    invalid=subprocess.run([str(args.binary.resolve()), *(['--demo', args.demo] if args.demo else []),option,value],stdin=subprocess.DEVNULL,capture_output=True,timeout=5)
    if invalid.returncode==0 or option.encode() not in invalid.stderr or b'\x1b[?1049h' in invalid.stdout:
        raise RuntimeError(f'Invalid policy reached terminal setup: {option}={value}: {invalid.stderr!r}')
master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 32, 120, 0, 0))

def terminal():
    os.setsid()
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)

process = None
captured = bytearray()
screen = Screen()
reports = 0

def drain(seconds):
    global reports
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if select.select([master], [], [], .03)[0]:
            try:
                data=os.read(master, 65536)
                captured.extend(data)
                screen.feed(data)
            except OSError:
                return
            while reports < captured.count(b'\x1b[6n'):
                os.write(master, b'\x1b[1;1R')
                reports += 1

def send(data):
    os.write(master, data)
    drain(.2)
    if process.poll() is not None:
        raise RuntimeError('Workspace exited during input: ' + captured[-300:].decode(errors='replace'))

def visible(): return ''.join(''.join(row) for row in screen.rows).replace(' ','')

try:
    options=['--layout','rows','--focus-order','content,tree,tabs','--quit-key','ctrl-x'] if args.host_policy=='alternate' else []
    if args.tab_rows is not None:
        options += ['--tab-rows', str(args.tab_rows)]
    title_row = 3 if args.tab_rows == 3 else 2
    process = subprocess.Popen([str(args.binary.resolve()), *(['--demo', args.demo] if args.demo else []), '--lang', args.lang]+options, stdin=slave, stdout=slave,
                               stderr=slave, preexec_fn=terminal,
                               env=dict(os.environ, TERM='xterm-256color'))
    os.close(slave)
    slave = None
    drain(.6)
    if args.host_policy=='alternate':
        content='내용' if args.lang=='ko' else 'Content'
        explorer='탐색' if args.lang=='ko' else 'Explorer'
        assert '>'+content in visible(), visible()
        assert 'Ctrl+X' in visible() and 'Ctrl+Q' not in visible(), visible()
        send(b'\x11')  # The old global shortcut must no longer quit.
        send(b'\t')
        assert '>'+explorer in visible(), visible()
        send(b'\t')  # Supplied order routes to tabs, not content.
        send(b'\x1b[C');send(b'\r');send(b'x')
        guard='보류' if args.lang=='ko' else 'retained'
        assert guard in visible(),visible()
        send(b'\x1b[Z')
        assert '>'+explorer in visible(),visible()
        send(b'\x1b[Z')
        assert '>'+content in visible(),visible()
        send(b'\x1b[17~')  # Initial rows -> columns, using the same split model.
        assert screen.rows[7][32] in ('│','|'),visible()
        for height,width in ((16,32),(32,120)):
            fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',height,width,0,0))
            os.killpg(process.pid,signal.SIGWINCH);drain(.2)
        send(b'\x1b[12~');send(b'\x1b[13~')
    else:
        draft = '변경된' if args.lang == 'ko' else 'Edited'
        title_cells = screen.rows[title_row]
        assert draft in ''.join(title_cells).replace(' ', ''), visible()
        draft_x = title_cells.index(draft[0])
        active = '활성탭:overview' if args.lang == 'ko' else 'Activetab:overview'
        if args.tab_rows == 3:
            assert '┌' in screen.rows[2] and '─' in screen.rows[4], visible()
            # Decorative rows should not trigger activation.
            for y in (2, 4):
                send(f'\x1b[<0;{draft_x+1};{y+1}M\x1b[<0;{draft_x+1};{y+1}m'.encode())
            assert active in visible(), visible()
        else:
            assert '─' not in screen.rows[2], visible()
        # Focus and activate the edited document; closing must retain it in the host.
        send(b'\x1b[C')
        assert active in visible() and '>'+draft in ''.join(screen.rows[title_row]).replace(' ',''), visible()
        send(b'\r')
        send(b'x')
        if ('보류' if args.lang=='ko' else 'retained') not in visible():
            raise RuntimeError('Edited-tab close guard was not rendered: ' + captured[-500:].decode(errors='replace'))
        # Click another title to activate it on the actual title row.
        overview = '개요' if args.lang == 'ko' else 'Overview'
        x = screen.rows[title_row].index(overview[0])
        send(f'\x1b[<0;{x+1};{title_row+1}M\x1b[<0;{x+1};{title_row+1}m'.encode())
        assert active in visible(), visible()
        send(b'\x1b[C')
        send(b'\r')
        # Clear edited state, request close again, then change theme/profile/ASCII.
        for key in (b'\x1b[15~', b'x', b'\x1b[12~', b'\x1b[13~', b'\x1b[14~'):
            send(key)
        # Drag the column divider; exercise tree focus and global keyboard resizing.
        for event in (b'\x1b[<0;33;10M', b'\x1b[<32;45;10M', b'\x1b[<0;45;10m'):
            send(event)
        send(b'\t')
        send(b'\x1b[B')
        send(b'\x1b[1;5C')
        for height, width in ((16, 32), (32, 120)):
            fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', height, width, 0, 0))
            os.killpg(process.pid, signal.SIGWINCH)
            drain(.2)
        send(b'\x1b[17~')  # Switch to row split and resize it with Ctrl+Down.
        send(b'\x1b[1;5B')
    os.write(master, b'\x18' if args.host_policy=='alternate' else b'\x11')
    drain(.5)
    process.wait(timeout=3)
    if process.returncode != 0 or b'\x1b[?1049l' not in captured:
        raise RuntimeError('Workspace exit/restore failed')
    print(f'Workspace {args.host_policy}/{args.lang}: edited-close, host keys/focus/layout, resize and terminal restore passed.')
finally:
    if process is not None and process.poll() is None:
        process.kill()
        process.wait()
    if slave is not None:
        os.close(slave)
    os.close(master)
