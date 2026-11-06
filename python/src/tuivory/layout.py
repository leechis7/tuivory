"""Cell geometry and supporting components; hosts choose screens and bindings."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from .drawing import Rect, cells, clean, clip, fold
from .models import ControlState, Event
from .feedback import FeedbackRow, FeedbackSpan, _draw, _number


def _extent(value, maximum=1_000_000_000):
    if not isinstance(value,int) or isinstance(value,bool) or not 0<=value<=maximum:
        raise ValueError('invalid layout extent')
    return value


def _rect(rect):
    for value in (rect.x,rect.y,rect.width,rect.height):
        _extent(value)


@dataclass(frozen=True)
class SpacingTokens:
    gap: int = 0
    padding: int = 0
    control_gap: int = 1
    compact_below: int = 80

    @staticmethod
    def for_width(density,columns):
        _extent(columns)
        if density not in ('auto','compact','comfortable'):
            raise ValueError('invalid density')
        compact=density=='compact' or density=='auto' and columns<80
        return SpacingTokens() if compact else SpacingTokens(2,1,2)


def inset_rect(rect,padding):
    _rect(rect);_extent(padding,1024)
    return Rect(rect.x+min(padding,rect.width),rect.y+min(padding,rect.height),
                max(0,rect.width-2*padding),max(0,rect.height-2*padding))


@dataclass(frozen=True)
class StackItem:
    id: str
    min: int = 1
    preferred: int = 0
    weight: int = 1


@dataclass(frozen=True)
class StackSlot:
    id: str
    start: int
    size: int


@dataclass
class StackResult:
    slots: list[StackSlot] = field(default_factory=list)
    hidden: list[str] = field(default_factory=list)
    gap: int = 0


def stack_layout(items,total,gap=0):
    _extent(total);_extent(gap,1024)
    if len(items)>1024 or len({i.id for i in items})!=len(items):
        raise ValueError('invalid stack items')
    for item in items:
        if not item.id or not _extent(item.min,1_000_000):
            raise ValueError('invalid stack minimum/ID')
        _extent(item.preferred,1_000_000);_extent(item.weight,1_000_000)
    if not items:
        return StackResult()
    minimum=sum(i.min for i in items)
    gaps=gap*(len(items)-1)
    if gaps>total or total-gaps<minimum:
        gap=0
    available=total-gap*(len(items)-1)
    sizes=[0]*len(items);active=[False]*len(items)
    for n,item in enumerate(items):
        if item.min>available and n>0:
            continue
        sizes[n]=min(item.min,available);available-=sizes[n];active[n]=True
    for n,item in enumerate(items):
        if active[n]:
            add=min(max(0,item.preferred-sizes[n]),available)
            sizes[n]+=add;available-=add
    weights=sum(i.weight for n,i in enumerate(items) if active[n])
    if weights:
        extra=available
        for n,item in enumerate(items):
            if active[n]:
                add=extra*item.weight//weights;sizes[n]+=add;available-=add
        for n,item in enumerate(items):
            if available and active[n] and item.weight:
                sizes[n]+=1;available-=1
    result=StackResult(gap=gap);start=visible=0
    for n,item in enumerate(items):
        if not sizes[n]:
            result.hidden.append(item.id)
        else:
            if visible:start+=gap
            visible+=1
        result.slots.append(StackSlot(item.id,start,sizes[n]))
        start+=sizes[n]
    return result


@dataclass(frozen=True)
class NamedRect:
    id: str
    rect: Rect


@dataclass
class LayoutResult:
    rects: list[NamedRect] = field(default_factory=list)
    hidden: list[str] = field(default_factory=list)


def stack_rects(parent,items,tokens=SpacingTokens(),*,vertical=False):
    inner=inset_rect(parent,tokens.padding)
    result=stack_layout(items,inner.height if vertical else inner.width,tokens.gap)
    rects=[NamedRect(s.id,Rect(inner.x,inner.y+s.start,inner.width,s.size) if vertical else
                     Rect(inner.x+s.start,inner.y,s.size,inner.height)) for s in result.slots]
    return LayoutResult(rects,[r.id for r in rects if not r.rect.width or not r.rect.height])


@dataclass(frozen=True)
class DrawerPlacement:
    rect: Rect
    overlay: bool


def drawer_layout(parent,preferred,min_content=0):
    _rect(parent);_extent(preferred);_extent(min_content)
    return DrawerPlacement(Rect(parent.x,parent.y,min(parent.width,preferred),parent.height),
                           parent.width<preferred+min_content)


@dataclass
class Badge:
    id: str = ''
    label: str = ''
    count: int | None = None
    limit: int = 99
    state: ControlState = field(default_factory=ControlState)

    def line(self,width):
        _extent(width,65535);_number(self.limit)
        text=self.label
        if self.count is not None:
            _number(self.count);limit=self.limit or 99
            text+=' ['+(str(limit)+'+' if self.count>limit else str(self.count))+']'
        return FeedbackRow(self.id,clip(self.state.markers.lstrip('-')+text,width,True),self.state.role)

    def draw(self,canvas,rect):
        _draw(canvas,rect,[self.line(max(0,rect.width))])


@dataclass
class Chip:
    id: str = ''
    label: str = ''
    state: ControlState = field(default_factory=ControlState)
    removable: bool = False

    def line(self,width):
        _extent(width,65535)
        prefix=self.state.markers.lstrip('-')+'['
        suffix='] x' if self.removable else ']'
        text=clip(prefix+clip(self.label,max(0,width-cells(prefix)-cells(suffix)),True)+suffix,width,True)
        spans=[]
        if self.removable and text.endswith(' x'):
            spans.append(FeedbackSpan(cells(text)-1,1,'x',self.state.role if self.state.editable else 'disabled',
                                      'remove',not self.state.editable))
        return FeedbackRow(self.id,text,self.state.role,spans=spans)

    def request_remove(self):
        return Event('remove',self.id) if self.id and self.removable and self.state.editable else Event()

    def draw(self,canvas,rect):
        _draw(canvas,rect,[self.line(max(0,rect.width))])


@dataclass
class Shortcut:
    key: str
    text: str = ''
    priority: int = 0
    disabled: bool = False


_SPACE='\t\n\v\f\r \x85\xa0\u1680'+''.join(chr(c)for c in range(0x2000,0x200b))+'\u2028\u2029\u202f\u205f\u3000'


class Help:
    """Literal hints only. Hosts own key bindings and context-specific contents."""
    def __init__(self,items):
        if len(items)>65536:
            raise ValueError('too many shortcuts')
        owned=deepcopy(items);keys=set()
        for item in owned:
            key=fold(clean(item.key).strip(_SPACE))
            if not key or key in keys:
                raise ValueError('empty or duplicate shortcut')
            if not isinstance(item.priority,int) or isinstance(item.priority,bool) or not -(1<<31)<=item.priority<(1<<31):
                raise ValueError('priority must be a signed 32-bit integer')
            keys.add(key)
        self._items=sorted(owned,key=lambda i:-i.priority)

    def layout(self,width,height):
        _extent(width,65535);_extent(height,4096)
        limit=height-1 if len(self._items)>height and height>1 else height
        rows=[FeedbackRow(text=clip('['+s.key+'] '+s.text,width,True),role='disabled' if s.disabled else 'body')
              for s in self._items[:limit]]
        if len(self._items)>limit and height>len(rows):
            rows.append(FeedbackRow(text=clip('+'+str(len(self._items)-limit),width,True),role='hint'))
        return rows

    def draw(self,canvas,rect):
        _draw(canvas,rect,self.layout(max(0,rect.width),max(0,rect.height)))
