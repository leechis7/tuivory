"""Grapheme editing and host-approved grid operations; no database or clipboard I/O."""
from __future__ import annotations
import regex
from dataclasses import dataclass, field
from copy import deepcopy
from .drawing import Canvas, Rect, cells, clip, graphemes
from .models import ControlState, Event, unique


class Text:
    """Literal grapheme buffer. Only copy/cut events contain selected raw text."""
    def __init__(self, value: str = "", *, read_only: bool = False, secret: bool = False, multiline: bool = True):
        self.value = value
        self.cursor = self.anchor = len(graphemes(value))
        self.read_only, self.secret, self.multiline = read_only, secret, multiline
        self.disabled = False
        self.scroll_x = self.scroll_y = 0
        self._undo = []
        self._redo = []

    def __repr__(self):
        return f"Text({self.display()!r}, cursor={self.cursor}, anchor={self.anchor})"

    def display(self):
        return "*" * len(graphemes(self.value)) if self.secret else self.value

    def select(self, anchor: int, cursor: int) -> None:
        n = len(graphemes(self.value))
        self.anchor, self.cursor = max(0, min(n, anchor)), max(0, min(n, cursor))

    def _save(self):
        self._undo.append((self.value, self.cursor, self.anchor))
        self._undo = self._undo[-128:]
        self._redo.clear()

    def _replace_range(self, lo, hi, text):
        parts = graphemes(self.value)
        if self.disabled or self.read_only or lo == hi and not text:
            return Event()
        self._save()
        prefix = "".join(parts[:lo]) + text
        self.value = prefix + "".join(parts[hi:])
        offset = cursor = 0
        for g in graphemes(self.value):
            if offset >= len(prefix):
                break
            offset += len(g)
            cursor += 1
        self.select(cursor, cursor)
        return Event("change")

    def selection_bytes(self):
        parts = graphemes(self.value)
        a, b = sorted((min(self.anchor,len(parts)),min(self.cursor,len(parts))))
        return len("".join(parts[:a]).encode()), len("".join(parts[:b]).encode())

    def _byte_index(self, byte):
        offset = 0
        for i, g in enumerate(graphemes(self.value)):
            if offset == byte:
                return i
            offset += len(g.encode())
        if offset == byte:
            return len(graphemes(self.value))
        raise ValueError("offset splits a grapheme or is outside text")

    def select_bytes(self, anchor, cursor):
        a, c = self._byte_index(anchor), self._byte_index(cursor)
        self.select(a,c)

    def replace_bytes(self, start, end, text):
        if start > end:
            raise ValueError("reversed byte range")
        a,b = self._byte_index(start),self._byte_index(end)
        return self._replace_range(a,b,text)

    def handle(self, action: str, text: str = "") -> Event:
        if self.disabled:
            return Event()
        self.select(self.anchor, self.cursor)
        parts = graphemes(self.value)
        lo,hi = sorted((self.anchor,self.cursor))
        at = self.cursor
        breaks = ("\n","\r","\r\n")
        start = at
        while start and parts[start-1] not in breaks:
            start -= 1
        end = at
        while end < len(parts) and parts[end] not in breaks:
            end += 1
        extend = action.startswith("select_")
        move = action[7:] if extend else action
        target = None
        if move == "all" and extend:
            self.select(0,len(parts)); return Event("select")
        if move == "left": target = lo if not extend and lo != hi else max(0,at-1)
        if move == "right": target = hi if not extend and lo != hi else min(len(parts),at+1)
        if move == "home": target = start
        if move == "end": target = end
        if move == "up":
            previous = max(0,start-1)
            while previous and parts[previous-1] not in breaks: previous -= 1
            target = min(previous+at-start,start-1) if start else at
        if move == "down":
            following = min(len(parts),end+1)
            while following < len(parts) and parts[following] not in breaks: following += 1
            target = min(end+1+at-start,following) if end < len(parts) else at
        if target is not None:
            self.select(self.anchor if extend else target,target)
            return Event("select")
        if action in ("copy","cut"):
            if self.secret or lo == hi or action == "cut" and self.read_only:
                return Event()
            copied = "".join(parts[lo:hi])
            if action == "cut": self._replace_range(lo,hi,"")
            return Event(action,text=copied)
        if self.read_only: return Event()
        if action in ("undo","redo"):
            src,dst = (self._undo,self._redo) if action == "undo" else (self._redo,self._undo)
            if not src: return Event()
            dst.append((self.value,self.cursor,self.anchor))
            self.value,self.cursor,self.anchor = src.pop()
            return Event("change")
        if action == "backspace":
            if lo == hi: lo = max(0,lo-1)
            text = ""
        elif action == "delete":
            if lo == hi: hi = min(len(parts),hi+1)
            text = ""
        elif action in ("insert","paste","newline"):
            if action == "newline": text = "\n"
            text = text.replace("\r\n","\n").replace("\r","\n")
            text = "".join(" " if c == "\t" else c for c in text if (ord(c)>=32 and not 127<=ord(c)<160) or c == "\t" or c == "\n" and self.multiline)
        else: return Event()
        return self._replace_range(lo,hi,text)

    def window(self, width: int) -> tuple[str, int, int]:
        parts = graphemes(self.display())
        cursor = max(0,min(len(parts),self.cursor))
        next_width = max(1,cells(parts[cursor])) if cursor<len(parts) else 1
        start = 0
        while start<cursor and cells("".join(parts[start:cursor]))+next_width>width: start+=1
        if next_width>width: return "",0,1
        return clip("".join(parts[start:]),width),cells("".join(parts[start:cursor])),next_width

    def _visual_rows(self):
        rows=[[]]
        for i,g in enumerate(graphemes(self.value)):
            if g in ("\r","\n","\r\n") and self.multiline:
                rows.append([])
            else: rows[-1].append((i,"*" if self.secret else g))
        return rows

    def draw(self, canvas: Canvas, rect: Rect, *, focused: bool = True, ascii: bool = False) -> None:
        role="disabled" if self.disabled else "field" if not self.read_only else "body"
        canvas.fill(rect,role)
        if rect.width<=0 or rect.height<=0: return
        rows=self._visual_rows()
        raw=graphemes(self.value)
        cy=sum(g in ("\r","\n","\r\n") for g in raw[:self.cursor]) if self.multiline else 0
        cy=min(cy,len(rows)-1)
        cx=sum(cells(g) for i,g in rows[cy] if i<self.cursor)
        cursor_g=next((g for i,g in rows[cy] if i==self.cursor)," ")
        cw=max(1,cells(cursor_g))
        self.scroll_y=max(0,min(self.scroll_y,cy),cy-rect.height+1)
        self.scroll_x=max(0,min(self.scroll_x,cx),cx+min(cw,rect.width)-rect.width)
        lo,hi=sorted((self.anchor,self.cursor))
        for y,row in enumerate(rows[self.scroll_y:self.scroll_y+rect.height]):
            x=0
            for i,g in row:
                n=cells(g); local=x-self.scroll_x
                if local>=0 and local+n<=rect.width:
                    canvas.write(rect.x+local,rect.y+y,g,"selection" if lo<=i<hi else role,width=n,preserve_background=False)
                x+=n
        if focused and not self.read_only and not self.disabled and cw<=rect.width:
            canvas.set_cursor(rect.x+cx-self.scroll_x,rect.y+cy-self.scroll_y,cw)

    def click(self,x,y,width,height,*,extend=False):
        if self.disabled or x<0 or y<0 or x>=width or y>=height: return Event()
        rows=self._visual_rows();row_index=min(len(rows)-1,self.scroll_y+y);row=rows[row_index]
        cell=0; target=(row[-1][0]+1 if row else sum(len(r)+1 for r in rows[:row_index]))
        for i,g in row:
            n=cells(g)
            if x+self.scroll_x<cell+n: target=i;break
            cell+=n
        self.select(self.anchor if extend else target,target)
        return Event("select")

