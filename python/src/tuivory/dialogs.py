"""Literal confirmation surfaces; hosts own visibility and accept action requests."""
from dataclasses import dataclass,field
from copy import deepcopy
from .drawing import Canvas,Rect,cells,clip,clean,graphemes
from .layout import inset_rect
from .models import Event

def _text(value,limit):
    if not isinstance(value,str)or len(value.encode('utf-8'))>limit:raise ValueError('invalid dialog text/ID')
    return value

def _wrap(text,width,limit):
    if not text:return [],False
    if width<=0 or limit<=0:return [],True
    rows=[];line='';used=0;last_break=False;truncated=False
    for g in graphemes(text):
        if g in ('\r','\n','\r\n'):
            if len(rows)>=limit:truncated=True;break
            rows.append(line);line='';used=0;last_break=True;continue
        last_break=False;g=clean(g);n=cells(g)
        if n>width:g=clip(g,width,True);n=cells(g)
        if used+n>width and line:
            if len(rows)>=limit:truncated=True;break
            rows.append(line);line='';used=0
        if len(rows)>=limit:truncated=True;break
        line+=g;used+=n
    else:
        if line or not rows or last_break:
            if len(rows)<limit:rows.append(line)
            else:truncated=True
    if truncated and rows:rows[-1]=clip(rows[-1],max(0,width-1))+'~'
    return rows,truncated

@dataclass
class DialogButton:
    id:str
    label:str=''
    disabled:bool=False
@dataclass(frozen=True)
class DialogButtonCell:
    id:str
    rect:Rect
    text:str
    disabled:bool=False
    focused:bool=False
@dataclass
class DialogLayout:
    body:list[str]=field(default_factory=list)
    buttons:list[DialogButtonCell]=field(default_factory=list)
    hidden_buttons:int=0
    body_truncated:bool=False

class Dialog:
    def __init__(self,title='',message='',buttons=(),cancel_id=''):
        self._title='';self._message='';self._buttons=[];self._cancel='';self._focused='';self._hits=[]
        self.set_text(title=title,message=message);self.set_buttons(buttons,cancel_id=cancel_id)
    @property
    def title(self):return self._title
    @property
    def message(self):return self._message
    @property
    def buttons(self):return deepcopy(self._buttons)
    @property
    def cancel_id(self):return self._cancel
    @property
    def focused(self):return self._focused
    def set_text(self,*,title=None,message=None):
        title=_text(self._title if title is None else title,4096);message=_text(self._message if message is None else message,1_000_000)
        self._title,self._message=title,message;self._hits=[]
    def set_buttons(self,buttons,*,cancel_id=None):
        source=[deepcopy(b)if isinstance(b,DialogButton)else DialogButton(**b)for b in buttons]
        if len(source)>1024:raise ValueError('too many dialog buttons')
        ids=set()
        for b in source:
            _text(b.id,1024);_text(b.label,4096)
            if not b.id or b.id in ids:raise ValueError('empty/duplicate dialog button ID')
            ids.add(b.id);b.disabled=bool(b.disabled)
        cancel=_text(self._cancel if cancel_id is None else cancel_id,1024)
        if cancel and cancel not in ids:raise ValueError('unknown dialog cancel ID')
        eligible=[b.id for b in source if not b.disabled]
        focus=self._focused if self._focused in eligible else cancel if cancel in eligible else next(iter(eligible),'')
        self._buttons,self._cancel,self._focused=source,cancel,focus;self._hits=[]
    def focus(self,id):
        if not any(b.id==id and not b.disabled for b in self._buttons):return False
        if self._focused!=id:self._focused=id;self._hits=[]
        return True
    def handle(self,action):
        eligible=[b.id for b in self._buttons if not b.disabled]
        if action=='cancel':
            if self._cancel:return Event('cancel',self._cancel)if self._cancel in eligible else Event()
            return Event('cancel')
        if action=='activate':return Event('activate',self._focused)if self._focused in eligible else Event()
        if not eligible:return Event()
        at=eligible.index(self._focused)if self._focused in eligible else 0
        if action in ('next','right','down'):at=(at+1)%len(eligible)
        elif action in ('previous','left','up'):at=(at-1)%len(eligible)
        elif action=='home':at=0
        elif action=='end':at=len(eligible)-1
        else:return Event()
        id=eligible[at]
        if id==self._focused:return Event()
        self.focus(id);return Event('focus',id)
    def layout(self,width,height):
        for v in (width,height):
            if type(v)is not int or not 0<=v<=1_000_000:raise ValueError('invalid dialog dimensions')
        if not width or not height:return DialogLayout(hidden_buttons=len(self._buttons),body_truncated=bool(self._message))
        positions=[];x=y=0;focus_row=0
        for b in self._buttons:
            label=clean(b.label or b.id);w=min(width,max(1,cells(label)+4))
            if x and x+1+w>width:x=0;y+=1
            if x:x+=1
            positions.append((b,Rect(x,y,w,1)))
            if b.id==self._focused:focus_row=y
            x+=w
        total_rows=y+1 if positions else 0;visible=min(height,total_rows);start=max(0,focus_row+1-visible)
        available=height-visible;gap=1 if self._message and visible and available>=2 else 0
        body,truncated=_wrap(self._message,width,available-gap);buttons=[]
        for b,r in positions:
            if not start<=r.y<start+visible:continue
            label=clean(b.label or b.id)
            text='[ '+clip(label,max(0,r.width-4),True)+' ]'if r.width>=6 else clip(label,r.width,True)
            buttons.append(DialogButtonCell(b.id,Rect(r.x,height-visible+r.y-start,r.width,1),text,b.disabled,b.id==self._focused))
        return DialogLayout(body,buttons,len(self._buttons)-len(buttons),truncated)
    def draw(self,canvas:Canvas,bounds:Rect,*,focused=True,ascii=False):
        for v,limit in [(bounds.x,1_000_000_000),(bounds.y,1_000_000_000),(bounds.width,1_000_000),(bounds.height,1_000_000)]:
            if type(v)is not int or not 0<=v<=limit:raise ValueError('invalid dialog bounds')
        self._hits=[];x=min(bounds.x,canvas.width);y=min(bounds.y,canvas.height)
        r=Rect(x,y,max(0,min(canvas.width,bounds.x+bounds.width)-x),max(0,min(canvas.height,bounds.y+bounds.height)-y))
        inner=inset_rect(canvas.panel(r,self._title,focused,ascii),1);layout=self.layout(inner.width,inner.height)
        for row,text in enumerate(layout.body):canvas.write(inner.x,inner.y+row,text,'body',width=inner.width)
        for b in layout.buttons:
            rect=Rect(inner.x+b.rect.x,inner.y+b.rect.y,b.rect.width,1);role='disabled'if b.disabled else'button.focus'if focused and b.focused else'button'
            canvas.fill(rect,role);canvas.write(rect.x+max(0,(rect.width-cells(b.text))//2),rect.y,b.text,role,width=rect.width)
            self._hits.append((rect,b.id,b.disabled))
        return layout
    def click(self,x,y):
        if type(x)is not int or type(y)is not int:return Event()
        for rect,id,disabled in self._hits:
            if rect.contains(x,y):
                if disabled:return Event()
                self.focus(id);return Event('activate',id)
        return Event()
