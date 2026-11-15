#!/usr/bin/env python3
"""Check collapse, focus handoff, pointer capture and proportional restore in real PTYs."""
import argparse
import fcntl
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import termios
import time

from smoke_focus import Screen


def check(binary, rows, ascii, lang):
    master, slave = pty.openpty()
    original = termios.tcgetattr(slave)

    def resize(width, height):
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', height, width, 0, 0))

    def session():
        os.setsid()
        fcntl.ioctl(0, termios.TIOCSCTTY, 0)

    width, height = 120, 32
    resize(width, height)
    options = ['--demo', 'workspace', '--lang', lang, '--layout', 'rows' if rows else 'columns',
               '--focus-order', 'content,tabs,tree' if rows else 'tree,tabs,content']
    proc = subprocess.Popen([binary, *options, *(['--ascii'] if ascii else [])],
                            stdin=slave, stdout=slave, stderr=slave, preexec_fn=session,
                            env=dict(os.environ, TERM='xterm-256color'))
    screen, raw = Screen(), bytearray()
    reports = 0
    left, right = ('탐색', '내용') if lang == 'ko' else ('Explorer', 'Content')
    hidden, shown = (right, left) if rows else (left, right)
    def text():
        return '\n'.join(''.join(line[:width]).replace(' ', '') for line in screen.rows[:height])
    def wait(predicate, reason):
        nonlocal reports
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if select.select([master], [], [], .02)[0]:
                data = os.read(master, 65536)
                raw.extend(data)
                screen.feed(data)
                while reports < raw.count(b'\x1b[6n'):
                    os.write(master, b'\x1b[1;1R')
                    reports += 1
            if predicate():
                return
            if proc.poll() is not None:
                break
        raise AssertionError((str(binary), rows, ascii, lang, reason, text()))
    def mouse(button, x, y, up=False):
        os.write(master, f'\x1b[<{button};{x+1};{y+1}{"m" if up else "M"}'.encode())
    def click(x, y):
        mouse(0, x, y)
        mouse(0, x, y, True)
    def focused(label):
        return '>'+label in text()

    expanded = ('v' if ascii else '↓') if rows else ('<' if ascii else '‹')
    collapsed = ('^' if ascii else '↑') if rows else ('>' if ascii else '›')
    # Find a grip on its known perpendicular center; other widgets use > and v.
    def grip(axis):
        return (width // 2, 3 + axis) if rows else (axis, 3 + (height - 5) // 2)
    def drawn(glyph, axis):
        x, y = grip(axis)
        return screen.rows[y][x] == glyph
    try:
        axis = 8 if rows else 32
        wait(lambda: drawn(expanded, axis) and focused(hidden), 'initial grip and focus')
        x, y = grip(axis)
        # A drag must resize without collapsing.
        mouse(0, x, y)
        dx, dy = (0, 2) if rows else (10, 0)
        mouse(32, x+dx, y+dy)
        mouse(0, x+dx, y+dy, True)
        new_axis = axis + dx + dy
        wait(lambda: drawn(expanded, new_axis) and hidden in text(), 'drag resizes')
        click(*grip(new_axis))
        edge = height - 6 if rows else 0
        wait(lambda: drawn(collapsed, edge) and hidden not in text() and focused(shown), 'click collapses and hands off focus')
        os.write(master, b'\t')
        wait(lambda: not focused(shown), 'tab reaches the tab bar')
        os.write(master, b'\t')
        wait(lambda: focused(shown), 'tab skips hidden child')
        # Restore by clicking even while below the two-pane minimum; grow afterwards.
        width, height = (120, 13) if rows else (35, 32)
        resize(width, height)
        edge = height - 6 if rows else 0
        wait(lambda: drawn(collapsed, edge) and (rows or screen.rows[3][width - 1] in '+╗┐'), 'narrow collapsed divider remains clickable')
        click(*grip(edge))
        wait(lambda: not drawn(collapsed, edge) and screen.rows[3 + edge if rows else 3][0] in '+╚└╔┌', 'narrow click restores compact layout')
        width, height = (120, 27) if rows else (100, 32)
        resize(width, height)
        new_axis = 8 if rows else 35
        wait(lambda: drawn(expanded, new_axis) and hidden in text(), 'ratio restored at new size')
        os.write(master, b'\x1b[18~')  # F7
        edge = height - 6 if rows else 0
        wait(lambda: drawn(collapsed, edge) and hidden not in text(), 'keyboard collapse')
        os.write(master, b'\x1b[18~')
        wait(lambda: drawn(expanded, new_axis) and hidden in text(), 'keyboard restore')
        os.write(master, b'\x11')
        assert proc.wait(timeout=5) == 0
        assert termios.tcgetattr(slave) == original
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)
        os.close(slave)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    args = parser.parse_args()
    for rows in (False, True):
        for ascii in (False, True):
            for lang in ('ko', 'en'):
                check(args.binary.resolve(), rows, ascii, lang)
                print(f'{args.binary}: rows={rows} ascii={ascii} {lang} PASS', flush=True)


if __name__ == '__main__':
    main()
