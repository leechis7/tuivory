"""Host-controlled focus, menus, geometry, feedback and drag requests."""
from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
from .drawing import Canvas, Rect, cells, clip, clean, graphemes
from .models import ControlState, Event, Item, List, unique


@dataclass
class FocusTarget:
    id: str
    state: ControlState = field(default_factory=ControlState)
    hidden: bool = False


@dataclass(frozen=True)
class InputRoute:
    scope_id: str
    blocked: bool


@dataclass(frozen=True)
class PopupCloseRequest:
    id: str
    reason: str = 'escape'


class Focus:
    """Host-owned scope stack; empty popups still consume input."""
    def __init__(self,id,targets):
        if not id:raise ValueError('empty root scope')
        unique(targets)
        self.scopes=[dict(id=id,targets=deepcopy(targets),focused='',restore='',dismissible=False)]
        self._reconcile(self.scopes[-1])

    @staticmethod
    def _ids(scope):return [t.id for t in scope['targets'] if not t.hidden and t.state.focusable]

    def _reconcile(self,scope):
        ids=self._ids(scope)
        if scope['focused'] not in ids:scope['focused']=ids[0] if ids else ''

    @property
    def focused(self):return self.scopes[-1]['focused']

    @property
    def scope_id(self):return self.scopes[-1]['id']

    @property
    def depth(self):return len(self.scopes)-1

    def open(self,id,targets,initial='',dismissible=True):
        if not id or len(self.scopes)>=65 or any(s['id']==id for s in self.scopes):raise ValueError('invalid scope or depth')
        unique(targets)
        scope=dict(id=id,targets=deepcopy(targets),focused='',restore=self.focused,dismissible=dismissible)
        self._reconcile(scope)
        if initial:
            if initial not in self._ids(scope):raise ValueError('initial target not focusable')
            scope['focused']=initial
        self.scopes.append(scope)

    def update(self,id,targets):
        unique(targets)
        scope=next((s for s in self.scopes if s['id']==id),None)
        if scope is None:raise ValueError('unknown scope')
        owned=deepcopy(targets)
        scope['targets']=owned;self._reconcile(scope)

    def close(self,id):
        if self.depth==0 or self.scope_id!=id:raise ValueError('only top popup can close')
        restore=self.scopes.pop()['restore'];top=self.scopes[-1]
        if restore in self._ids(top):top['focused']=restore
        else:self._reconcile(top)
        return Event('focus',self.focused)

    def focus(self,id):
        if id not in self._ids(self.scopes[-1]):return False
        self.scopes[-1]['focused']=id;return True

    def move(self,previous=False):
        top=self.scopes[-1];ids=self._ids(top)
        if not ids:top['focused']=''
        else:
            at=ids.index(top['focused']) if top['focused'] in ids else None
            next=((at or 0)+len(ids)-1)%len(ids) if previous else (at+1)%len(ids) if at is not None else 0
            top['focused']=ids[next]
        return self.focused

    def request_close(self):
        return PopupCloseRequest(self.scope_id) if self.depth and self.scopes[-1]['dismissible'] else None

    def route(self,target=''):
        return InputRoute(self.scope_id,bool(target and target!=self.scope_id))

    def blocked(self,scope):return self.route(scope).blocked


@dataclass
class MenuItem(Item):
    mnemonic: str = ''


@dataclass(frozen=True)
class MenuEvent:
    kind: str = ''
    id: str = ''
    return_id: str = ''

    @property
    def data(self):return {'return_id':self.return_id}

    @property
    def text(self):return ''


@dataclass
class MenuSpan:
    start: int
    width: int
    text: str
    role: str


@dataclass
class MenuRow:
    id: str
    text: str
    role: str
    spans: list[MenuSpan] = field(default_factory=list)
    focused: bool = False


@dataclass
class MenuBarCell:
    id: str
    text: str
    role: str
    start: int
    width: int
    focused: bool


@dataclass
class MenuBarLayout:
    cells: list[MenuBarCell] = field(default_factory=list)
    previous: bool = False
    next: bool = False


