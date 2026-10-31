#!/usr/bin/env python3
"""Exercise public control/container examples through real terminal I/O."""
import argparse
import fcntl
import os
from pathlib import Path
import pty
import select
import signal
import struct
import subprocess
import termios
import time
from smoke_focus import Screen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path)
parser.add_argument('--lang', choices=['ko', 'en'], default='en')
parser.add_argument('--ascii', action='store_true')
args = parser.parse_args()
master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 32, 120, 0, 0))
def terminal():
    os.setsid()
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)
process = subprocess.Popen([str(args.binary.resolve()), '--lang', args.lang] + (['--ascii'] if args.ascii else []), stdin=slave, stdout=slave, stderr=slave, preexec_fn=terminal, env=dict(os.environ, TERM='xterm-256color'))
os.close(slave)
screen = Screen()
captured = bytearray()
reports = 0
def drain(seconds=.2):
    global reports
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if select.select([master], [], [], .02)[0]:
            try:
                data = os.read(master, 65536)
            except OSError:
                return
            captured.extend(data)
            screen.feed(data)
            while reports < captured.count(b'\x1b[6n'):
                os.write(master, b'\x1b[1;1R')
                reports += 1
    for secret in (b'example-secret', b'never-render-this', b'hidden-value', b'MODAL_HIDDEN'):
        assert secret not in captured, 'Secret appeared in terminal output'
def send(data):
    os.write(master, data)
    drain()
    assert process.poll() is None, captured[-1000:]
def visible():
    return ''.join(''.join(row) for row in screen.rows)
try:
    drain(.8)
    send(b'\t')  # Password field.
    send(b'\x1b[200~hidden-value\x1b[201~')
    send(b'\x01\x03')  # Secret select/copy emits no plaintext.
    send(b'\t \t\r')
    assert 'activate' in visible(), visible()
    send(b'\t')  # Leave the form scope for the editor.
    send(b'\x1b[200~CONTROL_EDIT\x1b[201~')
    assert 'CONTROL_EDIT' in visible(), visible()
    send(b'\x1a')
    assert 'CONTROL_EDIT' not in visible(), visible()
    send(b'\x19')
    assert 'CONTROL_EDIT' in visible(), visible()
    send(b'\x01\x03')
    assert 'copy' in visible(), visible()
    send(b'\t\x1b[200~READONLY_BAD\x1b[201~')
    assert 'READONLY_BAD' not in visible(), visible()
    send(b'\x1b[14~')  # F4 opens a modal with a secret input.
    send(b'\x1b[200~MODAL_HIDDEN\x1b[201~')
    send(b'\t\r')
    assert 'activate' in visible(), visible()
    send(b'\x1b[12~\x1b[13~')  # Theme/profile changes with the modal open.
    send(b'\x1b')
    assert 'CONTROL_EDIT' in visible(), visible()
    for height, width in ((16, 50), (32, 120)):
        fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', height, width, 0, 0))
        os.killpg(process.pid, signal.SIGWINCH)
        drain()
    assert 'CONTROL_EDIT' in visible(), visible()
    # Captured editor selection, including a pointer outside its pane.
    send(b'\x1b[<0;55;5M\x1b[<32;80;6M\x1b[<0;115;20m')
    os.write(master, b'\x11')
    drain()
    process.wait(timeout=3)
    assert process.returncode == 0 and b'\x1b[?1049l' in captured
    if args.lang == 'en':
        assert not any('\uac00' <= c <= '\ud7a3' for c in captured.decode(errors='replace'))
    print(f'Controls PTY {args.lang}: secret masking, scope traversal, paste, undo/redo, read-only, modal isolation, resize, captured selection and terminal restore passed')
finally:
    if process.poll() is None:
        process.kill()
        process.wait()
    os.close(master)
