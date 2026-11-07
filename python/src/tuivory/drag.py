"""Independent request-only tab/tree movement; hosts approve immutable replacements."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, replace
from .models import Tree,Tabs,Node,TabCell
from .drawing import Rect,Canvas,Style,cells,clip

class DropError(ValueError):
    def __init__(self,reason):self.reason=reason;super().__init__(reason)

@dataclass(frozen=True)
class DropRequest:
    source_id: str
    target_id: str
    position: str
    revision: str

@dataclass
class DragOptions:
    threshold: int = 0
    auto_scroll: bool = False
    hover_expand: bool = False
    locked: tuple[str,...] = ()

@dataclass(frozen=True)
class DragPointer:
    action: str
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass(frozen=True)
class DragLayout:
    first: int = 0
    scroll: int = 0
    expanded: tuple[str,...] = ()
    tabs: tuple[TabCell,...] = ()
    rows: tuple[Node,...] = ()

def _revision(parts):
    result=14695981039346656037
    for part in parts:
        data=part.encode('utf-8')
        for b in str(len(data)).encode('ascii')+b':'+data:
            result=((result^b)*1099511628211)&0xffffffffffffffff
    return f'{result:016x}'

def _options(options):
    o=deepcopy(options)if options is not None else DragOptions()
    if type(o.threshold)is not int or not 0<=o.threshold<=1_000_000:raise DropError('options')
    if len(o.locked)>65536 or any(not isinstance(id,str)or not id or len(id.encode('utf-8'))>1_000_000 for id in o.locked):raise DropError('options')
    o.locked=tuple(o.locked)
    return o

def _nodes(model):
    return [replace(n,branch=n.id in model.branches)for n in model.nodes]

def drag_revision(model):
    parts=[]
    if isinstance(model,Tabs):
        for t in model.items:parts.extend((t.id,t.title,str(t.edited).lower(),str(t.closable).lower(),str(t.disabled).lower()))
    elif isinstance(model,Tree):
        for n in _nodes(model):parts.extend((n.id,n.parent,n.name,n.secondary,n.icon,n.ascii_icon,''if n.count is None else str(n.count),str(n.branch).lower()))
    else:raise DropError('model')
    return _revision(parts)

def _state_revision(model):
    return _revision((model.active,model.focused,str(model.first)))if isinstance(model,Tabs)else _revision((model.selected,str(model.scroll),str(model.horizontal),*sorted(model.expanded)))

def _copy_state(old,new):
    if isinstance(old,Tabs):
        new.active,new.focused,new.first=old.active,old.focused,old.first
        new._eligible()
    else:
        new.selected,new.scroll,new.horizontal=old.selected,old.scroll,old.horizontal
        new.expanded=set(old.expanded)&set(new.by_id)
    return new

def apply_drop(model,request):
    """Return a new model; structural validation never mutates the source."""
    if request.revision!=drag_revision(model):raise DropError('stale')
    source,target=request.source_id,request.target_id
    position=request.position
    if isinstance(model,Tabs):
        if source==target:raise DropError('self')
        if position not in ('before','after'):raise DropError('position')
        items=deepcopy(model.items)
        si=next((i for i,t in enumerate(items)if t.id==source),None)
        ti=next((i for i,t in enumerate(items)if t.id==target),None)
        if si is None or ti is None:raise DropError('missing')
        if items[si].disabled or items[ti].disabled:raise DropError('disabled')
        item=items.pop(si);ti-=int(si<ti);ti+=int(position=='after')
        if si==ti:raise DropError('unchanged')
        items.insert(ti,item)
        return _copy_state(model,Tabs(items))
    if not isinstance(model,Tree):raise DropError('model')
    nodes=_nodes(model);index={n.id:i for i,n in enumerate(nodes)}
    if source not in index or target not in index:raise DropError('missing')
    if source==target:raise DropError('self')
    if position not in ('before','after','inside'):raise DropError('position')
    si,ti=index[source],index[target]
    parent=target
    while parent:
        if parent==source:raise DropError('cycle')
        parent=nodes[index[parent]].parent
    if position=='inside'and not nodes[ti].branch:raise DropError('leaf')
    end=si+1
    while end<len(nodes)and model.depth[nodes[end].id]>model.depth[source]:end+=1
    new_depth=model.depth[target]+int(position=='inside')
    if new_depth+max(model.depth[n.id]-model.depth[source] for n in nodes[si:end])>128:raise DropError('depth')
    block=nodes[si:end];remaining=nodes[:si]+nodes[end:]
    at=next(i for i,n in enumerate(remaining)if n.id==target)
    parent=target if position=='inside'else remaining[at].parent
    if position!='before':
        at+=1
        while at<len(remaining)and model.depth[remaining[at].id]>model.depth[target]:at+=1
    block[0]=replace(block[0],parent=parent)
    reordered=remaining[:at]+block+remaining[at:]
    if [(n.id,n.parent)for n in reordered]==[(n.id,n.parent)for n in nodes]:raise DropError('unchanged')
    return _copy_state(model,Tree(reordered))

def request_drop(model,source_id,target_id,position,options=None,allow=None):
    o=_options(options)
    if source_id in o.locked or target_id in o.locked:raise DropError('locked')
    request=DropRequest(source_id,target_id,position,drag_revision(model))
    apply_drop(model,request)
    if allow is not None:
        if not callable(allow):raise DropError('policy')
        try:allowed=bool(allow(request))
        except Exception as error:raise DropError('policy')from error
        if not allowed:raise DropError('policy')
        if request.revision!=drag_revision(model):raise DropError('stale')
    return request

def keyboard_drop(model,direction,options=None,allow=None):
    if isinstance(model,Tabs):
        i=next((i for i,t in enumerate(model.items)if t.id==model.focused),None)
        if i is None:raise DropError('missing')
        if direction not in ('previous','next'):raise DropError('position')
        j=i+(-1 if direction=='previous'else 1)
        if not 0<=j<len(model.items):raise DropError('missing')
        return request_drop(model,model.focused,model.items[j].id,'before'if direction=='previous'else'after',options,allow)
    if not isinstance(model,Tree):raise DropError('model')
    node=model.by_id.get(model.selected)
    if node is None:raise DropError('missing')
    if direction=='outside'and node.parent:return request_drop(model,node.id,node.parent,'after',options,allow)
    siblings=[n for n in model.nodes if n.parent==node.parent]
    i=next(i for i,n in enumerate(siblings)if n.id==node.id)
    if direction not in ('previous','next','inside'):raise DropError('position')
    j=i+(1 if direction=='next'else-1)
    if not 0<=j<len(siblings):raise DropError('missing')
    return request_drop(model,node.id,siblings[j].id,'inside'if direction=='inside'else'after'if direction=='next'else'before',options,allow)

class DragState:
    """Opt-in gesture state. Previews do not modify the source model."""
    def __init__(self,enabled=False):
        self.enabled=bool(enabled);self._render_key='';self._busy=False
        self._reset('')
    def _reset(self,result):
        self.phase='idle';self.result=result;self.source_id=self.target_id=self.position=self.reason=''
        self.allowed=False;self._request=None;self._revision=self._state_revision=''
        self._x=self._y=self._width=self._height=self._first=self._scroll=0
        self._expanded=set();self._pointer=DragPointer('cancel')
    @property
    def captured(self):return self.phase in ('armed','dragging')
    def cancel(self):
        if self._busy:raise DropError('reentrant')
        self._reset('cancel')
    def render_key(self,key):
        if self._busy:raise DropError('reentrant')
        if not isinstance(key,str):raise DropError('render_key')
        if self.captured and self._render_key and key!=self._render_key:self._reset('stale')
        self._render_key=key
    def _valid(self,model,width,height):
        if not self.captured:return False
        if not self.enabled:self._reset('cancel');return False
        if self._revision!=drag_revision(model)or self._state_revision!=_state_revision(model)or self._width!=width or self._height!=height:
            self._reset('stale');return False
        return True
    def _tab_cells(self,model,width,first):
        from .models import TabCell
        from .drawing import clean
        out=[];x=1
        if width<=2:return out
        for item in model.items[first:]:
            if x>=width-1:break
            w=min(max(6,min(24,cells(item.title)+5)),width-1-x)
            if w<4 and out:break
            active,focused=item.id==model.active,item.id==model.focused
            suffix=(' *'if item.edited else'')+(' x'if item.closable else'')
            label=clip(clean(item.title),max(0,w-3-len(suffix)),True)
            text=clip(('>'if focused else' ')+('['if active else' ')+label+suffix+(']'if active else' '),w,True)
            out.append(TabCell(item.id,text,x,w,active,focused,item.disabled));x+=w
        return out
    def _tree_rows(self,model,height):
        preview=deepcopy(model);preview.expanded=set(self._expanded)
        rows=preview.visible();self._scroll=max(0,min(self._scroll,max(0,len(rows)-max(1,height))))
        return rows
    def preview_layout(self,model,width,height):
        if self._busy:raise DropError('reentrant')
        if type(width)is not int or type(height)is not int or not 0<=width<=65535 or not 0<=height<=4096:raise DropError('bounds')
        if not self._valid(model,width,height):
            preview=deepcopy(model)
            if isinstance(model,Tabs):
                cells=preview.layout(width)
                return DragLayout(first=preview.first,tabs=tuple(cells))
            rows=preview._reconcile(height)
            return DragLayout(scroll=preview.scroll,expanded=tuple(sorted(preview.expanded)),rows=tuple(rows))
        if isinstance(model,Tabs):return DragLayout(first=self._first,tabs=tuple(self._tab_cells(model,width,self._first)))
        rows=self._tree_rows(model,height)
        return DragLayout(scroll=self._scroll,expanded=tuple(sorted(self._expanded)),rows=tuple(rows))

    def pointer(self,model,pointer,options=None,allow=None):
        if self._busy:raise DropError('reentrant')
        p=pointer;o=_options(options)
        if p.action not in ('down','move','up','cancel')or any(type(v)is not int or not -1_000_000_000<=v<=1_000_000_000 for v in (p.x,p.y))or type(p.width)is not int or type(p.height)is not int or not 0<=p.width<=65535 or not 0<=p.height<=4096:raise DropError('pointer')
        if p.action=='cancel':self.cancel();return None
        if not self.enabled:
            if self.captured:self._reset('cancel')
            return None
        if p.action=='down':
            self._reset('')
            if not 0<=p.x<p.width or not 0<=p.y<p.height:return None
            preview=deepcopy(model)
            if isinstance(model,Tabs):
                if p.y:return None
                target=next((c for c in preview.layout(p.width)if c.start<=p.x<c.start+c.width and not c.disabled),None)
                id=target.id if target else''
            elif isinstance(model,Tree):
                rows=preview._reconcile(p.height);i=preview.scroll+p.y
                id=rows[i].id if i<len(rows)else''
            else:raise DropError('model')
            if not id or id in o.locked:return None
            self.phase='armed';self.source_id=id;self._revision=drag_revision(model);self._state_revision=_state_revision(model)
            self._x,self._y,self._width,self._height=p.x,p.y,p.width,p.height
            self._first=preview.first if isinstance(model,Tabs)else 0
            self._scroll=preview.scroll if isinstance(model,Tree)else 0
            self._expanded=set(preview.expanded)if isinstance(model,Tree)else set();self._pointer=p
            return None
        if not self._valid(model,p.width,p.height):return None
        self._pointer=p
        if max(abs(p.x-self._x),abs(p.y-self._y))>= (o.threshold or 2):self.phase='dragging'
        if self.phase=='dragging':
            raw=None;error='outside'
            if isinstance(model,Tabs):
                if o.auto_scroll and p.action=='move':
                    if p.x<=0:self._first=max(0,self._first-1)
                    elif p.x>=p.width-1:self._first=min(max(0,len(model.items)-1),self._first+1)
                target=next((c for c in self._tab_cells(model,p.width,self._first)if 0<=p.x<p.width and p.y==0 and c.start<=p.x<c.start+c.width),None)
                if target:raw=DropRequest(self.source_id,target.id,'after'if p.x-target.start>=target.width//2 else'before',self._revision)
            else:
                rows=self._tree_rows(model,p.height)
                if o.auto_scroll and p.action=='move':
                    if p.y<=0:self._scroll=max(0,self._scroll-1)
                    elif p.y>=p.height-1:self._scroll=min(max(0,len(rows)-max(1,p.height)),self._scroll+1)
                i=self._scroll+p.y
                if 0<=p.x<p.width and 0<=p.y<p.height and 0<=i<len(rows):
                    target=rows[i]
                    position='before'if p.x<=2+model.depth[target.id]*2 else'inside'if target.id in model.branches and p.x<p.width-2 else'after'
                    raw=DropRequest(self.source_id,target.id,position,self._revision)
            if raw:
                self._busy=True
                try:
                    request_drop(model,raw.source_id,raw.target_id,raw.position,o,allow);error=''
                except DropError as rejected:error=rejected.reason
                finally:self._busy=False
                if not self._valid(model,p.width,p.height):return None
            self._request=raw;self.target_id=raw.target_id if raw else'';self.position=raw.position if raw else''
            self.allowed=not error;self.reason=error
            if raw and not error and o.hover_expand and isinstance(model,Tree)and raw.position=='inside':self._expanded.add(raw.target_id)
        if p.action!='up':return None
        request=self._request if self.phase=='dragging'and self.allowed else None
        result='drop'if request else'reject'if self.phase=='dragging'else''
        self._reset(result);return request

    def draw(self,model,canvas,rect,*,focused=True,ascii=False):
        if self._busy:raise DropError('reentrant')
        for v in (rect.x,rect.y,rect.width,rect.height):
            if type(v)is not int or not 0<=v<=1_000_000_000:raise DropError('bounds')
        if rect.width>65535 or rect.height>4096:raise DropError('bounds')
        if not focused and self.captured:self._reset('cancel')
        self.render_key('|'.join(map(str,(rect.x,rect.y,rect.width,rect.height,canvas.palette.theme,canvas.palette.colors,canvas.surface_role,focused,ascii))))
        if not self._valid(model,rect.width,rect.height):
            model.draw(canvas,rect,focused=focused,ascii=ascii);return
        child=Canvas(rect.width,rect.height,canvas.palette,canvas.surface_role)
        if isinstance(model,Tabs):
            views=self._tab_cells(model,rect.width,self._first)
            if self._first:child.write(0,0,'<','hint',width=1)
            if self._first+len(views)<len(model.items)and rect.width:child.write(rect.width-1,0,'>','hint',width=1)
            for cell in views:
                role='disabled'if cell.disabled else'selection'if cell.active else'body'
                child.write(cell.start,0,' '*cell.width,role,focused=focused and cell.focused,width=cell.width)
                child.write(cell.start,0,cell.text,role,focused=focused and cell.focused,width=cell.width)
            target=next((c for c in views if c.id==self.target_id),None)
            marker_x=(target.start+(target.width-1 if self.position=='after'else 0))if target else max(0,min(rect.width-1,self._pointer.x))
            marker_y=0;marker='|'if ascii else'│'
        else:
            from .drawing import graphemes
            rows=self._tree_rows(model,rect.height)
            for y,n in enumerate(rows[self._scroll:self._scroll+rect.height]):
                selected=model.selected==n.id
                arrow=('v'if ascii else'▾')if n.id in self._expanded else('>'if ascii else'▸')
                arrow=arrow if n.id in model.branches else' '
                icon=n.ascii_icon if ascii else n.icon
                text='  '*model.depth[n.id]+arrow+' '+((icon+' ')if icon else'')+n.name
                if n.secondary:text+='  '+n.secondary
                if n.count is not None:text+=f' ({n.count})'
                gs=graphemes(text);skipped=0
                while gs and skipped<model.horizontal:skipped+=cells(gs.pop(0))
                child.write(0,y,('> 'if selected else'  ')+clip(''.join(gs),max(0,rect.width-2),True),'selection'if selected else'body',focused=focused and selected,width=rect.width)
            marker_x=0;marker_y=next((i-self._scroll for i,n in enumerate(rows)if n.id==self.target_id),max(0,min(rect.height-1,self._pointer.y)))
            marker={'before':'^'if ascii else'↑','after':'v'if ascii else'↓','inside':'+'if ascii else'↳'}.get(self.position,'!')
        if self.phase=='dragging'and 0<=marker_x<rect.width and 0<=marker_y<rect.height:
            from .drawing import color_contrast
            old=child.data[marker_y][marker_x].style
            semantic=child.palette.style('info'if self.allowed else'error')
            foreground=semantic.foreground
            if color_contrast(foreground,old.background)<4.5 and color_contrast(old.foreground,old.background)>color_contrast(foreground,old.background):foreground=old.foreground
            child.write_style(marker_x,marker_y,marker if self.allowed else'!',Style(foreground,old.background,True,False,True),width=1)
        canvas.blit(child,Rect(0,0,rect.width,rect.height),rect.x,rect.y)
