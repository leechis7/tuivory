"""Literal document viewing/editing with source ranges and optional explicit markup."""
from dataclasses import dataclass,field
from .drawing import Rect,Style,graphemes,cells,clean,clip
from .editing import Text
from .models import Event
from . import syntax as _syntax

TEXT_ROLES=frozenset(('body','hint','info','success','warning','error','header','field','selection','button','disabled','edited','syntax.keyword','syntax.function','syntax.type','syntax.string','syntax.number','syntax.comment','syntax.parameter'))
SYNTAX_PALETTE={'keyword':'info','function':'success','type':'header','string':'warning','number':'edited','comment':'hint','parameter':'error'}
@dataclass(frozen=True)
class DocumentSpan:
    start:int
    end:int
    role:str='body'
@dataclass(frozen=True)
class DocumentRange:
    start:int
    end:int
@dataclass(frozen=True)
class DocumentGlyph:
    x:int
    text:str
    index:int
    width:int
    role:str='body'
    cursor:bool=False
@dataclass
class DocumentLine:
    number:int
    prefix:str
    glyphs:list[DocumentGlyph]=field(default_factory=list)
    hits:list[tuple[int,int]]=field(default_factory=list)

def _valid_text(text):
    if not isinstance(text,str)or len(text.encode('utf-8'))>1_000_000:raise ValueError('invalid document source')
    return text

def parse_markup(markup):
    _valid_text(markup);out=[];changes=[(0,'body')];stack=['body'];at=size=0
    while at<len(markup):
        if markup.startswith('[[',at):out.append('[');size+=1;at+=2;continue
        if markup[at]=='[':
            end=markup.find(']',at)
            if end<0:raise ValueError('unbalanced markup')
            tag=markup[at+1:end]
            if tag=='/':
                if len(stack)==1:raise ValueError('unbalanced markup')
                stack.pop()
            else:
                if tag not in TEXT_ROLES:raise ValueError('unknown markup role')
                stack.append(tag)
            changes.append((size,stack[-1]));at=end+1;continue
        end=markup.find('[',at)
        if end<0:end=len(markup)
        out.append(markup[at:end]);size+=end-at;at=end
    if len(stack)!=1:raise ValueError('unbalanced markup')
    source=''.join(out);spans=[];which=offset=0
    for index,g in enumerate(graphemes(source)):
        while which+1<len(changes)and changes[which+1][0]<=offset:which+=1
        role=changes[which][1]
        if role!='body':
            if spans and spans[-1].end==index and spans[-1].role==role:spans[-1]=DocumentSpan(spans[-1].start,index+1,role)
            else:spans.append(DocumentSpan(index,index+1,role))
        offset+=len(g)
    return source,spans

