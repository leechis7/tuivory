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

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path)
args = parser.parse_args()
master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 32, 120, 0, 0))

def terminal():
    os.setsid()
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)

process = None
captured = bytearray()
reports = 0

def drain(seconds):
    global reports
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if select.select([master], [], [], .03)[0]:
            try:
                captured.extend(os.read(master, 65536))
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

try:
    process = subprocess.Popen([str(args.binary.resolve()), '--lang', 'en'], stdin=slave, stdout=slave,
                               stderr=slave, preexec_fn=terminal,
                               env=dict(os.environ, TERM='xterm-256color'))
    os.close(slave)
    slave = None
    drain(.6)
    # Focus and activate the edited document; closing must retain it in the host.
    send(b'\x1b[C')
    send(b'\r')
    send(b'x')
    if b'retained' not in captured:
        raise RuntimeError('Edited-tab close guard was not rendered: ' + captured[-500:].decode(errors='replace'))
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
    os.write(master, b'\x11')
    drain(.5)
    process.wait(timeout=3)
    if process.returncode != 0 or b'\x1b[?1049l' not in captured:
        raise RuntimeError('Workspace exit/restore failed')
    print('Workspace edited-close guard, keys, drag, resize/reflow, and terminal restore passed.')
finally:
    if process is not None and process.poll() is None:
        process.kill()
        process.wait()
    if slave is not None:
        os.close(slave)
    os.close(master)
