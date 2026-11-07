"""Optional visual-only popup shadows; hosts own anchors, visibility and actions."""
from dataclasses import dataclass,field
from .drawing import Canvas,Rect,Style,color_rgb

def _number(value,limit=1_000_000):
    if type(value)is not int or not 0<=value<=limit:raise ValueError('invalid popup bounds/options')
def _rect(r):
    for v in (r.x,r.y):_number(v,1_000_000_000)
    for v in (r.width,r.height):_number(v)

@dataclass(frozen=True)
class PopupLayout:
    bounds:Rect=field(default_factory=Rect)
    card:Rect=field(default_factory=Rect)
    shadow:Rect=field(default_factory=Rect)
    def shadow_regions(self):
        s,c=self.shadow,self.card;sr,sb=s.x+s.width,s.y+s.height;cr,cb=c.x+c.width,c.y+c.height;x=max(s.x,cr);y=max(s.y,cb)
        return [Rect(x,s.y,max(0,sr-x),max(0,min(sb,cb)-s.y)),Rect(s.x,y,s.width,max(0,sb-y))]
    def hit(self,x,y):return self.card.contains(x,y)

@dataclass(frozen=True)
class ShadowOptions:
    mode:str='off'
    offset_x:int=0
    offset_y:int=0
    def _offsets(self):
        if self.mode not in ('off','auto','solid','dim'):raise ValueError('invalid shadow mode')
        _number(self.offset_x);_number(self.offset_y)
        return (0,0)if self.mode=='off'else(1,1)if not self.offset_x and not self.offset_y else(self.offset_x,self.offset_y)
    def _layout(self,bounds):
        dx,dy=self._offsets()
        if not bounds.width or not bounds.height:return PopupLayout(bounds,bounds)
        dx=min(dx,bounds.width-1);dy=min(dy,bounds.height-1)
        card=Rect(bounds.x,bounds.y,bounds.width-dx,bounds.height-dy);shadow=Rect()
        if dx or dy:
            caps=self.mode in ('auto','solid')and dy>0
            shadow=Rect(bounds.x+dx,bounds.y+dy-int(caps),card.width,card.height+int(caps))
        return PopupLayout(bounds,card,shadow)
    def layout(self,bounds):_rect(bounds);return self._layout(bounds)

def popup_placement(anchor:Rect,viewport:Rect,width:int,height:int,options:ShadowOptions|None=None)->PopupLayout:
    _rect(anchor);_rect(viewport);_number(width);_number(height);o=options or ShadowOptions();dx,dy=o._offsets()
    w,h=(min(width+dx,viewport.width),min(height+dy,viewport.height))if width and height else(0,0)
    mx,my=viewport.x+viewport.width-w,viewport.y+viewport.height-h;x=max(viewport.x,min(anchor.x,mx));y=anchor.y+anchor.height
    if y>my:y=max(0,anchor.y-h)
    return o._layout(Rect(x,max(viewport.y,min(y,my)),w,h))

def _shade(backdrop,has_rgb,has_256):
    r,g,b=color_rgb(backdrop);maximum=max(r,g,b)
    if maximum<=16:return '#404040'if has_rgb else'238'if has_256 else'7'
    factor=2 if maximum<=96 else 4
    if has_rgb:return '#%02x%02x%02x'%(r*factor//5,g*factor//5,b*factor//5)
    if has_256:return str(232+max(0,min(23,((r+g+b)*factor//15-3)//10)))
    return '0'

def _paint_shadow(canvas,region,layout,options,ascii,has_rgb,has_256):
    left=max(0,region.x);right=min(canvas.width,region.x+region.width);top=max(0,region.y);bottom=min(canvas.height,region.y+region.height)
    if left>=right or top>=bottom:return
    canvas.clear_cursor(Rect(left,top,right-left,bottom-top))
    for y in range(top,bottom):
        backgrounds=[]
        for x in range(left,right):
            c=canvas.data[y][x];backgrounds.append(canvas.data[y][c.owner].style.background if c.continuation else c.style.background)
        if canvas.data[y][left].continuation:canvas.write_style(left,y," ",canvas.data[y][left].style,width=1)
        end=right-1
        cell=canvas.data[y][end];start=cell.owner if cell.continuation else end
        if end+1<canvas.width and canvas.data[y][end+1].continuation and canvas.data[y][end+1].owner==start:canvas.write_style(end,y," ",cell.style,width=1)
        for x in range(left,right):
            old=canvas.data[y][x]
            if options.mode=='dim':
                s=old.style;old.style=Style(s.foreground,s.background,s.bold,True,s.underline)
                continue
            bg=backgrounds[x-left];shade='0'if options.mode=='solid'else _shade(bg,has_rgb,has_256);symbol=' ';style=Style(shade,shade)
            if ascii:symbol='.';style=Style(shade,bg)
            elif layout.shadow.height>layout.card.height:
                if y==layout.shadow.y:symbol='▄';style=Style(shade,bg)
                elif y==layout.shadow.y+layout.shadow.height-1:symbol='▀';style=Style(shade,bg)
            canvas.write_style(x,y,symbol,style,width=1)

@dataclass
class Shadow:
    options:ShadowOptions=field(default_factory=ShadowOptions)
    def draw(self,canvas:Canvas,bounds:Rect,painter,*,ascii=False)->PopupLayout:
        _rect(bounds);self.options._offsets()
        x=max(0,bounds.x);y=max(0,bounds.y);r=min(canvas.width,bounds.x+bounds.width);b=min(canvas.height,bounds.y+bounds.height)
        clipped=Rect(min(x,canvas.width),min(y,canvas.height),max(0,r-x),max(0,b-y));layout=self.options._layout(clipped)
        working=Canvas(canvas.width,canvas.height,canvas.palette,canvas.surface_role);working.blit(canvas,Rect(0,0,canvas.width,canvas.height),0,0)
        colors=[v[k]for v in canvas.palette.roles.values()for k in ('foreground','background')];has_rgb=any(c.startswith('#')for c in colors);has_256=any(not c.startswith('#')and int(c)>=16 for c in colors)
        if self.options.mode!='off':
            for region in layout.shadow_regions():_paint_shadow(working,region,layout,self.options,ascii,has_rgb,has_256)
        card=layout.card;child=Canvas(card.width,card.height,canvas.palette,canvas.surface_role);child.blit(working,card,0,0);child.clear_cursor();painter(child)
        working.blit(child,Rect(0,0,card.width,card.height),card.x,card.y);canvas.blit(working,Rect(0,0,canvas.width,canvas.height),0,0)
        return layout
