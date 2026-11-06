"""Host-controlled focus, menus, geometry, feedback and drag requests."""
from __future__ import annotations
from dataclasses import dataclass, field
from .drawing import Canvas, Rect, cells, clip, clean, graphemes
from .models import ControlState, Event, Item, List, unique


@dataclass
class FocusTarget:
    id: str
    state: ControlState = field(default_factory=ControlState)
    hidden: bool = False


class Focus:
    def __init__(self, id: str, targets: list[FocusTarget]):
        self.scopes: list[dict] = []
        self.open(id, targets)

    @property
    def focused(self) -> str:
        return self.scopes[-1]["focused"]

    def _eligible(self) -> list[str]:
        scope = self.scopes[-1]
        ids = [t.id for t in scope["targets"] if not t.hidden and t.state.focusable]
        if scope["focused"] not in ids:
            scope["focused"] = ids[0] if ids else ""
        return ids

    def open(self, id: str, targets: list[FocusTarget], *, focused: str = "", modal: bool = True) -> None:
        unique(targets)
        if not id or any(s["id"] == id for s in self.scopes):
            raise ValueError("duplicate/empty focus scope")
        self.scopes.append(dict(id=id, targets=list(targets), focused=focused, modal=modal))
        self._eligible()

    def close(self, id: str) -> Event:
        if len(self.scopes) <= 1 or self.scopes[-1]["id"] != id:
            raise ValueError("only top popup can close")
        self.scopes.pop()
        self._eligible()
        return Event("focus", self.focused)

    def focus(self, id: str) -> bool:
        if id not in self._eligible():
            return False
        self.scopes[-1]["focused"] = id
        return True

    def move(self, previous: bool = False) -> str:
        ids = self._eligible()
        if ids:
            self.scopes[-1]["focused"] = ids[(ids.index(self.focused) + (-1 if previous else 1)) % len(ids)]
        return self.focused

    def blocked(self, scope: str) -> bool:
        at = next((i for i, s in enumerate(self.scopes) if s["id"] == scope), -1)
        return at < 0 or any(s["modal"] for s in self.scopes[at + 1:])


class Menu:
    def __init__(self, items: list[Item]):
        unique(items)
        self.items = list(items)
        by_id = {i.id: i for i in items}
        for item in items:
            seen = {item.id}
            parent = item.parent
            while parent:
                if parent not in by_id or parent in seen:
                    raise ValueError("invalid menu parent/cycle")
                seen.add(parent)
                parent = by_id[parent].parent
        self.path: list[str] = []
        self.opened = False
        self.return_id = ""
        self.level = List([])

    def _level(self) -> None:
        parent = self.path[-1] if self.path else ""
        old = self.level.focused
        self.level = List([i for i in self.items if i.parent == parent])
        if any(i.id == old and not i.disabled and not i.separator for i in self.level.items):
            self.level.focused = old

    def open(self, id: str = "", return_id: str = "") -> Event:
        item = next((i for i in self.items if i.id == id), None)
        if id and (item is None or item.disabled or item.separator):
            return Event()
        self.path = [id] if id else []
        self.return_id, self.opened = return_id, True
        self._level()
        return Event("open", id)

    def handle(self, action: str, height: int = 10, text: str = "") -> Event:
        if not self.opened:
            return Event()
        if action in ("cancel", "close"):
            self.opened = False
            return Event("close", self.return_id)
        if action in ("back", "left"):
            if self.path:
                self.path.pop()
                self._level()
                return Event("back", self.path[-1] if self.path else "")
            return self.handle("close")
        if action in ("activate", "right"):
            item = next((i for i in self.level.items if i.id == self.level.focused), None)
            if item is None or item.disabled or item.separator:
                return Event()
            if any(i.parent == item.id for i in self.items):
                self.path.append(item.id)
                self._level()
                return Event("open", item.id)
            if action == "activate":
                self.opened = False
                return Event("activate", item.id, data={"return_id": self.return_id})
            return Event()
        return self.level.handle(action, height, text)

    def click(self, x: int, y: int, height: int = 10) -> Event:
        if not self.opened:
            return Event()
        event = self.level.click(x, y, height)
        return self.handle("activate", height) if event.kind else Event()

    def draw(self, canvas: Canvas, rect: Rect, *, focused: bool = True, ascii: bool = False) -> None:
        if self.opened:
            self.level.draw(canvas, rect, focused=False, ascii=ascii)


@dataclass(frozen=True)
class SplitLayout:
    first: int
    divider: int
    second: int
    compact: bool


