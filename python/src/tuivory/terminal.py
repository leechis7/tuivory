"""Opt-in POSIX terminal context. The host chooses lifecycle and routes events."""
from __future__ import annotations
import os
import math
import re
import select
import shutil
import sys
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class InputEvent:
    key: str = ""
    text: str = ""
    x: int = 0
    y: int = 0
    button: int = 0


class InputDecoder:
    """Incremental UTF-8/escape parser; no terminal or OS access."""
    def __init__(self):
        self._buffer = b""
        self._paste = None
        self._rejected = False

    def feed(self, chunk: bytes) -> None:
        if not isinstance(chunk, (bytes, bytearray, memoryview)):
            raise TypeError("input requires bytes")
        self._buffer += bytes(chunk)
        if len(self._buffer) > 16 * 1024 * 1024 + 64:
            self._buffer = b""; self._paste = None; self._rejected = True

    def next(self, flush_escape: bool = False) -> InputEvent | None:
        if self._rejected:
            self._rejected = False
            return InputEvent('paste_rejected')
        event = self._parse()
        if event is None and flush_escape and self._paste is None and self._buffer.startswith(b'\x1b'):
            self._buffer = self._buffer[1:]
            return InputEvent('escape')
        return event

    def _parse(self) -> InputEvent | None:
        b = self._buffer
        if not b:
            return None
        if self._paste is not None:
            end = b.find(b'\x1b[201~')
            if end >= 0:
                if len(self._paste)+end > 16*1024*1024:
                    self._paste=None;self._buffer=b[end+6:]
                    return InputEvent('paste_rejected')
                self._paste.extend(b[:end])
                text = self._paste.decode('utf-8', 'replace')
                self._paste = None
                self._buffer = b[end + 6:]
                return InputEvent('paste', text)
            if len(self._paste) + len(b) > 16 * 1024 * 1024:
                self._paste = None
                self._buffer = b''
                return InputEvent('paste_rejected')
            # Keep an incomplete ending delimiter across reads.
            keep = min(5, len(b))
            self._paste.extend(b[:-keep] if keep else b)
            self._buffer = b[-keep:] if keep else b''
            return None
        if b.startswith(b'\x1b[200~'):
            self._buffer = b[6:]
            self._paste = bytearray()
            return self._parse()
        mouse = re.match(rb'\x1b\[<(\d+);(\d+);(\d+)([Mm])', b)
        if mouse:
            self._buffer = b[mouse.end():]
            button, x, y = map(int, mouse.groups()[:3])
            if any(v<0 or v>1000000000 for v in (button,x-1,y-1)):
                return InputEvent('unknown')
            return InputEvent('mouse_release' if mouse[4] == b'm' else 'wheel' if button & 64 else 'mouse_move' if button & 32 else 'mouse', x=x - 1, y=y - 1, button=button)
        keys = {b'\x1b[A': 'up', b'\x1b[B': 'down', b'\x1b[C': 'right', b'\x1b[D': 'left',
                b'\x1b[H': 'home', b'\x1b[F': 'end', b'\x1b[5~': 'page_up', b'\x1b[6~': 'page_down',
                b'\x1b[3~': 'delete', b'\x1b[Z': 'shift_tab', b'\x1bOP': 'f1', b'\x1bOQ': 'f2',
                b'\x1b[21~': 'f10', b'\x1b[21;2~': 'shift_f10'}
        for seq, key in keys.items():
            if b.startswith(seq):
                self._buffer = b[len(seq):]
                return InputEvent(key)
        if b[0] == 27:
            if any(seq.startswith(b) for seq in [*keys, b'\x1b[200~']) or b.startswith(b'\x1b[<') and not re.search(rb'[Mm]', b):
                return None
            csi = re.match(rb'\x1b\[[0-?]*[ -/]*[@-~]', b)
            if csi:
                self._buffer = b[csi.end():]
                return InputEvent('unknown')
            self._buffer = b[1:]
            return InputEvent('escape')
        controls = {9: 'tab', 10: 'enter', 13: 'enter', 127: 'backspace', 8: 'backspace'}
        if b[0] < 32 or b[0] == 127:
            self._buffer = b[1:]
            return InputEvent(controls.get(b[0], 'ctrl_' + chr(b[0] + 96)))
        first=b[0]
        n=1 if first<128 else 2 if 0xc2<=first<=0xdf else 3 if 0xe0<=first<=0xef else 4 if 0xf0<=first<=0xf4 else 0
        if not n:
            self._buffer=b[1:]
            return InputEvent('text','\ufffd')
        if len(b)<n:return None
        try:text=b[:n].decode('utf-8','strict')
        except UnicodeDecodeError:
            self._buffer=b[1:]
            return InputEvent('text','\ufffd')
        self._buffer=b[n:]
        return InputEvent('text',text)

class Terminal(InputDecoder):
    def __init__(self, *, mouse: bool = True, mouse_motion: bool = False):
        super().__init__()
        self.mouse = mouse
        self.mouse_motion = mouse_motion
        self._saved = None
        self._escape_at = 0.0
        self._size = (0, 0)

    @property
    def size(self) -> tuple[int, int]:
        size = shutil.get_terminal_size((80, 24))
        return size.columns, size.lines

    def __enter__(self):
        if self._saved is not None:
            raise RuntimeError("Terminal session is already active")
        self._buffer=b"";self._paste=None;self._rejected=False
        if os.name != 'posix' or not sys.stdin.isatty() or not sys.stdout.isatty():
            raise RuntimeError("interactive Terminal requires a POSIX TTY")
        import termios
        import tty
        self._saved = termios.tcgetattr(sys.stdin.fileno())
        try:
            tty.setraw(sys.stdin.fileno())
            self.write("\x1b[?1049h\x1b[?2004h" + (("\x1b[?1002h" if self.mouse_motion else "\x1b[?1000h") + "\x1b[?1006h" if self.mouse else ""))
        except BaseException:
            try:
                self.__exit__(None,None,None)
            except BaseException:
                pass
            raise
        self._size = self.size
        return self

    def __exit__(self, *_):
        if self._saved is not None:
            import termios
            try:
                self.write("\x1b[0m\x1b[?1000l\x1b[?1002l\x1b[?1006l\x1b[?2004l\x1b[?25h\x1b[?1049l")
            finally:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._saved)
                self._saved = None

    def write(self, data: str) -> None:
        sys.stdout.write(data)
        sys.stdout.flush()

    def read(self, timeout: float = 0.1) -> InputEvent | None:
        if not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or not 0<=timeout<=3600:
            raise ValueError("invalid terminal timeout")
        if self._saved is None:return InputEvent("eof")
        size = self.size
        if size != self._size:
            self._size = size
            return InputEvent('resize', x=size[0], y=size[1])
        event = self.next()
        if event:
            self._escape_at = 0
            return event
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            incoming = os.read(sys.stdin.fileno(), 8192)
            if not incoming:
                return InputEvent('eof')
            if not self._buffer:
                self._escape_at = time.monotonic()
            self.feed(incoming)
            return self.next()
        if self._paste is None and self._buffer.startswith(b'\x1b') and time.monotonic() - self._escape_at >= 0.1:
            self._buffer = self._buffer[1:]
            return InputEvent('escape')
        return None
