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
    args = parser.parse_args()
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 36, 120, 0, 0))

    def controlling_terminal():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)

    process = None
    captured = bytearray()

    def drain(seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if select.select([master], [], [], .05)[0]:
                try:
                    captured.extend(os.read(master, 65536))
                except OSError:
                    break

    try:
        process = subprocess.Popen([str(args.binary.resolve())], stdin=slave, stdout=slave,
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
            raise RuntimeError('startup/exit/alternate-screen restore check failed')
        print('PTY startup, one Ctrl+Q, and alternate-screen restore passed.')
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        if slave is not None:
            os.close(slave)
        os.close(master)


if __name__ == '__main__':
    main()
