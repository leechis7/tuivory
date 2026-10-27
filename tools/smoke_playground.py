#!/usr/bin/env python3
"""POSIX PTY check: start TUIVORY, quit once, verify alternate-screen restore."""
import argparse
import fcntl
import os
import pty
import select
import struct
import subprocess
import termios
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--lang', choices=['ko', 'en'], default='ko')
    args = parser.parse_args()
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 36, 120, 0, 0))

    def controlling_terminal():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)

    process = None
    captured = bytearray()
    cursor_reports = 0

    def drain(seconds):
        nonlocal cursor_reports
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if select.select([master], [], [], .05)[0]:
                try:
                    captured.extend(os.read(master, 65536))
                    # Ratatui queries the initial cursor position. A real terminal
                    # replies to DSR; this PTY harness must emulate that response.
                    queries = captured.count(b'\x1b[6n')
                    while cursor_reports < queries:
                        os.write(master, b'\x1b[1;1R')
                        cursor_reports += 1
                except OSError:
                    break

    try:
        process = subprocess.Popen([str(args.binary.resolve()), '--lang', args.lang], stdin=slave, stdout=slave,
                                   stderr=slave, env=dict(os.environ, TERM='xterm-256color'),
                                   preexec_fn=controlling_terminal)
        os.close(slave)
        slave = None
        drain(1)
        if process.poll() is not None:
            raise RuntimeError('TUIVORY exited before input: ' + captured.decode(errors='replace')[-250:])
        os.write(master, b'\x11')  # One Ctrl+Q; keep draining output while it exits.
        drain(2)
        process.wait(timeout=3)
        if process.returncode or b'TUIVORY' not in captured or b'\x1b[?1049l' not in captured:
            raise RuntimeError('startup/exit/alternate-screen restore check failed: '
                               f'exit={process.returncode}, title={b"TUIVORY" in captured}, '
                               f'restore={bytes([27]) + b"[?1049l" in captured}, '
                               f'tail={captured[-300:]!r}')
        # tcell can emit cursor/backspace sequences between wide glyphs.
        has_korean = any('\uac00' <= char <= '\ud7a3' for char in captured.decode(errors='replace'))
        if (args.lang == 'ko' and not has_korean) or (args.lang == 'en' and (has_korean or b'Name' not in captured)):
            raise RuntimeError('expected UI language was not rendered: ' + args.lang)
        print(f'PTY {args.lang} UI, startup, one Ctrl+Q, and alternate-screen restore passed.')
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        if slave is not None:
            os.close(slave)
        os.close(master)


if __name__ == '__main__':
    main()
