"""Independent Python component state. Returned events request host actions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from copy import deepcopy
from .drawing import Canvas, Rect, cells, clip, graphemes, fold


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


@dataclass(frozen=True)
class TabCell:
    id: str
    text: str
    start: int
    width: int
    active: bool
    focused: bool
    disabled: bool


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

    def layout(self, width: int) -> list[TabCell]:
        self._eligible()
        if width <= 2 or not self.items:
            return []
        target = next((i for i, t in enumerate(self.items) if t.id == self.focused), 0)
        self.first = max(0, min(self.first, target))
        size = lambda item: min(24, max(6, cells(item.title) + 5))
        while self.first < target and sum(size(t) for t in self.items[self.first:target + 1]) > width - 2:
            self.first += 1
        while self.first > 0 and sum(size(t) for t in self.items[self.first - 1:target + 1]) <= width - 2:
            self.first -= 1
        out, x = [], 1
        for item in self.items[self.first:]:
            if x >= width - 1:
                break
            w = min(size(item), width - 1 - x)
            if w < 4 and out:
                break
            active, focused = item.id == self.active, item.id == self.focused
            suffix = (' *' if item.edited else '') + (' x' if item.closable else '')
            label = clip(item.title, max(0, w - 3 - len(suffix)), True)
            text = clip(('>' if focused else ' ') + ('[' if active else ' ') + label + suffix + (']' if active else ' '), w, True)
            out.append(TabCell(item.id, text, x, w, active, focused, item.disabled))
            x += w
        return out

    def click(self, x: int, width: int) -> Event:
        views = self.layout(width)
        if x == 0 and self.first > 0:
            return self.handle('previous')
        if width > 0 and x == width - 1 and self.first + len(views) < len(self.items):
            return self.handle('next')
        for cell in views:
            if cell.start <= x < cell.start + cell.width and not cell.disabled:
                self.focused = cell.id
                if cell.text.endswith(('x]', 'x ')) and any(t.id == cell.id and t.closable for t in self.items) and x == cell.start + cells(cell.text) - 2:
                    return Event('close', cell.id)
                self.active = cell.id
                return Event('activate', cell.id)
        return Event()

    def draw(self, canvas: Canvas, rect: Rect, *, focused: bool = True, ascii: bool = False) -> None:
        canvas.fill(rect)
        views = self.layout(rect.width)
        if self.first > 0:
            canvas.write(rect.x, rect.y, '<', 'hint', width=1)
        if self.first + len(views) < len(self.items) and rect.width:
            canvas.write(rect.x + rect.width - 1, rect.y, '>', 'hint', width=1)
        for cell in views:
            role = 'disabled' if cell.disabled else 'selection' if cell.active else 'body'
            canvas.write(rect.x + cell.start, rect.y, ' ' * cell.width, role, focused=focused and cell.focused, width=cell.width)
            canvas.write(rect.x + cell.start, rect.y, cell.text,
                         'disabled' if cell.disabled else 'selection' if cell.active else 'body',
                         focused=focused and cell.focused, width=cell.width)


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
    def __init__(self,items):
        self.items=[];self.focused=self.selected=self.query='';self.empty='(empty)';self.scroll=0;self._hits=[];self._width=0
        self.set_items(items)

    def set_items(self,items):
        unique(items);owned=deepcopy(items)
        if self.selected not in [i.id for i in owned]:self.selected=''
        self.items=owned;self._eligible()

    def visible(self):
        q=fold(self.query)
        return [i for i in self.items if not q or not i.separator and q in fold(i.label+' '+i.secondary)]

    def _eligible(self):
        items=[i for i in self.visible() if not i.disabled and not i.separator]
        if self.focused not in [i.id for i in items]:self.focused=items[0].id if items else ''
        return items

    def focus(self,id):
        if not any(i.id==id and not i.disabled and not i.separator for i in self.visible()):return False
        self.focused=id;return True

    def set_query(self,query):
        self.query=''.join(c for c in query if ord(c)>=32 and not 127<=ord(c)<160);self._eligible();return Event('query',text=self.query)

    def handle(self,action,height=10,text=''):
        if action=='query':return self.set_query(text)
        items=self._eligible()
        if not items:return Event()
        ids=[i.id for i in items];at=ids.index(self.focused)
        if action in ('activate','select'):self.selected=self.focused;return Event(action,self.focused)
        action={'up':'previous','down':'next','home':'first','end':'last'}.get(action,action)
        if action=='previous':at=max(0,at-1)
        elif action=='next':at=min(len(ids)-1,at+1)
        elif action=='first':at=0
        elif action=='last':at=len(ids)-1
        elif action=='page_up':at=max(0,at-max(1,height-1))
        elif action=='page_down':at=min(len(ids)-1,at+max(1,height-1))
        else:return Event()
        self.focused=ids[at];return Event('focus',self.focused)

    def layout(self,width,height,ascii=False):
        rows=[];anchor=0
        for item in self.visible():
            current=item.id==self.focused
            if current:anchor=len(rows)
            role='disabled' if item.disabled else 'selection' if item.id==self.selected else 'body'
            if item.separator:rows.append(CollectionRow(item.id,'--- '+item.label+' ---','hint'));continue
            icon=item.ascii_icon if ascii else item.icon
            text=('> ' if current else '  ')+('* ' if item.id==self.selected else '')+(icon+' ' if icon else '')+item.label+(' ['+item.shortcut+']' if item.shortcut else '')
            rows.append(CollectionRow(item.id,text,role,current))
            if item.secondary:rows.append(CollectionRow(item.id,'    '+item.secondary,'disabled' if item.disabled else 'hint'))
        if not rows:rows=[CollectionRow('',self.empty,'hint')]
        height=max(0,height);width=max(0,width);self.scroll=min(max(0,anchor-max(0,height-2)),max(0,len(rows)-height));self._width=width
        self._hits=rows[self.scroll:self.scroll+height]
        for row in self._hits:row.text=clip(row.text,width)
        return self._hits

    def click_id(self,id):
        if not self.focus(id):return Event()
        return self.handle('activate')

    def click(self,x,y,height=10):
        if x<0 or x>=self._width or y<0 or y>=min(height,len(self._hits)):return Event()
        return self.click_id(self._hits[y].id)

    def draw(self,canvas,rect,*,focused=True,ascii=False):
        canvas.fill(rect)
        for y,row in enumerate(self.layout(rect.width,rect.height,ascii)):
            canvas.fill(Rect(rect.x,rect.y+y,rect.width,1),row.role)
            canvas.write(rect.x,rect.y+y,row.text,row.role,focused=focused and row.focused,width=rect.width,preserve_background=True)


@dataclass
class CollectionRow:
    id: str
    text: str
    role: str = 'body'
    focused: bool = False


class SearchPicker:
    def __init__(self,items):
        self.list=List(items);self.open=False;self.value='';self._width=self._height=0

    def handle(self,action,text='',height=10):
        if action=='open':self.open=True;self.list.set_query('');self.list.focus(self.value);return Event('open')
        if action=='cancel':self.open=False;return Event('cancel')
        if action in ('insert','backspace'):
            if not self.open:self.handle('open')
            query=self.list.query+text if action=='insert' else ''.join(graphemes(self.list.query)[:-1])
            return self.list.set_query(query)
        if action=='activate':
            if not self.open:return self.handle('open')
            e=self.list.handle('activate',height)
            if e.id:self.value=e.id;self.open=False;return Event('change',e.id)
            return e
        return self.list.handle(action,height) if self.open else Event()

    def click_id(self,id):
        if not self.list.focus(id):return Event()
        return self.handle('activate')

    def click(self,x,y,height=10):
        if x<0 or x>=self._width or y<0 or y>=min(height,self._height):return Event()
        if not self.open:return self.handle('open')
        if y==0:return Event()
        e=self.list.click(x,y-1,max(0,height-1))
        if e.id:self.value=e.id;self.open=False;return Event('change',e.id)
        return Event()

    def layout(self,width,height,ascii=False):
        self._width=max(0,width);self._height=max(0,height)
        if height<=0:return []
        if not self.open:
            label=next((i.label for i in self.list.items if i.id==self.value),self.list.empty)
            return [CollectionRow(self.value,clip('v '+label,width),'field')]
        from .editing import Text
        query=Text(self.list.query,multiline=False).window(max(0,width-2))[0]
        return [CollectionRow('',clip('? '+query,width),'field')]+self.list.layout(width,max(0,height-1),ascii)

    def draw(self,canvas,rect,*,focused=True,ascii=False):
        canvas.fill(rect);rows=self.layout(rect.width,rect.height,ascii)
        if not self.open:
            if rows:
                canvas.fill(Rect(rect.x,rect.y,rect.width,1),'field')
                canvas.write(rect.x,rect.y,rows[0].text,'field',width=rect.width,preserve_background=True)
            return
        if rect.height>0:
            canvas.fill(Rect(rect.x,rect.y,rect.width,1),'field')
            canvas.write(rect.x,rect.y,'? ','field',width=rect.width,preserve_background=True)
            if rect.width>2:
                from .editing import Text
                Text(self.list.query,multiline=False).draw(canvas,Rect(rect.x+2,rect.y,rect.width-2,1),focused=focused)
        if rect.height>1:self.list.draw(canvas,Rect(rect.x,rect.y+1,rect.width,rect.height-1),focused=focused,ascii=ascii)
