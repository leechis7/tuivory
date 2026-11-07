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
    italic: bool = False

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
        codes += [str(code) for on, code in [(self.bold, 1), (self.dim, 2), (self.italic, 3), (self.underline, 4)] if on]
        return "\x1b[" + ";".join(codes) + "m"


_PLAIN_ROLES = ('body','hint','disabled','info','success','warning','error')
_ANSI_RGB = ((0,0,0),(128,0,0),(0,128,0),(128,128,0),(0,0,128),(128,0,128),(0,128,128),(192,192,192),(128,128,128),(255,0,0),(0,255,0),(255,255,0),(0,0,255),(255,0,255),(0,255,255),(255,255,255))

def color_rgb(value: str) -> tuple[int,int,int]:
    if value.startswith('#'):
        if len(value)!=7:raise ValueError('invalid RGB color')
        return tuple(int(value[i:i+2],16)for i in (1,3,5))
    n=int(value)
    if not 0<=n<=255:raise ValueError('invalid ANSI color')
    if n<16:return _ANSI_RGB[n]
    if n>=232:return (8+(n-232)*10,)*3
    n-=16;cube=(0,95,135,175,215,255)
    return cube[n//36],cube[(n//6)%6],cube[n%6]

def color_contrast(a: str,b: str) -> float:
    def luminance(color):
        def linear(n):
            v=n/255
            return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
        r,g,b=map(linear,color_rgb(color))
        return .2126*r+.7152*g+.0722*b
    x,y=luminance(a),luminance(b)
    return (max(x,y)+.05)/(min(x,y)+.05)


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


    def text_on_surface(self, role: str, surface: str = 'surface', *, focused=False) -> Style:
        text,base=self.style(role),self.style(surface)
        foreground=text.foreground
        current=color_contrast(foreground,base.background)
        if current<(2 if role=='disabled'else 4.5) and color_contrast(base.foreground,base.background)>current:
            foreground=base.foreground
        disabled=role=='disabled'
        return Style(foreground,base.background,False if disabled else text.bold,text.dim or disabled,focused and not disabled)

    def control_on_surface(self,state,surface: str='surface',*,focused=False) -> Style:
        role=state.role;focus=focused and state.focusable
        return self.text_on_surface(role,surface,focused=focus)if role in _PLAIN_ROLES else self.style(role,focused=focus)


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
    def __init__(self, width: int, height: int, palette: Palette | None = None, surface: str = "surface"):
        if width < 0 or height < 0 or width * height > 1_000_000:
            raise ValueError("invalid canvas dimensions")
        self.width, self.height = width, height
        self.palette = palette or Palette()
        self.surface_role = surface
        self.palette.style(surface)
        self.data = [[Cell(style=self.palette.style(surface)) for _ in range(width)] for _ in range(height)]
        self.cursor: tuple[int, int] | None = None
        self._cursor_width = 1

    def _erase(self, x: int, y: int) -> None:
        c = self.data[y][x]
        start = c.owner if c.continuation else x
        end = start + 1
        while end < self.width and self.data[y][end].continuation and self.data[y][end].owner == start:
            end += 1
        self.clear_cursor(Rect(start, y, end-start, 1))
        for i in range(start, end):
            self.data[y][i] = Cell(style=self.data[y][i].style)

    def write(self, x: int, y: int, text: str, role: str = "body", *, focused: bool = False,
              width: int | None = None, preserve_background: bool = False) -> None:
        actual = self.surface_role if role=='surface'else role
        style = self.palette.style(actual, focused=focused)
        if not preserve_background and role in _PLAIN_ROLES:
            style = self.palette.text_on_surface(role,self.surface_role,focused=focused)
        self.write_style(x,y,text,style,width=width)

    def write_style(self,x:int,y:int,text:str,style:Style,*,width:int|None=None) -> None:
        """Paint an exact style; callers own its background and contrast choice."""
        if not 0 <= y < self.height:return
        limit=min(self.width,x+max(0,width))if width is not None else self.width
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
            self.write(rect.x, y, " " * max(0, rect.width), role, width=rect.width, preserve_background=False)

    def panel(self, rect: Rect, title: str = "", focused: bool = False, ascii: bool = False) -> Rect:
        self.fill(rect)
        if rect.width < 2 or rect.height < 2:
            return Rect(rect.x, rect.y, 0, 0)
        a, b, c, d, horizontal, vertical = ("+", "+", "+", "+", "-", "|") if ascii else (
            ("╔", "╗", "╚", "╝", "═", "║") if focused else ("┌", "┐", "└", "┘", "─", "│"))
        role = "focus.border" if focused else "hint"
        style=self.palette.text_on_surface(role,self.surface_role)
        self.write_style(rect.x, rect.y, a + horizontal * (rect.width - 2) + b, style)
        self.write_style(rect.x, rect.y + rect.height - 1, c + horizontal * (rect.width - 2) + d, style)
        for y in range(rect.y + 1, rect.y + rect.height - 1):
            self.write_style(rect.x, y, vertical, style)
            self.write_style(rect.x + rect.width - 1, y, vertical, style)
        self.write_style(rect.x + 2, rect.y, clip(title, max(0, rect.width - 4)), style)
        return Rect(rect.x + 1, rect.y + 1, rect.width - 2, rect.height - 2)

    def set_cursor(self, x: int, y: int, glyph_width: int = 1) -> None:
        self._cursor_width = max(1, glyph_width)
        self.cursor = (x, y) if 0 <= x and x + max(1, glyph_width) <= self.width and 0 <= y < self.height else None

    def clear_cursor(self, rect: Rect | None = None) -> None:
        """Hide a cursor intersecting an opaque paint region, or hide unconditionally."""
        if rect is None or (self.cursor is not None and
                rect.y <= self.cursor[1] < rect.y + rect.height and
                rect.x < self.cursor[0] + self._cursor_width and
                self.cursor[0] < rect.x + rect.width and rect.width > 0):
            self.cursor = None

    def blit(self, source: Canvas, region: Rect, x: int, y: int) -> None:
        """Copy clipped cells/styles; incomplete glyphs become blanks. Self-copy is safe."""
        values = (region.x, region.y, region.width, region.height, x, y)
        if any(type(v) is not int or abs(v) > 10**9 for v in values) or min(region.width, region.height) < 0:
            raise ValueError("invalid blit bounds")
        left = max(0, region.x, region.x-x)
        top = max(0, region.y, region.y-y)
        right = min(source.width, region.x+region.width, region.x+self.width-x)
        bottom = min(source.height, region.y+region.height, region.y+self.height-y)
        if left >= right or top >= bottom:
            return
        cursor, cw = source.cursor, source._cursor_width
        rows = []
        for sy in range(top, bottom):
            row = []
            for sx in range(left, right):
                cell = source.data[sy][sx]
                start = cell.owner if cell.continuation else sx
                end = start+1
                while end < source.width and source.data[sy][end].continuation and source.data[sy][end].owner == start:
                    end += 1
                if start < left or end > right:
                    row.append(Cell(style=cell.style))
                else:
                    row.append(Cell(cell.text, cell.style, cell.continuation,
                                    x+start-region.x if cell.continuation else -1))
            rows.append(row)
        for sy in range(top, bottom):
            for sx in range(left, right):
                self._erase(x+sx-region.x, y+sy-region.y)
        for offset, row in enumerate(rows):
            dy = y+top+offset-region.y
            self.data[dy][x+left-region.x:x+right-region.x] = row
        if cursor is not None and left <= cursor[0] and cursor[0]+cw <= right and top <= cursor[1] < bottom:
            self.set_cursor(x+cursor[0]-region.x, y+cursor[1]-region.y, cw)

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


_FOLD = {int(k): v for k,v in json.loads(files("tuivory").joinpath("casefold.json").read_text())["mappings"].items()}

def fold(text: str) -> str:
    """Unicode17 default full case folding; leaves source normalization unchanged."""
    return "".join(_FOLD.get(ord(c),c) for c in text)
