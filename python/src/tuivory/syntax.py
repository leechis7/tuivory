"""Optional original-UTF8 syntax analysis; no SQL execution or validation."""
from dataclasses import dataclass,field
from copy import deepcopy
from .drawing import graphemes
import json
from importlib.resources import files
_SYNTAX_UNICODE=json.loads(files(__package__).joinpath("syntax-unicode.json").read_text())
def _property(cp,name):
    ranges=_SYNTAX_UNICODE[name];lo=0;hi=len(ranges)
    while lo<hi:
        mid=(lo+hi)//2;a,b=ranges[mid]
        if cp<a:hi=mid
        elif cp>b:lo=mid+1
        else:return True
    return False
def _syntax_text(text,limit):
    if not isinstance(text,str)or len(text.encode('utf-8'))>limit:raise ValueError('invalid syntax source/metadata')
    return text

@dataclass
class SyntaxToken:
    start:int
    end:int
    role:str
@dataclass
class SyntaxRequest:
    language:str=''
    dialect:str=''
@dataclass
class SyntaxAnalysis:
    source:str
    language:str=''
    dialect:str=''
    tokens:list[SyntaxToken]=field(default_factory=list)
    def validate(self,text):
        _syntax_text(self.source,1_000_000);_syntax_text(self.language,128);_syntax_text(self.dialect,128)
        if not isinstance(self.tokens,(list,tuple))or len(self.tokens)>1_000_000:raise ValueError('invalid syntax tokens')
        if self.source!=text:raise ValueError('stale syntax source')
        boundaries={0};offset=0
        for ch in text:offset+=len(ch.encode());boundaries.add(offset)
        end=0
        for token in self.tokens:
            _syntax_text(token.role,128)
            if type(token.start)is not int or type(token.end)is not int or token.start<end or token.end<=token.start or token.start not in boundaries or token.end not in boundaries:raise ValueError('unordered, overlapping or invalid UTF-8 syntax range')
            end=token.end
        return self

def syntax_role_style(role):
    family={'keyword':'keyword','function':'function','macro':'function','attribute':'function','type':'type','string':'string','character':'string','number':'number','constant':'number','comment':'comment','directive':'comment','parameter':'parameter','lifetime':'parameter'}.get(role)
    return 'syntax.'+family if family else 'body'
def syntax_palette_role(role):return {'keyword':'info','function':'success','type':'header','string':'warning','number':'edited','comment':'hint','parameter':'error'}.get(role.removeprefix('syntax.'),'body')

def _ident_start(c):return c=='_'or _property(ord(c),'alphabetic')
def _ident_part(c):return _ident_start(c)or _property(ord(c),'number')or c in '$#'or any(a<=ord(c)<=b for a,b in [(0x300,0x36f),(0x1ab0,0x1aff),(0x1dc0,0x1dff),(0x20d0,0x20ff),(0xfe20,0xfe2f)])
class SQLAnalyzer:
    def __init__(self):
        vocabulary=json.loads(files(__package__).joinpath('sql-syntax-words.json').read_text());self._words={k:set(v)for k,v in vocabulary.items()}
    def analyze_syntax(self,text,request=None):
        _syntax_text(text,1_000_000);request=request or SyntaxRequest();language=(_syntax_text(request.language,128)or'sql').lower();dialect=(_syntax_text(request.dialect,128)or'oracle').lower()
        if language not in ('sql','plsql')or dialect!='oracle':raise ValueError('unsupported syntax language/dialect')
        words=self._words
        n=len(text);i=0;raw=[]
        def quoted(at,quote):
            at+=1
            while at<n:
                if text[at]==quote:
                    at+=1
                    if at<n and text[at]==quote:at+=1;continue
                    return at
                at+=1
            return at
        while i<n:
            start=i;c=text[i]
            if _property(ord(c),'whitespace'):i+=1;continue
            role='punctuation'
            prefix=2 if i+2<n and text[i:i+2].lower()=="q'"else 3 if i+3<n and text[i:i+3].lower()=="nq'"else 0
            if text.startswith('--',i):
                role='comment';i+=2
                while i<n and text[i]not in '\r\n':i+=1
            elif text.startswith('/*',i):
                role='comment';end=text.find('*/',i+2);i=n if end<0 else end+2
            elif prefix:
                role='string';i+=prefix
                if i<n:
                    opening=text[i]
                    if not _property(ord(opening),'whitespace'):
                        closing={'[':']','{':'}','(':')','<':'>'}.get(opening,opening);end=text.find(closing+"'",i+1);i=n if end<0 else end+2
                    else:i=start+1;role='identifier'
            elif c=="'"or c in 'nN'and i+1<n and text[i+1]=="'":role='string';i=quoted(i+(c!="'"),"'")
            elif c=='"':role='identifier';i=quoted(i,'"')
            elif c==':'and i+1<n and(_ident_start(text[i+1])or text[i+1]in'0123456789"'):
                role='parameter';i+=1
                if text[i]=='"':i=quoted(i,'"')
                else:
                    while i<n and _ident_part(text[i]):i+=1
            elif text.startswith('..',i):role='operator';i+=2
            elif c in '0123456789'or c=='.'and i+1<n and text[i+1]in'0123456789':
                role='number'
                while i<n and text[i]in'0123456789':i+=1
                if i<n and text[i]=='.'and not text.startswith('..',i):
                    i+=1
                    while i<n and text[i]in'0123456789':i+=1
                if i<n and text[i]in'eE':
                    end=i+1
                    if end<n and text[end]in'+-':end+=1
                    first=end
                    while end<n and text[end]in'0123456789':end+=1
                    if end>first:i=end
                if i<n and text[i]in'fFdD':i+=1
            elif _ident_start(c):
                i+=1
                while i<n and _ident_part(text[i]):i+=1
                word=text[start:i].translate(str.maketrans('abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'));role='identifier'
                for group,kind in [('types','type'),('functions','function'),('keywords','keyword')]:
                    if word in words[group]:role=kind;break
            else:
                i+=1
                if c in '+-*/%=<>!|:^~':
                    role='operator'
                    if i<n and text[start:i+1]in(':=','=>','<=','>=','!=','<>','||','**'):i+=1
            raw.append((start,i,role))
        offsets=[0]
        for ch in text:offsets.append(offsets[-1]+len(ch.encode()))
        aligned=[];at=0;which=0;previous=None
        for cluster in graphemes(text):
            end=at+len(cluster)
            while which<len(raw)and raw[which][1]<=at:which+=1
            if which<len(raw)and raw[which][0]<end:
                if previous==which and aligned and aligned[-1].end==offsets[at]:aligned[-1].end=offsets[end]
                else:aligned.append(SyntaxToken(offsets[at],offsets[end],raw[which][2]))
                previous=which
            else:previous=None
            at=end
        return SyntaxAnalysis(text,language,dialect,aligned)