class Menu:
    def __init__(self,items):
        self._items=[];self._by_id={};self._children={};self._path=[];self._focus={};self._top={}
        self.opened=False;self.context=False;self.return_id='';self.bar='';self.bar_first=0
        self.back_label='Back';self.empty_label='(empty)';self._hits=[];self._width=0
        self.set_items(items)

    @property
    def items(self):return deepcopy(self._items)

    @staticmethod
    def _validate(items):
        unique(items)
        if len(items)>10000:raise ValueError('too many menu items')
        by_id={i.id:i for i in items};children={};keys=set()
        for i in items:
            if i.id.startswith('@'):raise ValueError('reserved menu ID')
            if i.mnemonic:
                key=i.mnemonic.lower()
                if len(key)!=1 or not key.isascii() or not key.isalnum() or i.separator or (i.parent,key) in keys:raise ValueError('invalid/duplicate mnemonic')
                keys.add((i.parent,key))
            children.setdefault(i.parent,[]).append(i.id)
        for i in items:
            if i.separator and children.get(i.id):raise ValueError('separator cannot have children')
            parent=i.parent;seen={i.id};depth=1
            while parent:
                if parent not in by_id or parent in seen or by_id[parent].separator:raise ValueError('invalid parent/cycle')
                depth+=1
                if depth>32:raise ValueError('menu depth exceeds32')
                seen.add(parent);parent=by_id[parent].parent
        return by_id,children

    def set_items(self,items):
        owned=[deepcopy(i) if isinstance(i,MenuItem) else MenuItem(**vars(i)) for i in items]
        by_id,children=self._validate(owned)
        self._items,self._by_id,self._children=owned,by_id,children
        self._focus={p:id for p,id in self._focus.items() if not p or p in by_id}
        self._top={p:top for p,top in self._top.items() if not p or p in by_id}
        self._hits=[]
        if not self._usable(self.bar,''):self.bar=self._first('')
        for n,id in enumerate(self._path):
            if not self._usable(id,self._path[n-1] if n else '') or not self._children.get(id):return self.close()
        if self.opened:self._reconcile()
        return MenuEvent()

    @property
    def path(self):return list(self._path)

    def _parent(self):return self._path[-1] if self._path else ''

    def _usable(self,id,parent):
        i=self._by_id.get(id)
        return bool(i is not None and i.parent==parent and not i.disabled and not i.separator)

    def _first(self,parent):return next((id for id in self._children.get(parent,[]) if self._usable(id,parent)),'')

    def _back_allowed(self):return len(self._path)>1 or self.context and bool(self._path)

    def _reconcile(self):
        p=self._parent();id=self._focus.get(p,'')
        if id=='@back' and self._back_allowed():return
        if not self._usable(id,p):self._focus[p]=self._first(p) or ('@back' if self._back_allowed() else '')

    @property
    def focused(self):return self._focus.get(self._parent(),'')

    @property
    def bar_focused(self):return self.bar

    def title(self):return ' / '.join(clean(self._by_id[id].label) for id in self._path)

    def _event(self,kind='',id=''):return MenuEvent(kind,id,self.return_id)

    def _finish(self,kind,id=''):
        self.opened=False;self._path=[];self._hits=[];return self._event(kind,id)

    def open(self,id='',return_id=''):
        path=[];at=id
        while at:
            item=self._by_id.get(at)
            if item is None or item.disabled or item.separator:return MenuEvent()
            path.insert(0,at);at=item.parent
        self.return_id=return_id;self._path=path;self._hits=[]
        for n,child in enumerate(path):self._focus[path[n-1] if n else '']=child
        self.context=not id;self.opened=True
        if path:self.bar=path[0]
        if id and not self._children.get(id):return self._finish('activate',id)
        self._reconcile();return self._event('open',id)

    def close(self):return self._finish('close') if self.opened else MenuEvent()

    def back(self):
        if not self.opened:return MenuEvent()
        if not self._back_allowed():return self.close()
        self._path.pop();self._reconcile();return self._event('back',self._parent())

    def focus(self,id):
        if not self.opened:return False
        if id=='@back' and self._back_allowed() or self._usable(id,self._parent()):self._focus[self._parent()]=id;return True
        return False

    def _enter(self,id):
        self._path.append(id);self._reconcile();return self._event('open',id)

    def _switch_root(self,next):
        ids=[id for id in self._children.get('',[]) if self._usable(id,'')]
        if not ids:return MenuEvent()
        at=ids.index(self.bar) if self.bar in ids else 0;step=1 if next else len(ids)-1
        for _ in ids:
            at=(at+step)%len(ids)
            if ids[at]!=self.bar and self._children.get(ids[at]):return self.open(ids[at],self.return_id)
        return MenuEvent()

    def handle(self,action,value='',height=10):
        if not self.opened:return MenuEvent()
        self._reconcile();p=self._parent();id=self.focused
        if action in ('cancel','back'):return self.back()
        if action=='close':return self.close()
        if action=='left':return self.back() if self._back_allowed() else MenuEvent() if self.context else self._switch_root(False)
        if action=='right':
            if self._usable(id,p) and self._children.get(id):return self._enter(id)
            return self._switch_root(True) if not self._back_allowed() and not self.context else MenuEvent()
        if action=='activate':
            if id=='@back':return self.back()
            if not self._usable(id,p):return MenuEvent()
            return self._enter(id) if self._children.get(id) else self._finish('activate',id)
        if action=='mnemonic':
            if len(value)!=1 or not value.isascii() or not value.isalnum():return MenuEvent()
            for candidate in self._children.get(p,[]):
                item=self._by_id[candidate]
                if self._usable(candidate,p) and item.mnemonic and item.mnemonic.lower()==value.lower():self._focus[p]=candidate;return self.handle('activate','',height)
            return MenuEvent()
        ids=(['@back'] if self._back_allowed() else [])+[id for id in self._children.get(p,[]) if self._usable(id,p)]
        if not ids:return MenuEvent()
        at=ids.index(id) if id in ids else 0
        if action in ('previous','up'):at=(at+len(ids)-1)%len(ids)
        elif action in ('next','down'):at=(at+1)%len(ids)
        elif action in ('first','home'):at=0
        elif action in ('last','end'):at=len(ids)-1
        elif action=='page_up':at=max(0,at-max(1,height-1))
        elif action=='page_down':at=min(len(ids)-1,at+max(1,height-1))
        else:return MenuEvent()
        self._focus[p]=ids[at];return self._event('focus',ids[at])

    def handle_bar(self,action,value=''):
        ids=[id for id in self._children.get('',[]) if self._usable(id,'')]
        if not ids:return MenuEvent()
        at=ids.index(self.bar) if self.bar in ids else 0
        if action in ('previous','left'):at=(at+len(ids)-1)%len(ids)
        elif action in ('next','right'):at=(at+1)%len(ids)
        elif action in ('first','home'):at=0
        elif action in ('last','end'):at=len(ids)-1
        elif action in ('activate','down'):return MenuEvent('open_request',ids[at])
        elif action=='mnemonic':
            if len(value)!=1 or not value.isascii() or not value.isalnum():return MenuEvent()
            for id in ids:
                item=self._by_id[id]
                if item.mnemonic and item.mnemonic.lower()==value.lower():self.bar=id;return MenuEvent('open_request',id)
            return MenuEvent()
        else:return MenuEvent()
        self.bar=ids[at];return MenuEvent('focus',self.bar)

    def click_id(self,id):return self.handle('activate') if self.focus(id) else MenuEvent()

    def click(self,x,y=None,height=10):
        if isinstance(x,str):return self.click_id(x)
        if not self.opened or x<0 or x>=self._width or y is None or y<0 or y>=min(height,len(self._hits)):return MenuEvent()
        return self.click_id(self._hits[y].id)

    @staticmethod
    def _label(i):return i.label+(' ('+i.mnemonic.upper()+')' if i.mnemonic else '')

    def _rows(self):
        return ([MenuItem('@back',self.back_label),MenuItem('',separator=True)] if self._back_allowed() else [])+[self._by_id[id] for id in self._children.get(self._parent(),[])]

    def content_size(self):
        rows=self._rows();width=12
        for i in rows:width=max(width,cells(self._label(i))+cells(i.secondary)+cells(i.shortcut)+cells(i.icon)+8)
        return min(width,4096),max(1,len(rows))

    def layout(self,width,height,ascii=False):
        self._hits=[];self._width=max(0,min(width,65535));height=max(0,min(height,4096));width=self._width
        if not self.opened or not width or not height:return []
        self._reconcile();rows=self._rows()
        if not rows:self._hits=[MenuRow('',clip(self.empty_label,width,True),'hint')];return self._hits
        at=next((n for n,i in enumerate(rows) if i.id==self.focused),0);p=self._parent();top=min(self._top.get(p,0),at)
        if at>=top+height:top=at-height+1
        top=min(top,max(0,len(rows)-height));self._top[p]=top
        for i in rows[top:top+height]:
            if i.separator:self._hits.append(MenuRow('',('-' if ascii else '─')*width,'hint'));continue
            current=i.id==self.focused;role='disabled' if i.disabled else 'selection' if current else 'surface'
            icon=(i.ascii_icon or ('*' if i.icon else '')) if ascii else i.icon
            prefix=('> ' if current else '  ')+(icon+' ' if icon else '')
            text=prefix+('< '+i.label if i.id=='@back' else self._label(i))+('  '+i.secondary if i.secondary else '')
            suffix=(' >' if ascii else ' ›') if self._children.get(i.id) else ''
            shortcut=clean(i.shortcut);reserve=min(width//3,cells(shortcut));tail=(' '+clip(shortcut,reserve)+suffix) if reserve else suffix;tw=min(width,cells(tail))
            left=clip(text,width-tw,True);spans=[MenuSpan(0,width,left,role)]
            if tw:spans.append(MenuSpan(width-tw,tw,clip(tail,tw),'hint' if role=='surface' else role))
            combined=left+' '*max(0,width-tw-cells(left))+clip(tail,tw)
            self._hits.append(MenuRow(i.id,combined,role,spans,current))
        return self._hits

    def draw(self,canvas,rect,*,ascii=False):
        if not self.opened:return
        canvas.fill(rect,'surface')
        for y,row in enumerate(self.layout(rect.width,rect.height,ascii)):
            canvas.fill(Rect(rect.x,rect.y+y,rect.width,1),row.role)
            if not row.spans:canvas.write(rect.x,rect.y+y,row.text,row.role,width=rect.width,preserve_background=False)
            for span in row.spans:canvas.write(rect.x+span.start,rect.y+y,span.text,span.role,width=span.width,preserve_background=False)

    def draw_popup(self, canvas, rect, title='', *, padding=1, ascii=False):
        """Draw inside the host's rectangle; return the content hit-test rectangle."""
        if not self.opened:
            return Rect(rect.x, rect.y, 0, 0)
        inner = canvas.panel(rect, title, False, ascii)
        padding = max(0, min(4096, int(padding)))
        px, py = min(padding, inner.width // 2), min(padding, inner.height // 2)
        content = Rect(inner.x + px, inner.y + py,
                       max(0, inner.width - 2 * px), max(0, inner.height - 2 * py))
        self.draw(canvas, content, ascii=ascii)
        return content

    def bar_layout(self,width):
        width=max(0,min(width,65535));out=MenuBarLayout()
        if width<3:return out
        ids=[id for id in self._children.get('',[]) if not self._by_id[id].separator]
        if not ids:return out
        target=ids.index(self.bar) if self.bar in ids else 0;self.bar_first=min(self.bar_first,target)
        size=lambda n:min(24,cells(self._label(self._by_id[ids[n]]))+2)
        while self.bar_first<target and sum(size(n)for n in range(self.bar_first,target+1))>width-2:self.bar_first+=1
        while self.bar_first>0 and sum(size(n)for n in range(self.bar_first-1,target+1))<=width-2:self.bar_first-=1
        x=1;last=self.bar_first
        for n,id in enumerate(ids[self.bar_first:],self.bar_first):
            if x>=width-1:break
            i=self._by_id[id];w=min(size(n),width-1-x);current=id==self.bar;role='disabled' if i.disabled else 'selection' if current else 'header'
            out.cells.append(MenuBarCell(id,clip(' '+self._label(i)+' ',w,True),role,x,w,current));x+=w;last=n+1
        out.previous=self.bar_first>0;out.next=last<len(ids);return out

    def bar_click(self,x,width):
        if x<0 or x>=width:return MenuEvent()
        layout=self.bar_layout(width)
        if x==0 and layout.previous:return self.handle_bar('previous')
        if x+1==width and layout.next:return self.handle_bar('next')
        for cell in layout.cells:
            if cell.start<=x<cell.start+cell.width and self._usable(cell.id,''):self.bar=cell.id;return MenuEvent('open_request',cell.id)
        return MenuEvent()

    def draw_bar(self,canvas,rect):
        if rect.height<=0:return
        canvas.fill(Rect(rect.x,rect.y,rect.width,1),'surface');layout=self.bar_layout(rect.width)
        for cell in layout.cells:
            canvas.fill(Rect(rect.x+cell.start,rect.y,cell.width,1),cell.role)
            canvas.write(rect.x+cell.start,rect.y,cell.text,cell.role,width=cell.width,preserve_background=False)
        if layout.previous:canvas.write(rect.x,rect.y,'<','hint',width=1)
        if layout.next:canvas.write(rect.x+rect.width-1,rect.y,'>','hint',width=1)


def menu_placement(anchor,viewport,width,height):
    w=min(max(0,width),max(0,viewport.width));h=min(max(0,height),max(0,viewport.height))
    x=max(viewport.x,min(viewport.x+max(0,viewport.width)-w,anchor.x));y=anchor.y+max(0,anchor.height)
    if y+h>viewport.y+viewport.height:y=anchor.y-h
    y=max(viewport.y,min(viewport.y+max(0,viewport.height)-h,y))
    return Rect(x,y,w,h)


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
