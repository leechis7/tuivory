"""Independent Python component state. Returned events request host actions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .drawing import Canvas, Rect, cells, clip, graphemes


@dataclass(frozen=True)
class Event:
    kind: str = ""
    id: str = ""
    text: str = ""
    data: Any = None


@dataclass
class ControlState:
    disabled: bool = False
    read_only: bool = False
    busy: bool = False
    selected: bool = False
    edited: bool = False
    invalid: bool = False

    @property
    def focusable(self) -> bool:
        return not self.disabled

    @property
    def activatable(self) -> bool:
        return not (self.disabled or self.busy)

    @property
    def editable(self) -> bool:
        return self.activatable and not self.read_only

    @property
    def role(self) -> str:
        return "disabled" if self.disabled else "error" if self.invalid else "selection" if self.selected else "edited" if self.edited else "body"

    @property
    def markers(self) -> str:
        return "".join(c for flag, c in [(self.disabled, "-"), (self.invalid, "!"), (self.selected, ">"), (self.edited, "*"), (self.busy, "~"), (self.read_only, "=")] if flag)


def unique(items: list[Any]) -> None:
    ids = [i.id for i in items]
    if any(not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("IDs must be nonempty and unique")


@dataclass(frozen=True)
class Node:
    id: str
    name: str = ""
    parent: str = ""
    secondary: str = ""
    icon: str = ""
    ascii_icon: str = ""
    count: int | None = None
    branch: bool = False


class Tree:
    def __init__(self, nodes: list[Node]):
        unique(nodes)
        self.nodes = tuple(nodes)
        self.depth: dict[str, int] = {}
        self.by_id = {n.id: n for n in nodes}
        self.branches: set[str] = {n.id for n in nodes if n.branch}
        # A parent must precede its descendants in contiguous preorder.
        stack: list[str] = []
        for n in nodes:
            if n.parent:
                if n.parent not in stack:
                    raise ValueError("tree requires contiguous preorder")
                stack = stack[:stack.index(n.parent) + 1]
                self.branches.add(n.parent)
            else:
                stack = []
            if len(stack) > 128:
                raise ValueError("tree depth exceeds 128")
            self.depth[n.id] = len(stack)
            stack.append(n.id)
        self.selected = ""
        self.expanded: set[str] = set()
        self.scroll = self.horizontal = 0
        self._reconcile(1)

    def visible(self) -> list[Node]:
        result: list[Node] = []
        visible: set[str] = set()
        for n in self.nodes:
            if not n.parent or n.parent in visible and n.parent in self.expanded:
                visible.add(n.id)
                result.append(n)
        return result

    def _reconcile(self, height: int) -> list[Node]:
        self.expanded &= self.branches
        visible = self.visible()
        ids = [n.id for n in visible]
        while self.selected and self.selected not in ids and self.selected in self.by_id:
            self.selected = self.by_id[self.selected].parent
        if self.selected not in ids:
            self.selected = ids[0] if ids else ""
        if ids:
            i = ids.index(self.selected)
            h = max(1, height)
            self.scroll = min(self.scroll, max(0, len(ids) - h))
            if i < self.scroll:
                self.scroll = i
            if i >= self.scroll + h:
                self.scroll = i - h + 1
        else:
            self.scroll = 0
        return visible

    def handle(self, action: str, height: int = 10) -> Event:
        rows = self._reconcile(height)
        if not rows:
            return Event()
        ids = [n.id for n in rows]
        old = self.selected
        n, i = self.by_id[old], ids.index(old)
        target = i
        moves = {"up": i - 1, "down": i + 1, "home": 0, "end": len(rows) - 1,
                 "page_up": i - max(1, height), "page_down": i + max(1, height)}
        if action in moves:
            target = max(0, min(len(rows) - 1, moves[action]))
        elif action == "pan_left":
            self.horizontal = max(0, self.horizontal - 4)
        elif action == "pan_right":
            self.horizontal = min(65535, self.horizontal + 4)
        elif action == "activate":
            return Event("activate", old)
        elif action == "left":
            if old in self.expanded:
                self.expanded.remove(old)
                self._reconcile(height)
                return Event("collapse", old)
            if n.parent:
                self.selected = n.parent
        elif action in ("right", "toggle") and old in self.branches:
            if action == "toggle" and old in self.expanded:
                self.expanded.remove(old)
                self._reconcile(height)
                return Event("collapse", old)
            if old not in self.expanded:
                self.expanded.add(old)
                self._reconcile(height)
                return Event("expand", old)
            if i + 1 < len(rows) and rows[i + 1].parent == old:
                target += 1
        if target != i:
            self.selected = ids[target]
        self._reconcile(height)
        return Event("select", self.selected) if old != self.selected else Event()

    def click(self, x: int, y: int, height: int = 10) -> Event:
        rows = self._reconcile(height)
        if not 0 <= y < height or self.scroll + y >= len(rows):
            return Event()
        old = self.selected
        n = rows[self.scroll + y]
        self.selected = n.id
        if x >= 2 and x + self.horizontal == 2 + 2 * self.depth[n.id]:
            event = self.handle("toggle", height)
            if event.kind:
                return event
        return Event("select", n.id) if old != n.id else Event()

    def draw(self, canvas: Canvas, rect: Rect, *, focused: bool = True, ascii: bool = False) -> None:
        canvas.fill(rect)
        rows = self._reconcile(rect.height)
        for y, n in enumerate(rows[self.scroll:self.scroll + rect.height]):
            selected = self.selected == n.id
            prefix = "> " if selected else "  "
            arrow = ("v" if ascii else "▾") if n.id in self.expanded else (">" if ascii else "▸")
            arrow = arrow if n.id in self.branches else " "
            icon = n.ascii_icon if ascii else n.icon
            text = "  " * self.depth[n.id] + arrow + " " + ((icon + " ") if icon else "") + n.name
            if n.secondary:
                text += "  " + n.secondary
            if n.count is not None:
                text += f" ({n.count})"
            # Pan by cells, never slice a multibyte code point or half a grapheme.
            skipped = 0
            parts = graphemes(text)
            while parts and skipped < self.horizontal:
                skipped += cells(parts.pop(0))
            role = "selection" if selected else "body"
            canvas.write(rect.x, rect.y + y, prefix + clip("".join(parts), max(0, rect.width - 2), True),
                         role, focused=focused and selected, width=rect.width)


@dataclass
class Tab:
    id: str
    title: str = ""
    edited: bool = False
    closable: bool = False
    disabled: bool = False


class Tabs:
    def __init__(self, items: list[Tab]):
        unique(items)
        self.items = list(items)
        self.active = self.focused = ""
        self.first = 0
        self._eligible()

    def _eligible(self) -> list[Tab]:
        items = [i for i in self.items if not i.disabled]
        ids = [i.id for i in items]
        if self.active not in ids:
            self.active = ids[0] if ids else ""
        if self.focused not in ids:
            self.focused = self.active
        return items

    def handle(self, action: str) -> Event:
        items = self._eligible()
        if not items:
            return Event()
        i = next(i for i, t in enumerate(items) if t.id == self.focused)
        if action == "activate":
            self.active = self.focused
            return Event("activate", self.active)
        if action == "close":
            return Event("close", self.focused) if items[i].closable else Event()
        target = {"previous": max(0, i - 1), "next": min(len(items) - 1, i + 1), "first": 0, "last": len(items) - 1}.get(action, i)
        if target != i:
            self.focused = items[target].id
            return Event("focus", self.focused)
        return Event()

    def layout(self, width: int) -> list[tuple[Tab, int, str]]:
        self._eligible()
        if width <= 2:
            return []
        focused = next((i for i, t in enumerate(self.items) if t.id == self.focused), 0)
        self.first = min(self.first, focused)
        def build(start: int) -> list[tuple[Tab, int, str]]:
            out, x = [], 1 if start else 0
            for item in self.items[start:]:
                size = min(24, max(6, cells(item.title) + 5))
                if x + size > width - 1:
                    break
                label = ("*" if item.edited else " ") + clip(item.title, size - 4, True) + (" x" if item.closable else "  ")
                out.append((item, x, label.ljust(size - cells(label) + len(label))))
                x += size
            return out
        out = build(self.first)
        while self.first < focused and not any(t.id == self.focused for t, _, _ in out):
            self.first += 1
            out = build(self.first)
        return out

    def click(self, x: int, width: int) -> Event:
        for tab, start, text in self.layout(width):
            if start <= x < start + cells(text) and not tab.disabled:
                self.focused = self.active = tab.id
                return Event("activate", tab.id)
        return Event()

    def draw(self, canvas: Canvas, rect: Rect, *, focused: bool = True, ascii: bool = False) -> None:
        canvas.fill(rect)
        for tab, x, text in self.layout(rect.width):
            role = "disabled" if tab.disabled else "selection" if self.active == tab.id else "body"
            canvas.write(rect.x + x, rect.y, text, role, focused=focused and self.focused == tab.id, width=rect.width - x)


@dataclass
class Item:
    id: str
    label: str = ""
    secondary: str = ""
    shortcut: str = ""
    icon: str = ""
    ascii_icon: str = ""
    disabled: bool = False
    separator: bool = False
    parent: str = ""


class List:
    def __init__(self, items: list[Item]):
        unique(items)
        self.items = list(items)
        self.focused = self.selected = self.query = ""
        self.scroll = 0
        self._eligible()

    def visible(self) -> list[Item]:
        return [i for i in self.items if not self.query or self.query.casefold() in (i.label + " " + i.secondary).casefold()]

    def _eligible(self) -> list[Item]:
        eligible = [i for i in self.visible() if not i.disabled and not i.separator]
        if self.focused not in [i.id for i in eligible]:
            self.focused = eligible[0].id if eligible else ""
        return eligible

    def handle(self, action: str, height: int = 10, text: str = "") -> Event:
        if action == "query":
            self.query = text
            self._eligible()
            return Event("query", text=text)
        eligible = self._eligible()
        if not eligible:
            return Event()
        i = next(i for i, t in enumerate(eligible) if t.id == self.focused)
        if action == "activate":
            self.selected = self.focused
            return Event("activate", self.focused)
        target = {"up": i - 1, "down": i + 1, "home": 0, "end": len(eligible) - 1,
                  "page_up": i - max(1, height), "page_down": i + max(1, height)}.get(action, i)
        target = max(0, min(len(eligible) - 1, target))
        if i != target:
            self.focused = eligible[target].id
            return Event("focus", self.focused)
        return Event()

    def click(self, x: int, y: int, height: int = 10) -> Event:
        rows = self.visible()
        if not 0 <= y < height or self.scroll + y >= len(rows):
            return Event()
        item = rows[self.scroll + y]
        if item.disabled or item.separator:
            return Event()
        self.focused = self.selected = item.id
        return Event("activate", item.id)

    def draw(self, canvas: Canvas, rect: Rect, *, focused: bool = True, ascii: bool = False) -> None:
        canvas.fill(rect)
        self._eligible()
        rows = self.visible()
        index = next((i for i, t in enumerate(rows) if t.id == self.focused), 0)
        h = max(1, rect.height)
        self.scroll = max(0, min(self.scroll, max(0, len(rows) - h)))
        if index < self.scroll:
            self.scroll = index
        elif index >= self.scroll + h:
            self.scroll = index - h + 1
        for y, item in enumerate(rows[self.scroll:self.scroll + rect.height]):
            current = item.id == self.focused
            role = "disabled" if item.disabled else "selection" if current else "body"
            if item.separator:
                text = ("-" if ascii else "─") * rect.width
            else:
                icon = item.ascii_icon if ascii else item.icon
                text = ("> " if current else "  ") + (icon + " " if icon else "") + item.label
                if item.secondary:
                    text += "  " + item.secondary
                if item.shortcut:
                    text += "  " + item.shortcut
            canvas.write(rect.x, rect.y + y, clip(text, rect.width, True), role,
                         focused=focused and current, width=rect.width)