class TextDocument:
    def __init__(self,text='',*,read_only=False):
        self.buffer=Text(_valid_text(text),read_only=read_only);self.wrap=False;self.line_numbers=not read_only
        self.scroll_x=self.scroll_y=0;self._syntax=[];self._search=[];self._syntax_source=self._search_source=text
        self._hits=[];self._last=None;self._height=0;self._reveal=not read_only;self._binding=None
    @classmethod
    def editor(cls,text=''):return cls(text)
    @classmethod
    def viewer(cls,text=''):return cls(text,read_only=True)
    def __repr__(self):return f'TextDocument({self.buffer!r})'
    @property
    def syntax(self):return list(self._syntax)
    @property
    def search_matches(self):return list(self._search)
    def set_text(self,text):
        text=_valid_text(text);readonly=self.buffer.read_only;secret=self.buffer.secret;disabled=self.buffer.disabled
        self.buffer=Text(text,read_only=readonly,secret=secret);self.buffer.disabled=disabled
        self._syntax=[];self._search=[];self._syntax_source=self._search_source=text;self.scroll_x=self.scroll_y=0;self._hits=[];self._last=None;self._reveal=not readonly
        self._refresh_syntax_safe()
    def _ranges(self,ranges,syntax=False):
        n=len(graphemes(_valid_text(self.buffer.value)));out=[]
        for r in ranges:
            if type(r.start)is not int or type(r.end)is not int or not 0<=r.start<=r.end<=n:raise ValueError('invalid document grapheme range')
            if syntax and r.role not in TEXT_ROLES:raise ValueError('unknown document role')
            if len(out)>=1_000_000:raise ValueError('too many document ranges')
            out.append(DocumentSpan(r.start,r.end,r.role)if syntax else DocumentRange(r.start,r.end))
        return out
    def set_syntax(self,spans):self._syntax=self._ranges(spans,True);self._syntax_source=self.buffer.value
    def set_search_matches(self,matches):self._search=self._ranges(matches);self._search_source=self.buffer.value
    def set_byte_syntax(self,spans):
        offsets={0:0};offset=0
        for i,g in enumerate(graphemes(self.buffer.value),1):offset+=len(g.encode());offsets[offset]=i
        converted=[]
        for s in spans:
            if type(s.start)is not int or type(s.end)is not int or s.start not in offsets or s.end not in offsets:raise ValueError('offset splits grapheme or outside text')
            converted.append(DocumentSpan(offsets[s.start],offsets[s.end],s.role))
        self.set_syntax(converted)
    def set_markup(self,markup):
        source,spans=parse_markup(markup);self.set_syntax_analyzer(None);self.set_text(source);self.set_syntax(spans)
    def set_syntax_analysis(self,analysis):_syntax.set_analysis(self,analysis)
    def set_syntax_analyzer(self,analyzer,request=None):_syntax.set_analyzer(self,analyzer,request)
    def refresh_syntax(self):_syntax.refresh(self)
    @property
    def syntax_error(self):return self._binding.error if self._binding and not self.buffer.secret else None
    def _refresh_syntax_safe(self):
        try:self.refresh_syntax()
        except Exception:pass
    def reveal_cursor(self):self._reveal=True
    def _scroll_valid(self):
        if any(type(v)is not int or not 0<=v<=1_000_000 for v in (self.scroll_x,self.scroll_y)):raise ValueError('invalid document scroll position')
    def handle(self,action,text=''):
        self._scroll_valid()
        if self.buffer.disabled:return Event()
        step=max(1,self._height)
        if action in ('page_up','page_down','scroll_up','scroll_down','scroll_left','scroll_right'):
            if action=='page_up':self.scroll_y=max(0,self.scroll_y-step)
            elif action=='page_down':self.scroll_y=min(1_000_000,self.scroll_y+step)
            elif action=='scroll_up':self.scroll_y=max(0,self.scroll_y-1)
            elif action=='scroll_down':self.scroll_y=min(1_000_000,self.scroll_y+1)
            elif action=='scroll_left':self.scroll_x=max(0,self.scroll_x-4)
            else:self.scroll_x=min(1_000_000,self.scroll_x+4)
            self._reveal=False;return Event('scroll')
        if action in ('insert','paste','newline')and not self.buffer.read_only:
            addition=_valid_text('\n'if action=='newline'else text).replace('\r\n','\n').replace('\r','\n')
            addition=''.join(' 'if c=='\t'else c for c in addition if ord(c)>=32 and not 127<=ord(c)<160 or c=='\t'or c=='\n'and self.buffer.multiline)
            lo,hi=self.buffer.selection_bytes()
            if len(self.buffer.value.encode())-(hi-lo)+len(addition.encode())>1_000_000:raise ValueError('document source exceeds limit')
        e=self.buffer.handle(action,text)
        if e.kind in ('select','change','cut'):self._reveal=True
        self._refresh_syntax_safe()
        return e
    def layout(self,width,height):
        self._scroll_valid()
        if any(type(v)is not int or not 0<=v<=1_000_000 for v in (width,height)):raise ValueError('invalid document dimensions')
        _valid_text(self.buffer.value);self._refresh_syntax_safe();self._height=height;self._hits=[]
        if not width or not height:return []
        self.buffer.select(self.buffer.anchor,self.buffer.cursor)
        source=self.buffer.value
        if source!=self._syntax_source:self._syntax=[];self._syntax_source=source
        if source!=self._search_source:self._search=[];self._search_source=source
        raw=graphemes(source);shown=['*']*len(raw)if self.buffer.secret else raw
        lo,hi=sorted((self.buffer.anchor,self.buffer.cursor));roles=['body']*len(shown)
        if not self.buffer.secret:
            for s in self._syntax:
                for i in range(s.start,min(s.end,len(roles))):roles[i]=s.role
            for s in self._search:
                for i in range(s.start,min(s.end,len(roles))):roles[i]='edited'
        for i in range(lo,hi):roles[i]='selection'
        if self.buffer.disabled:roles=['disabled']*len(shown)
        logical=[([],0)];number=1
        for i,g in enumerate(shown):
            if g in ('\r','\n','\r\n'):logical[-1]=(logical[-1][0],i);logical.append(([],i+1))
            else:logical[-1][0].append((i,' 'if any(ord(c)<32 or 127<=ord(c)<160 for c in g)else g));logical[-1]=(logical[-1][0],i+1)
        signature=(source,self.buffer.cursor,self.buffer.anchor)
        reveal=self._reveal or self._last!=signature and not self.buffer.read_only
        # Keep the entire actual cursor glyph visible; never substitute a pipe.
        if reveal and not self.wrap:
            for number,(items,end)in enumerate(logical,1):
                start=items[0][0]if items else end
                if start<=self.buffer.cursor<=end:
                    prefix=cells(str(number)+' ')if self.line_numbers else 0;available=max(1,width-prefix)
                    col=sum(cells(g)for i,g in items if i<self.buffer.cursor);cw=next((max(1,cells(g))for i,g in items if i==self.buffer.cursor),1)
                    self.scroll_x=max(0,min(self.scroll_x,col),col+min(cw,available)-available);break
        self.scroll_x=max(0,min(self.scroll_x,sum(cells(g)for g in shown)))
        rows=[]
        for number,(items,end)in enumerate(logical,1):
            prefix=clip(str(number)+' ',width)if self.line_numbers else'';pw=cells(prefix);available=max(0,width-pw)
            groups=[[]];used=0
            for i,g in items:
                w=cells(g)
                if self.wrap and groups[-1]and used+w>available:groups.append([]);used=0
                groups[-1].append((i,g));used+=w
            if self.wrap and groups[-1]and used>=available and end==self.buffer.cursor and not self.buffer.read_only:groups.append([])
            for segment,group in enumerate(groups):
                x=pw;glyphs=[];start=group[0][0]if group else end;hits=[(pw,start)]
                for i,g in group:
                    w=cells(g);local=x-(0 if self.wrap else self.scroll_x);hits.append((local,i))
                    if local>=pw and local+w<=width:glyphs.append(DocumentGlyph(local,g,i,w,roles[i],i==self.buffer.cursor))
                    x+=w
                finish=group[-1][0]+1 if group else end;local=x-(0 if self.wrap else self.scroll_x)
                hits.append((local,finish))
                if finish==self.buffer.cursor and local>=pw and local<width and(segment==len(groups)-1 or self.buffer.cursor<end):glyphs.append(DocumentGlyph(local,' ',finish,1,'disabled'if self.buffer.disabled else'body',True))
                rows.append(DocumentLine(number,prefix,glyphs,hits))
        if reveal:
            cursor_rows=[i for i,row in enumerate(rows)if any(g.cursor for g in row.glyphs)]
            if cursor_rows:
                at=cursor_rows[-1];self.scroll_y=max(0,min(self.scroll_y,at),at-height+1)
        self.scroll_y=max(0,min(self.scroll_y,max(0,len(rows)-height)));visible=rows[self.scroll_y:self.scroll_y+height]
        self._hits=[row.hits for row in visible];self._last=signature;self._reveal=False
        return visible
    def draw(self,canvas,bounds,*,focused=True,ascii=False):
        for v,limit in [(bounds.x,1_000_000_000),(bounds.y,1_000_000_000),(bounds.width,1_000_000),(bounds.height,1_000_000)]:
            if type(v)is not int or not 0<=v<=limit:raise ValueError('invalid document bounds')
        role=canvas.surface_role if self.buffer.read_only else'editor';canvas.fill(bounds,role);rows=self.layout(bounds.width,bounds.height);cursor=None
        for y,row in enumerate(rows):
            canvas.write_style(bounds.x,bounds.y+y,row.prefix,canvas.palette.text_on_surface('disabled'if self.buffer.disabled else'hint',role),width=bounds.width)
            for g in row.glyphs:
                if g.role.startswith('syntax.'):
                    s=_syntax.syntax_style(canvas.palette,g.role,role)
                elif g.role in ('selection','edited','field','button','header'):s=canvas.palette.style(g.role)
                else:s=canvas.palette.text_on_surface(g.role,role)
                canvas.write_style(bounds.x+g.x,bounds.y+y,g.text,s,width=g.width)
                if g.cursor:cursor=(bounds.x+g.x,bounds.y+y,g.width)
        if focused and not self.buffer.read_only and not self.buffer.disabled and cursor:canvas.set_cursor(*cursor)
    def click(self,x,y,width,height,*,extend=False):
        if self.buffer.disabled or type(x)is not int or type(y)is not int or not 0<=x<width or not 0<=y<height:return Event()
        self.layout(width,height)
        if not self._hits:return Event()
        row=self._hits[min(y,len(self._hits)-1)];at=row[0][1]
        for column,index in row:
            if column<=x:at=index
        self.buffer.select(self.buffer.anchor if extend else at,at);self._reveal=True;return Event('select')