def syntax_style(palette,role,surface='editor'):
    from .drawing import Style,color_contrast
    kind=role.removeprefix('syntax.');base=palette.text_on_surface(syntax_palette_role(kind),surface)
    if kind not in ('keyword','function','type','string','number','comment','parameter'):return base
    if palette.theme=='blackwhite':return Style(base.foreground,base.background,False,False,kind in ('keyword','parameter'),kind=='comment')
    colors=[v[k]for v in palette.roles.values()for k in ('foreground','background')]
    dark_eight=palette.style('surface').background=='0'and palette.style('warning').foreground=='3'and all(not c.startswith('#')and 0<=int(c)<=7 for c in colors)
    if dark_eight:
        foreground='3'if kind in ('keyword','function','string','parameter')else'7'
        if color_contrast(foreground,base.background)<4.5 and color_contrast(base.foreground,base.background)>color_contrast(foreground,base.background):foreground=base.foreground
        return Style(foreground,base.background,kind in ('keyword','number'),False,kind in ('keyword','type','parameter'),kind in ('string','comment'))
    return base

@dataclass
class _SyntaxBinding:
    analyzer:object=None
    request:SyntaxRequest=field(default_factory=SyntaxRequest)
    source:str=''
    dirty:bool=False
    error:str|None=None
    refreshing:bool=False

def _apply(document,analysis):
    from .documents import DocumentSpan
    if document.buffer.secret:raise ValueError('syntax analysis unavailable for secret buffers')
    analysis.validate(document.buffer.value)
    document.set_byte_syntax([DocumentSpan(t.start,t.end,syntax_role_style(t.role))for t in analysis.tokens])

def set_analysis(document,analysis):
    if document._binding and document._binding.refreshing:raise ValueError("recursive syntax analysis")
    _apply(document,analysis);document._binding=_SyntaxBinding(source=document.buffer.value)

def _invoke(analyzer,text,request):
    return analyzer.analyze_syntax(text,deepcopy(request))if hasattr(analyzer,'analyze_syntax')else analyzer(text,deepcopy(request))

def set_analyzer(document,analyzer,request=None):
    if document._binding and document._binding.refreshing:raise ValueError("recursive syntax analysis")
    if analyzer is None:document._binding=None;document._syntax=[];document._syntax_source=document.buffer.value;return
    if document.buffer.secret:raise ValueError('syntax analysis unavailable for secret buffers')
    request=deepcopy(request or SyntaxRequest());_syntax_text(request.language,128);_syntax_text(request.dialect,128);analysis=_invoke(analyzer,document.buffer.value,request);_apply(document,analysis)
    document._binding=_SyntaxBinding(analyzer,request,document.buffer.value)

def refresh(document):
    binding=document._binding
    if document.buffer.secret:
        if binding:binding.source='';binding.dirty=True
        document._syntax=[];return
    if binding is None:return
    if binding.refreshing:raise ValueError('recursive syntax analysis')
    if binding.source==document.buffer.value and not binding.dirty:
        if binding.error:raise ValueError(binding.error)
        return
    source=document.buffer.value;binding.refreshing=True
    try:
        if binding.analyzer is not None:_apply(document,_invoke(binding.analyzer,source,binding.request))
        else:document._syntax=[];document._syntax_source=source
    except Exception as error:
        document._syntax=[];document._syntax_source=document.buffer.value;binding.error=str(error)or type(error).__name__
        raise
    else:binding.error=None
    finally:binding.source=source;binding.dirty=False;binding.refreshing=False
