"""Terminal-cell drawing independent of any other Tuivory language or framework."""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files

import regex
from wcwidth import wcswidth


def graphemes(text: str) -> list[str]:
    return regex.findall(r"\X", text)


def clean(text: str) -> str:
    return "".join(" " if ord(c) < 32 or 127 <= ord(c) < 160 else c for c in text)


def cells(text: str) -> int:
    return sum(max(0, wcswidth(g)) for g in graphemes(clean(text)))


def clip(text: str, width: int, ellipsis: bool = False) -> str:
    text = clean(text)
    if width <= 0:
        return ""
    if cells(text) <= width:
        return text
    limit = width - int(ellipsis)
    result, used = [], 0
    for g in graphemes(text):
        n = max(0, wcswidth(g))
        if used + n > limit:
            break
        result.append(g)
        used += n
    return "".join(result) + ("~" if ellipsis else "")


@dataclass(frozen=True)
class Style:
    foreground: str
    background: str
    bold: bool = False
    dim: bool = False
    underline: bool = False

    def sgr(self) -> str:
        def color(value: str, background: bool) -> str:
            base = 48 if background else 38
            if value.startswith("#"):
                rgb = [int(value[i:i + 2], 16) for i in (1, 3, 5)]
                return f"{base};2;" + ";".join(map(str, rgb))
            n = int(value)
            if n < 8:
                return str((40 if background else 30) + n)
            if n < 16:
                return str((100 if background else 90) + n - 8)
            return f"{base};5;{n}"
        codes = ["0", color(self.foreground, False), color(self.background, True)]
        codes += [str(code) for on, code in [(self.bold, 1), (self.dim, 2), (self.underline, 4)] if on]
        return "\x1b[" + ";".join(codes) + "m"


class Palette:
    def __init__(self, theme: str = "dark", colors: str = "256"):
        document = json.loads(files("tuivory").joinpath("tokens.json").read_text())
        self.theme, self.colors = theme, str(colors)
        key = f"{theme}-{colors}"
        if key not in document["palettes"]:
            raise ValueError(f"unknown palette: {key}")
        self.roles = document["palettes"][key]

    def style(self, role: str = "body", *, focused: bool = False) -> Style:
        if role not in self.roles:
            raise ValueError(f"unknown role: {role}")
        token = self.roles[role]
        return Style(token["foreground"], token["background"],
                     token["fontWeight"] == "bold", role == "disabled", focused)


@dataclass(frozen=True)
class Rect:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


@dataclass
class Cell:
    text: str = " "
    style: Style | None = None
    continuation: bool = False
    owner: int = -1


class Canvas:
    """Full-frame cell buffer. Overlay writes repair both edges of wide glyphs."""
    def __init__(self, width: int, height: int, palette: Palette | None = None):
        if width < 0 or height < 0 or width * height > 1_000_000:
            raise ValueError("invalid canvas dimensions")
        self.width, self.height = width, height
        self.palette = palette or Palette()
        self.data = [[Cell(style=self.palette.style("surface")) for _ in range(width)] for _ in range(height)]
        self.cursor: tuple[int, int] | None = None

    def _erase(self, x: int, y: int) -> None:
        c = self.data[y][x]
        start = c.owner if c.continuation else x
        end = start + 1
        while end < self.width and self.data[y][end].continuation and self.data[y][end].owner == start:
            end += 1
        for i in range(start, end):
            self.data[y][i] = Cell(style=self.data[y][i].style)

    def write(self, x: int, y: int, text: str, role: str = "body", *, focused: bool = False,
              width: int | None = None, preserve_background: bool = False) -> None:
        if not 0 <= y < self.height:
            return
        limit = min(self.width, x + max(0, width)) if width is not None else self.width
        style = self.palette.style(role, focused=focused)
        if not preserve_background and role in ("body", "hint", "info", "success", "warning", "error", "header"):
            style = Style(style.foreground, self.palette.style("surface").background,
                          style.bold, style.dim, style.underline)
        for g in graphemes(clean(text)):
            n = max(0, wcswidth(g))
            if n == 0:
                continue
            if x >= limit:
                break
            if x < 0 or x + n > limit:
                for i in range(max(0, x), min(limit, x + n)):
                    self._erase(i, y)
                    self.data[y][i] = Cell(style=style)
                x += n
                continue
            for i in range(x, x + n):
                self._erase(i, y)
            self.data[y][x] = Cell(g, style)
            for i in range(x + 1, x + n):
                self.data[y][i] = Cell("", style, True, x)
            x += n

    def fill(self, rect: Rect, role: str = "surface") -> None:
        for y in range(max(0, rect.y), min(self.height, rect.y + rect.height)):
            self.write(rect.x, y, " " * max(0, rect.width), role, width=rect.width, preserve_background=True)

    def panel(self, rect: Rect, title: str = "", focused: bool = False, ascii: bool = False) -> Rect:
        self.fill(rect)
        if rect.width < 2 or rect.height < 2:
            return Rect(rect.x, rect.y, 0, 0)
        a, b, c, d, horizontal, vertical = ("+", "+", "+", "+", "-", "|") if ascii else (
            ("╔", "╗", "╚", "╝", "═", "║") if focused else ("┌", "┐", "└", "┘", "─", "│"))
        role = "focus.border" if focused else "hint"
        self.write(rect.x, rect.y, a + horizontal * (rect.width - 2) + b, role)
        self.write(rect.x, rect.y + rect.height - 1, c + horizontal * (rect.width - 2) + d, role)
        for y in range(rect.y + 1, rect.y + rect.height - 1):
            self.write(rect.x, y, vertical, role)
            self.write(rect.x + rect.width - 1, y, vertical, role)
        self.write(rect.x + 2, rect.y, clip(title, max(0, rect.width - 4)), role)
        return Rect(rect.x + 1, rect.y + 1, rect.width - 2, rect.height - 2)

    def set_cursor(self, x: int, y: int, glyph_width: int = 1) -> None:
        self.cursor = (x, y) if 0 <= x and x + max(1, glyph_width) <= self.width and 0 <= y < self.height else None

    def lines(self) -> list[str]:
        return ["".join(c.text for c in row) for row in self.data]

    def ansi(self, *, origin_x: int = 0, origin_y: int = 0) -> str:
        out = ["\x1b[?25l"]
        for y, row in enumerate(self.data):
            out.append(f"\x1b[{origin_y + y + 1};{origin_x + 1}H")
            previous = None
            for c in row:
                if c.continuation:
                    continue
                if c.style != previous:
                    out.append(c.style.sgr())
                    previous = c.style
                out.append(c.text)
        out.append("\x1b[0m")
        if self.cursor is not None:
            x, y = self.cursor
            out.append(f"\x1b[{origin_y + y + 1};{origin_x + x + 1}H\x1b[?25h")
        return "".join(out)
