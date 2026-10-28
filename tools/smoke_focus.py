#!/usr/bin/env python3
"""Exercise public focus/popup hosts in a PTY and inspect the rendered state row."""
import argparse
import codecs
import fcntl
import os
from pathlib import Path
import pty
import re
import select
import signal
import struct
import subprocess
import termios
import time
import unicodedata


class Screen:
    """Small VT cursor/erase reader for these hosts' ASCII diagnostic row."""
    def __init__(self):
        self.rows = [[' '] * 160 for _ in range(60)]
        self.x = self.y = 0
        self.pending = ''
        self.decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')

    def feed(self, data):
        self.pending += self.decoder.decode(data)
        while self.pending:
            if self.pending.startswith('\x1b['):
                match = re.match(r'\x1b\[([0-?]*)([ -/]*)([@-~])', self.pending)
                if not match:
                    return
                params, _, command = match.groups()
                self.pending = self.pending[match.end():]
                if params.startswith(('?', '>', '<', '=')):
                    continue
                values = [int(n) if n else 0 for n in params.split(';')]
                first = values[0] or 1
                if command in 'Hf':
                    self.y = first - 1
                    self.x = (values[1] or 1) - 1 if len(values) > 1 else 0
                elif command == 'G':
                    self.x = first - 1
                elif command == 'd':
                    self.y = first - 1
                elif command in 'ABCD':
                    self.x += first * ((command == 'C') - (command == 'D'))
                    self.y += first * ((command == 'B') - (command == 'A'))
                elif command == 'J' and values[0] in (2, 3):
                    self.rows = [[' '] * 160 for _ in range(60)]
                elif command == 'K' and 0 <= self.y < 60:
                    begin, end = (self.x, 160) if values[0] == 0 else (0, self.x + 1)
                    if values[0] == 2:
                        begin, end = 0, 160
                    for x in range(max(0, begin), min(160, end)):
                        self.rows[self.y][x] = ' '
                continue
            if self.pending[0] == '\x1b':
                if len(self.pending) < 2:
                    return
                size = 3 if self.pending[1] in '()' else 2
                if len(self.pending) < size:
                    return
                self.pending = self.pending[size:]
                continue
            char, self.pending = self.pending[0], self.pending[1:]
            if char == '\r':
                self.x = 0
            elif char == '\n':
                self.y += 1
            elif char == '\b':
                self.x = max(0, self.x - 1)
            elif char >= ' ' and not unicodedata.combining(char):
                width = 2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1
                if 0 <= self.y < 60 and 0 <= self.x < 160:
                    self.rows[self.y][self.x] = char
                    if width==2 and self.x+1<160:
                        self.rows[self.y][self.x+1] = " "
                self.x += width

    def status(self):
        return ''.join(self.rows[1]).rstrip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--lang', choices=['ko', 'en'], default='en')
    args = parser.parse_args()
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 36, 120, 0, 0))

    def terminal():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)

    process = subprocess.Popen([str(args.binary.resolve()), '--lang', args.lang], stdin=slave,
                               stdout=slave, stderr=slave, preexec_fn=terminal,
                               env=dict(os.environ, TERM='xterm-256color'))
    os.close(slave)
    screen, captured, reports = Screen(), bytearray(), 0

    def drain(seconds):
        nonlocal reports
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if select.select([master], [], [], .03)[0]:
                try:
                    data = os.read(master, 65536)
                except OSError:
                    return
                captured.extend(data)
                screen.feed(data)
                while reports < captured.count(b'\x1b[6n'):
                    os.write(master, b'\x1b[1;1R')
                    reports += 1

    def step(key, scope, focus, depth):
        if key:
            os.write(master, key)
        expected = f'Scope={scope} Focus={focus} Depth={depth}'
        drain(.2)
        deadline = time.monotonic() + 3
        while expected not in screen.status() and time.monotonic() < deadline:
            drain(.1)
        if process.poll() is not None or expected not in screen.status():
            raise RuntimeError(f'Expected {expected!r}, got {screen.status()!r}; tail={captured[-150:]!r}')

    try:
        step(None, 'root', 'open', 0)
        step(b'\t', 'root', 'read', 0)
        step(b'\t', 'root', 'busy', 0)
        step(b'\r', 'root', 'busy', 0)
        step(b'\t', 'root', 'tail', 0)
        for focus in ('busy', 'read', 'open'):
            step(b'\x1b[Z', 'root', focus, 0)
        step(b'\r', 'outer', 'child', 1)
        step(b'\t', 'outer', 'invalid', 1)
        step(b'\t', 'outer', 'close', 1)
        step(b'\x1b[Z', 'outer', 'invalid', 1)
        step(b'\x1b[Z', 'outer', 'child', 1)
        step(b'\r', 'inner', 'close', 2)
        step(b'\x1b[<0;5;6M\x1b[<0;5;6m', 'inner', 'close', 2)
        step(b'\t', 'inner', 'read', 2)
        step(b'\x1b', 'outer', 'child', 1)
        for key in (b'\x1b[12~', b'\x1b[13~', b'\x1b[14~'):
            step(key, 'outer', 'child', 1)
        for height, width in ((16, 40), (36, 120)):
            fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', height, width, 0, 0))
            os.killpg(process.pid, signal.SIGWINCH)
            step(None, 'outer', 'child', 1)
        step(b'\x1b', 'root', 'open', 0)
        os.write(master, b'\x11')
        drain(.5)
        process.wait(timeout=3)
        korean = any('\uac00' <= c <= '\ud7a3' for c in captured.decode(errors='replace'))
        if process.returncode or b'\x1b[?1049l' not in captured or korean != (args.lang == 'ko'):
            raise RuntimeError('Language/exit/terminal restore failed')
        print(f'Focus PTY {args.lang}: disabled skip, busy guard, nested scopes, pointer blocking, restoration, theme/profile/ASCII and resize passed.')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)


if __name__ == '__main__':
    main()
