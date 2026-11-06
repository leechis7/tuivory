"""Configured cell layouts and scoped routing; hosts supply actual child controls."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable
from .drawing import Canvas, Rect
from .layout import NamedRect, inset_rect

@dataclass
class Track:
    min: int = 0
    max: int = 0
    fixed: int = 0
    weight: int = 0

@dataclass
class LayoutItem:
    id: str
    track: Track = field(default_factory=Track)
    row: int = 0
    column: int = 0
    row_span: int = 0
    column_span: int = 0
    hidden: bool = False
    disabled: bool = False
    drawer: str = ''
    modal: bool = False
    centered: bool = False
    area: Rect = field(default_factory=Rect)

@dataclass
class ContainerOptions:
    kind: str = 'row'
    gap: int = 0
    padding: int = 0
    rows: list[Track] = field(default_factory=list)
    columns: list[Track] = field(default_factory=list)
    virtual_width: int = 0
    virtual_height: int = 0

def _number(value, limit=1000000):
    if type(value) is not int or not 0 <= value <= limit:
        raise ValueError('invalid container constraints')

def _track(t):
    for v in (t.min, t.max, t.fixed, t.weight):
        _number(v)
    if t.max and (t.max < t.min or t.fixed > t.max):
        raise ValueError('invalid track maximum')

def _allocate(tracks, total, gap):
    if not tracks:
        return ([], 0)
    tracks = deepcopy(tracks)
    for t in tracks:
        if not any((t.min, t.max, t.fixed, t.weight)):
            t.weight = 1
    gap = min(gap, total // len(tracks))
    available = total - gap * (len(tracks) - 1)
    if sum((max(t.min, t.fixed) for t in tracks)) > available:
        gap = 0
        available = total
    sizes = []
    for t in tracks:
        size = min(available, max(t.min, t.fixed))
        sizes.append(size)
        available -= size
    while available:
        weight = sum((t.weight for i, t in enumerate(tracks) if not t.fixed and t.weight and (not t.max or sizes[i] < t.max)))
        if not weight:
            break
        budget = available
        for i, t in enumerate(tracks):
            if t.fixed or not t.weight or (t.max and sizes[i] >= t.max):
                continue
            add = min(available, max(1, budget * t.weight // weight))
            if t.max:
                add = min(add, t.max - sizes[i])
            sizes[i] += add
            available -= add
    return (sizes, gap)

def compute_container(bounds: Rect, items: list[LayoutItem], options: ContainerOptions) -> list[NamedRect]:
    for v in (bounds.x, bounds.y, bounds.width, bounds.height, options.virtual_width, options.virtual_height):
        _number(v)
    for v in (options.gap, options.padding):
        _number(v, 1024)
    if options.kind not in ('row', 'column', 'grid', 'layers') or max(len(items), len(options.rows), len(options.columns)) > 1024:
        raise ValueError('invalid container kind/count')
    seen = set()
    for t in [*options.rows, *options.columns]:
        _track(t)
    for i in items:
        if not isinstance(i.id, str) or not i.id or i.id in seen:
            raise ValueError('invalid container ID')
        seen.add(i.id)
        _track(i.track)
        for v in (i.row, i.column, i.row_span, i.column_span, i.area.x, i.area.y, i.area.width, i.area.height):
            _number(v)
        if i.drawer and (options.kind != 'layers' or i.centered or i.drawer not in ('left', 'right')):
            raise ValueError('invalid drawer')
    inner = inset_rect(bounds, options.padding)
    visible = [i for i in items if not i.hidden]
    out = []
    if options.kind in ('row', 'column'):
        horizontal = options.kind == 'row'
        total = inner.width if horizontal else inner.height
        sizes, gap = _allocate([i.track for i in visible], total, options.gap)
        at = 0
        for i, size in zip(visible, sizes):
            at = min(at, total)
            r = Rect(inner.x + at, inner.y, size, inner.height) if horizontal else Rect(inner.x, inner.y + at, inner.width, size)
            out.append(NamedRect(i.id, r))
            at += size + gap
    elif options.kind == 'grid':
        widths, gx = _allocate(options.columns, inner.width, options.gap)
        heights, gy = _allocate(options.rows, inner.height, options.gap)
        for i in visible:
            rs, cs = (max(1, i.row_span), max(1, i.column_span))
            if i.row + rs > len(heights) or i.column + cs > len(widths):
                raise ValueError('invalid grid span')
            x = sum(widths[:i.column]) + gx * i.column
            y = sum(heights[:i.row]) + gy * i.row
            w = sum(widths[i.column:i.column + cs]) + gx * (cs - 1)
            h = sum(heights[i.row:i.row + rs]) + gy * (rs - 1)
            out.append(NamedRect(i.id, Rect(inner.x + min(x, inner.width), inner.y + min(y, inner.height), min(w, max(0, inner.width - x)), min(h, max(0, inner.height - y)))))
    else:
        for i in visible:
            ax = min(i.area.x, inner.width)
            ay = min(i.area.y, inner.height)
            w = inner.width - ax
            h = inner.height - ay
            if i.area.width:
                w = min(w, i.area.width)
            if i.area.height:
                h = min(h, i.area.height)
            x = inner.x + ax
            y = inner.y + ay
            if i.centered:
                x = inner.x + (inner.width - w) // 2
                y = inner.y + (inner.height - h) // 2
            if i.drawer:
                w = min(inner.width, i.area.width or inner.width)
                x = inner.x + (inner.width - w if i.drawer == 'right' else 0)
            out.append(NamedRect(i.id, Rect(x, y, w, h)))
    return out

class ContainerState:

    def __init__(self):
        self.focused = ''
        self.captured = ''
        self._modal = ''
        self._restore = {}

    def eligible(self, items):
        start = next((i for i in range(len(items) - 1, -1, -1) if items[i].modal and (not items[i].hidden)), 0)
        return [i.id for i in items[start:] if not i.hidden and (not i.disabled)]

    def reconcile(self, items):
        ids = self.eligible(items)
        modal = next((i.id for i in reversed(items) if i.modal and (not i.hidden)), '')
        if modal != self._modal:
            old_visible = any((i.id == self._modal and i.modal and (not i.hidden) for i in items))
            if self._modal and (not old_visible):
                previous = self._restore.pop(self._modal, '')
                for _ in range(len(self._restore) + 1):
                    if previous in ids:
                        self.focused = previous
                        break
                    if previous not in self._restore:
                        break
                    previous = self._restore.pop(previous)
            if modal:
                self._restore.setdefault(modal, self.focused)
            self._modal = modal
        if self.focused not in ids:
            self.focused = next(iter(ids), '')
        if self.captured not in ids:
            self.captured = ''

    def move_focus(self, items, previous=False):
        self.reconcile(items)
        ids = self.eligible(items)
        if ids:
            self.focused = ids[(ids.index(self.focused) + (-1 if previous else 1)) % len(ids)]
        return self.focused

    def hit(self, items, rects, x, y):
        ids = self.eligible(items)
        return next((r.id for r in reversed(rects) if r.id in ids and r.rect.contains(x, y)), '')

    def pointer(self, items, rects, x, y, press=False, release=False):
        self.reconcile(items)
        id = self.captured or self.hit(items, rects, x, y)
        if press and id:
            self.focused = id
            self.captured = id
        if release:
            self.captured = ''
        return id

class Container:
    """One configured local layout; callback coordinates start at each child's (0,0)."""

    def __init__(self, items: list[LayoutItem], options: ContainerOptions | None=None):
        self.state = ContainerState()
        self.scroll_x = 0
        self.scroll_y = 0
        self._rects = []
        self._bounds = Rect()
        self._scroll = (0, 0)
        self.set_items(items, options or ContainerOptions())

    @property
    def items(self):
        return deepcopy(self._items)

    @property
    def options(self):
        return deepcopy(self._options)

    def set_items(self, items, options=None):
        candidate = deepcopy(items)
        o = deepcopy(options if options is not None else self._options)
        compute_container(Rect(0, 0, 1, 1), candidate, o)
        self._items, self._options = (candidate, o)
        self._rects = []
        self._bounds = Rect()
        self.state.reconcile(candidate)
        self.state.captured = ''

    def draw(self, canvas: Canvas, bounds: Rect, painter: Callable[[str, Canvas, bool], None]):
        o = self._options
        for v in (bounds.x, bounds.y, bounds.width, bounds.height):
            _number(v)
        vw = max(bounds.width, o.virtual_width)
        vh = max(bounds.height, o.virtual_height)
        if vw * vh > 1000000:
            raise ValueError('container virtual area exceeds limit')
        for v in (self.scroll_x, self.scroll_y):
            _number(v)
        sx = min(self.scroll_x, max(0, vw - bounds.width))
        sy = min(self.scroll_y, max(0, vh - bounds.height))
        rects = compute_container(Rect(0, 0, vw, vh), self._items, o)
        virtual = Canvas(vw, vh, canvas.palette)
        self.state.reconcile(self._items)
        for named in rects:
            r = named.rect
            if not r.width or not r.height:
                continue
            child = Canvas(r.width, r.height, canvas.palette)
            child.blit(virtual, r, 0, 0)
            child.clear_cursor()
            focused = named.id == self.state.focused
            painter(named.id, child, focused)
            if not focused:
                child.clear_cursor()
            virtual.blit(child, Rect(0, 0, r.width, r.height), r.x, r.y)
        canvas.blit(virtual, Rect(sx, sy, bounds.width, bounds.height), bounds.x, bounds.y)
        self.scroll_x, self.scroll_y = (sx, sy)
        self._scroll = (sx, sy)
        self._bounds = bounds
        self._rects = rects
        return deepcopy(rects)

    def pointer(self, x, y, press=False, release=False):
        if not self._bounds.contains(x, y) and (not self.state.captured):
            return ''
        return self.state.pointer(self._items, self._rects, x - self._bounds.x + self._scroll[0], y - self._bounds.y + self._scroll[1], press, release)
