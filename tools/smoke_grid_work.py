#!/usr/bin/env python3
"""Exercise host-approved grid editing, paste/find/columns/state/details in a PTY."""
import argparse
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
from smoke_focus import Screen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--demo', default='catalog', choices=['catalog'])
    parser.add_argument('--lang', choices=['ko', 'en'], default='en')
    parser.add_argument('--theme', choices=['dark', 'light', 'blackwhite'], default='dark')
    parser.add_argument('--colors', choices=['8', '16', '256', 'truecolor'], default='256')
    parser.add_argument('--ascii', action='store_true')
    parser.add_argument('--cursor',action='store_true',help='verify real-cursor integration and no shape/blink override')
    args = parser.parse_args()
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 36, 120, 0, 0))

    def terminal():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)

    environment = dict(os.environ, TERM='xterm-256color')
    environment.pop('NO_COLOR', None)
    process = subprocess.Popen([str(args.binary.resolve()), '--demo', 'catalog', '--mode', 'grid',
                                '--grid-sample', '--grid-preset', 'data', '--lang', args.lang,
                                '--theme', args.theme, '--colors', args.colors] + (['--ascii'] if args.ascii else []),
                               stdin=slave, stdout=slave, stderr=slave, preexec_fn=terminal, env=environment)
    os.close(slave)
    screen, captured, reports = Screen(), bytearray(), 0

    def drain(seconds=.15):
        nonlocal reports
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
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

    def visible():
        return '\n'.join(''.join(row) for row in screen.rows)

    def send(data):
        os.write(master, data)
        drain()

    def expect(text):
        assert text in visible(), f'{text!r} missing:\n{visible()}'

    try:
        drain(.8)
        before=len(captured)
        send(b'\r'); expect('edit_begin: row-2')
        if args.cursor:
            assert b'\x1b[?25h' in captured[before:], 'real cursor was never shown'
            before=len(captured);send(b'\x0e');assert b'\x1b[?25l' in captured[before:], 'NULL cursor not hidden'
            before=len(captured);send(b'\x0e');assert b'\x1b[?25h' in captured[before:], 'NULL reset cursor not restored'
            before=len(captured);send(b'\x1b');assert b'\x1b[?25l' in captured[before:], 'closed editor cursor not hidden'
            send(b'\r');expect('edit_begin: row-2')
        send(b'\x01'); send(('Updated' if args.lang == 'en' else '수정값').encode()); send(b'\r')
        expect('edit_submit: row-2')
        send(b'reject'); send(b'\r')
        expect('Rejected' if args.lang == 'en' else '거 절')
        send(b'\x01'); send(b'Retried'); send(b'\t'); expect('edit_submit: row-2')
        send(b'\x1b'); expect('edit_cancel: row-2')
        send(b'\x06'); send(b'\x01'); send(b'user3'); send(b'\r'); expect('find: row-3')
        send(b'\x1b[24~'); expect('details: row-3'); expect('user3@example.test')
        send(b'\x1b')
        send(b'\x1b[200~new@x\t123\nnew@y\t456\x1b[201~'); expect('paste_request:')
        expect('new@x')
        send(b'\x13'); expect('view_save:')
        send(b'\x1bh'); expect('columns:')
        send(b'\x1bu'); send(b'\x12'); expect('view_restore:')
        send(b'\x1bp'); expect('columns:')
        send(b'\x1b[1;6D'); expect('columns:')
        for data in (b'\x1b[12~', b'\x1b[13~'):
            send(data)
        for height, width in ((16, 40), (8, 8), (36, 120)):
            fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', height, width, 0, 0))
            os.killpg(process.pid, signal.SIGWINCH)
            drain()
        send(b'\x11')
        process.wait(timeout=4)
        assert process.returncode == 0 and b'\x1b[?1049l' in captured
        korean = any('\uac00' <= c <= '\ud7a3' for c in captured.decode(errors='replace'))
        assert korean == (args.lang == 'ko')
        if args.cursor:
            assert not re.search(rb'\x1b\[[0-9;]* q',captured),'cursor shape escape leaked'
            assert not re.search(rb'\x1b\[\?12[hl]',captured),'blink mode override leaked'
        print(f'grid workspace PTY {args.lang}/{args.theme}/{args.colors}/ascii={args.ascii}: passed')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)


if __name__ == '__main__':
    main()