class Split:
    def __init__(self, first_min: int = 1, second_min: int = 1, preferred: int = 0):
        self.first_min, self.second_min = max(1, first_min), max(1, second_min)
        self.preferred = max(0, preferred)

    def layout(self, total: int) -> SplitLayout:
        if total < 0:
            raise ValueError('negative split size')
        if total < self.first_min + self.second_min + 1:
            return SplitLayout(0, 0, total, True)
        first = max(self.first_min, min(total - 1 - self.second_min, self.preferred or (total - 1) // 2))
        return SplitLayout(first, 1, total - first - 1, False)

    def resize(self, total: int, position: int) -> bool:
        old = self.layout(total)
        if old.compact:
            return False
        self.preferred = max(self.first_min, min(total - 1 - self.second_min, position))
        return self.preferred != old.first


def split(rect: Rect, preferred: int, first_min: int = 0, second_min: int = 0, *, vertical: bool = False) -> tuple[Rect, Rect, Rect]:
    if min(rect.width, rect.height, preferred, first_min, second_min) < 0:
        raise ValueError("negative geometry")
    size = rect.height if vertical else rect.width
    layout = Split(first_min, second_min, preferred).layout(size)
    if layout.compact:
        return Rect(rect.x, rect.y, 0, 0), Rect(rect.x, rect.y, 0, 0), rect
    first, second = layout.first, layout.second
    if vertical:
        return (Rect(rect.x, rect.y, rect.width, first), Rect(rect.x, rect.y + first, rect.width, 1),
                Rect(rect.x, rect.y + first + 1, rect.width, second))
    return (Rect(rect.x, rect.y, first, rect.height), Rect(rect.x + first, rect.y, 1, rect.height),
            Rect(rect.x + first + 1, rect.y, second, rect.height))


def container(rect: Rect, ids: list[str], *, vertical: bool = False, gap: int = 0) -> dict[str, Rect]:
    if len(ids) != len(set(ids)) or any(not id for id in ids) or gap < 0:
        raise ValueError("invalid container IDs/gap")
    if not ids:
        return {}
    size = rect.height if vertical else rect.width
    usable = max(0, size - gap * (len(ids) - 1))
    result, offset = {}, 0
    for i, id in enumerate(ids):
        extent = usable // len(ids) + int(i < usable % len(ids))
        extent = min(extent, max(0, size - offset))
        result[id] = Rect(rect.x, rect.y + offset, rect.width, extent) if vertical else Rect(rect.x + offset, rect.y, extent, rect.height)
        offset = min(size, offset + extent + gap)
    return result


@dataclass(frozen=True)
class LineRun:
    text: str
    role: str
    id: str
    start: int
    width: int


@dataclass
class LineLayout:
    runs: list[LineRun] = field(default_factory=list)
    omitted: int = 0

    @property
    def text(self) -> str:
        return ''.join(r.text for r in self.runs)

    def add(self, text: str, role: str, id: str = '') -> None:
        text = clean(text)
        x = sum(r.width for r in self.runs)
        self.runs.append(LineRun(text, role, id, x, cells(text)))

    def hit(self, x: int) -> str:
        return next((r.id for r in self.runs if r.start <= x < r.start + r.width), '')

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        canvas.fill(rect)
        for run in self.runs:
            canvas.write(rect.x + run.start, rect.y, run.text, run.role, width=max(0, rect.width - run.start))


def tail_cells(text: str, width: int) -> str:
    text = clean(text)
    if cells(text) <= width:
        return text
    if width <= 0:
        return ''
    parts, used, result = graphemes(text), 0, []
    for g in reversed(parts):
        if used + cells(g) > width - 1:
            break
        result.insert(0, g)
        used += cells(g)
    return '~' + ''.join(result)


def path_runs(items: list[tuple[str, str]], width: int) -> LineLayout:
    out = LineLayout()
    if not items or width <= 0:
        return out
    if sum(cells(label) for _, label in items) + 3 * (len(items) - 1) <= width:
        for i, (id, label) in enumerate(items):
            if i:
                out.add(' / ', 'hint')
            out.add(label, 'body' if i == len(items) - 1 else 'hint', id)
        return out
    prefix = ''
    if len(items) > 2 and cells(items[0][1]) + 9 + cells(items[-1][1]) <= width:
        out.add(items[0][1], 'hint', items[0][0])
        prefix = ' / ... / '
    elif len(items) > 1 and width >= 7:
        prefix = '... / '
    out.add(prefix, 'hint')
    out.add(tail_cells(items[-1][1], width - cells(out.text)), 'body', items[-1][0])
    return out


def breadcrumbs(items: list[tuple[str, str]], width: int, ascii: bool = False) -> str:
    return path_runs(items, width).text


@dataclass
class StatusItem:
    id: str
    text: str
    role: str = "hint"
    priority: int = 0


def status(items: list[StatusItem], width: int) -> list[StatusItem]:
    remaining, selected = max(0, width), set()
    for i, item in sorted(enumerate(items), key=lambda p: (-p[1].priority, p[0])):
        need = cells(item.text) + (3 if selected else 0)
        if need <= remaining:
            selected.add(i)
            remaining -= need
    return [item for i, item in enumerate(items) if i in selected]


def status_line(items: list[StatusItem], width: int) -> LineLayout:
    ordered = sorted(items, key=lambda item: -item.priority)
    out = LineLayout(omitted=len(items))
    if width <= 0:
        return out
    included = 0
    for i, item in enumerate(ordered):
        reserve = len(f' +{len(ordered) - i - 1}') if i + 1 < len(ordered) else 0
        separator = ' | ' if included else ''
        prefix = {'warning': '! ', 'error': '! ', 'edited': '* ', 'success': '+ ', 'info': 'i '}.get(item.role, '')
        text = prefix + clean(item.text)
        needed = cells(separator) + cells(text)
        if needed + reserve > width - cells(out.text):
            if included:
                break
            available = width - reserve if width - reserve > 0 else width
            text = prefix[:1] if available == 1 and prefix else clip(text, available, True)
            separator = ''
        if separator:
            out.add(separator, 'hint')
        out.add(text, item.role or 'body', item.id)
        included += 1
        if needed + reserve > width:
            break
    out.omitted = len(items) - included
    marker = f' +{out.omitted}'
    if out.omitted and cells(out.text) + len(marker) <= width:
        out.add(marker, 'hint')
    return out


@dataclass
class Notice:
    id: str
    text: str
    severity: str = "info"
    priority: int = 0
    expires_at: int = 0
    persistent: bool = False


class Notices:
    def __init__(self, capacity: int = 10):
        if capacity < 1:
            raise ValueError("positive capacity required")
        self.capacity = capacity
        self.items: list[Notice] = []

    def push(self, notice: Notice) -> None:
        if not notice.id or notice.severity not in ("info", "success", "warning", "error"):
            raise ValueError("invalid notice")
        self.items = [i for i in self.items if i.id != notice.id] + [notice]
        self.items = sorted(self.items, key=lambda i: (i.priority, i.severity == "error"), reverse=True)[:self.capacity]

    def visible(self, now: int) -> list[Notice]:
        return [i for i in self.items if i.persistent or i.severity == "error" or not i.expires_at or i.expires_at > now]

    def dismiss(self, id: str) -> Event:
        self.items = [i for i in self.items if i.id != id]
        return Event("dismiss", id)

    def draw(self, canvas: Canvas, rect: Rect, *, now: int = 0, **_) -> None:
        canvas.fill(rect)
        for y, notice in enumerate(self.visible(now)[:rect.height]):
            canvas.write(rect.x, rect.y + y, clip(notice.text, rect.width, True), notice.severity, width=rect.width)


@dataclass
class Progress:
    value: int = 0
    total: int = 0
    label: str = ""
    cancellable: bool = False

    def cancel(self) -> Event:
        return Event("cancel") if self.cancellable else Event()

    def draw(self, canvas: Canvas, rect: Rect, *, frame: int = 0, **_) -> None:
        fraction = max(0, min(1, self.value / self.total)) if self.total > 0 else 0
        text = f"{self.label} {int(fraction * 100)}%" if self.total > 0 else f"{self.label} {'|/-'[frame % 3]}"
        canvas.write(rect.x, rect.y, clip(text, rect.width, True), "info", width=rect.width)


@dataclass
class DataState:
    status: str = "empty"
    message: str = ""
    def draw(self, canvas: Canvas, rect: Rect, **_) -> None:
        role = "error" if self.status == "error" else "hint"
        canvas.write(rect.x, rect.y, clip(self.message or self.status, rect.width, True), role, width=rect.width)


def popup_placement(anchor: Rect, viewport: Rect, width: int, height: int, *, shadow: bool = False) -> tuple[Rect, Rect]:
    if min(width, height, viewport.width, viewport.height) < 0:
        raise ValueError("negative popup size")
    w = min(viewport.width, width + int(shadow))
    h = min(viewport.height, height + int(shadow))
    x = max(viewport.x, min(viewport.x + viewport.width - w, anchor.x))
    y = anchor.y + anchor.height
    if y + h > viewport.y + viewport.height:
        y = anchor.y - h
    y = max(viewport.y, min(viewport.y + viewport.height - h, y))
    card = Rect(x, y, max(0, w - int(shadow and w > 0)), max(0, h - int(shadow and h > 0)))
    return card, Rect(x, y, w, h)


class Drag:
    """Opt-in request state; host validates/applies immutable model replacement."""
    def __init__(self, enabled: bool = False):
        self.enabled, self.source, self.target = enabled, "", ""
        self.start_x = self.start_y = 0
        self.active = False

    def begin(self, id: str, x: int, y: int) -> bool:
        if not self.enabled or not id:
            return False
        self.source, self.target = id, ""
        self.start_x, self.start_y, self.active = x, y, False
        return True

    def move(self, target: str, x: int, y: int, *, allowed: bool = True) -> None:
        if not self.source:
            return
        self.active |= abs(x - self.start_x) + abs(y - self.start_y) >= 2
        self.target = target if allowed and target != self.source else ""

    def cancel(self) -> Event:
        self.source = self.target = ""
        self.active = False
        return Event("drag_cancel")

    def drop(self) -> Event:
        event = Event("drop", self.source, data={"target": self.target}) if self.active and self.target else Event()
        self.cancel()
        return event