@dataclass
class FormOption:
    id: str
    label: str = ""
    disabled: bool = False


@dataclass
class Field:
    id: str
    kind: str = "text"
    label: str = ""
    value: str = ""
    help: str = ""
    error: str = ""
    required: bool = False
    checked: bool = False
    options: list[FormOption | tuple[str,str]] = field(default_factory=list)
    state: ControlState = field(default_factory=ControlState)
    choice: str = ""
    action: str = ""
    open: bool = False
    pending: str = ""
    height: int = 3


@dataclass
class FormRow:
    id: str
    text: str
    role: str = "body"
    option: str = ""
    input: bool = False
    focused: bool = False
    source_row: int = 0


class Form:
    def __init__(self, fields: list[Field]):
        unique(fields)
        self.fields = deepcopy(fields)
        self.inputs = {}
        for f in self.fields:
            if f.kind not in ("text","textarea","password","button","checkbox","radio","select") or f.open:
                raise ValueError("unknown field kind or initially open select")
            f.options=[o if isinstance(o,FormOption) else FormOption(*o) for o in f.options]
            unique(f.options)
            if f.choice and f.choice not in [o.id for o in f.options]: raise ValueError("unknown choice")
            if f.kind in ("text","password","textarea"):
                self.inputs[f.id]=Text(f.value,secret=f.kind=='password',multiline=f.kind=='textarea')
                f.value=self.inputs[f.id].display()
        self.focused="";self.scroll=0;self._hits=[];self._width=0
        self._eligible()

    def _field(self,id):
        return next((f for f in self.fields if f.id==id),None)

    def _eligible(self):
        items=[f for f in self.fields if f.state.focusable]
        if self.focused not in [f.id for f in items]: self.focused=items[0].id if items else ''
        return items

    def focus(self,id):
        f=self._field(id)
        if not f or not f.state.focusable:return False
        for field in self.fields:field.open=False
        self.focused=id;return True

    def at_tab_boundary(self,previous=False):
        ids=[f.id for f in self._eligible()]
        return not ids or self.focused==ids[0 if previous else -1]

    def set_state(self,id,state):
        f=self._field(id)
        if not f:return False
        f.state=deepcopy(state)
        if not state.editable:f.open=False
        self._eligible();return True

    def set_feedback(self,id,help='',error=''):
        f=self._field(id)
        if not f:return False
        f.help,f.error=help,error;f.state.invalid=bool(error);return True

    def value(self,id):
        f=self._field(id)
        if not f:raise ValueError('unknown field')
        return self.inputs[id].value if id in self.inputs else f.value

    def select_text(self,id,anchor,cursor):
        if id not in self.inputs:return False
        self.inputs[id].select(anchor,cursor);return True

    def missing(self):
        out=[]
        for f in self.fields:
            empty=bool(regex.fullmatch(r"\p{White_Space}*",self.value(f.id))) if f.id in self.inputs else not f.checked if f.kind=='checkbox' else not f.choice if f.kind in ('radio','select') else False
            if not f.state.disabled and (f.error or f.state.invalid or f.required and empty):out.append(f.id)
        return out

    def handle(self,action,text=''):
        items=self._eligible()
        if action in ('next','previous'):
            if items:
                at=next(i for i,f in enumerate(items) if f.id==self.focused)
                self.focus(items[(at+(1 if action=='next' else -1))%len(items)].id)
            return Event()
        if action=='submit':
            missing=self.missing();return Event('invalid' if missing else 'submit',data=missing)
        f=self._field(self.focused)
        if not f:return Event()
        if action=='cancel':
            if f.open:f.open=False;return Event()
            return Event('cancel',f.id)
        if action=='insert' and text==' ' and f.id not in self.inputs:action='toggle'
        if f.id in self.inputs:
            t=self.inputs[f.id];t.disabled=f.state.disabled;t.read_only=not f.state.editable
            if action=='activate' and f.kind!='textarea':return self.handle('submit') if f.state.activatable else Event()
            e=t.handle('newline' if action=='activate' else action,text);f.value=t.display()
            if e.kind in ('change','cut'):f.state.edited=True
            return Event(e.kind,f.id,e.text)
        if f.kind=='button' and action in ('left','right') and not f.state.disabled:
            self.handle('previous' if action=='left' else 'next');return Event()
        if not f.state.activatable:return Event()
        if f.kind=='button' and action in ('activate','toggle'):
            return self.handle('submit') if f.action=='submit' else Event('cancel' if f.action=='cancel' else 'activate',f.id)
        if not f.state.editable:return Event()
        changed=False
        if f.kind=='checkbox' and action in ('activate','toggle'):f.checked=not f.checked;changed=True
        elif f.kind in ('radio','select'):
            if f.kind=='select' and action in ('activate','toggle'):
                if f.open:f.choice=f.pending;f.open=False;changed=True
                else:
                    f.open=True;f.pending=f.choice or next((o.id for o in f.options if not o.disabled),'');return Event()
            elif action in ('left','right','up','down','activate','toggle'):
                if f.kind=='select' and not f.open:return Event()
                ids=[o.id for o in f.options if not o.disabled]
                if not ids:return Event()
                current=f.pending if f.open else f.choice
                at=ids.index(current) if current in ids else None
                target=ids[((at or 0)-1)%len(ids)] if action in ('left','up') else ids[(at+1)%len(ids)] if at is not None else ids[0]
                if f.kind=='select':f.pending=target
                else:f.choice=target;changed=True
        if changed:f.state.edited=True;return Event('change',f.id)
        return Event()

    def click_field(self,id,option=''):
        f=self._field(id)
        if not f or f.state.disabled or any(o.id==option and o.disabled for o in f.options):return Event()
        if self.focused!=id:self.focus(id)
        if f.kind=='button':return self.handle('activate')
        if not f.state.editable:return Event()
        if f.kind=='select' and not f.open:return self.handle('activate')
        if option and f.kind in ('radio','select'):
            if not any(o.id==option and not o.disabled for o in f.options):return Event()
            f.choice=option;f.open=False;f.state.edited=True;return Event('change',f.id)
        if f.kind in ('checkbox','select'):return self.handle('activate')
        return Event()

    def layout(self,width,height):
        rows=[];anchor=0
        for f in self.fields:
            current=f.id==self.focused
            if current:anchor=len(rows)
            role='disabled' if f.state.disabled else 'error' if f.error or f.state.invalid else f.state.role
            markers=f.state.markers.lstrip('-') if f.state.disabled else f.state.markers
            rows.append(FormRow(f.id,('> ' if current else '  ')+f.label+(' *' if f.required else '')+(' '+markers if markers else ''),role,focused=current))
            if f.id in self.inputs:
                display=self.inputs[f.id].display().splitlines() if f.kind=='textarea' else [self.inputs[f.id].display()]
                for i,text in enumerate((display or [''])[:max(1,f.height) if f.kind=='textarea' else 1]):rows.append(FormRow(f.id,'  '+text,'disabled' if f.state.disabled else 'field',input=True,source_row=i))
            elif f.kind=='checkbox':rows.append(FormRow(f.id,'  [x]' if f.checked else '  [ ]',role))
            elif f.kind=='button':rows.append(FormRow(f.id,'  [ '+f.label+(' ~' if f.state.busy else '')+' ]','disabled' if f.state.disabled else 'hint' if f.state.busy else 'button',focused=current))
            else:
                for o in f.options:
                    if f.kind=='select' and not f.open and o.id!=f.choice:continue
                    selected=o.id==(f.pending if f.open else f.choice)
                    rows.append(FormRow(f.id,'  ('+('*' if selected else ' ')+') '+o.label,'disabled' if o.disabled or f.state.disabled else role,option=o.id))
            if f.error:rows.append(FormRow(f.id,'! '+f.error,'error'))
            elif f.help:rows.append(FormRow(f.id,'  '+f.help,'hint'))
        height=max(0,height);width=max(0,width)
        start=min(max(0,anchor-max(0,height-2)),max(0,len(rows)-height))
        self.scroll=start
        self._width=width
        self._hits=rows[start:start+height]
        for r in self._hits:r.text=clip(r.text,width)
        return self._hits

    def click(self,x,y,height=10):
        if x<0:return Event()
        if not self._hits:return Event()
        if x>=self._width or not 0<=y<min(height,len(self._hits)):return Event()
        row=self._hits[y]
        if row.input and x>=2:
            f=self._field(row.id)
            if not f or f.state.disabled:return Event()
            if self.focused!=f.id:self.focus(f.id)
            indices=[i for i,r in enumerate(self._hits) if r.id==row.id and r.input]
            return self.inputs[f.id].click(x-2,y-indices[0],max(0,self._width-2),len(indices))
        return self.click_field(row.id,row.option)

    def draw(self,canvas,rect,*,focused=True,ascii=False):
        canvas.fill(rect);rows=self.layout(rect.width,rect.height)
        for y,row in enumerate(rows):canvas.write(rect.x,rect.y+y,row.text,row.role,focused=focused and row.focused,width=rect.width)
        for f in self.fields:
            indices=[i for i,r in enumerate(rows) if r.id==f.id and r.input]
            if not indices:continue
            t=self.inputs[f.id];t.disabled=f.state.disabled;t.read_only=not f.state.editable
            t.draw(canvas,Rect(rect.x+min(2,rect.width),rect.y+indices[0],max(0,rect.width-2),len(indices)),focused=focused and self.focused==f.id)


class Control(Form):
    def __init__(self, field: Field):super().__init__([field])


@dataclass
class Column:
    id: str
    label: str = ""
    width: int = 12
    editable: bool = False
    hidden: bool = False
    pin: str = ""


@dataclass
class Record:
    id: str
    cells: dict[str, str | None] = field(default_factory=dict)
    state: ControlState = field(default_factory=ControlState)
    cell_states: dict[str, ControlState] = field(default_factory=dict)
