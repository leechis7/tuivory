"""Host-selected content, demo keys and search matches; no external I/O."""
from . import TextDocument,DocumentSpan,DocumentRange,Rect,graphemes,SQLAnalyzer
class DocumentDemo:
    def __init__(self,en=False,ascii=False,syntax=False):
        self.en=en;self.area=Rect();self.document=TextDocument.editor(self.word('문서 편집 예제\n한글 é 界 문장을 좁은 화면에서도 확인합니다.\n[error]태그도 원문 그대로입니다.[/]\n마지막 줄입니다.','Document viewer/editor\n'+('Literal ASCII text with a long wrapped line.'if ascii else'Unicode é 界 with a long wrapped line.')+'\n[error]Tags remain literal text.[/]\nFinal line.'));self.document.wrap=True;self.document.buffer.select(0,0);self.document.set_syntax([DocumentSpan(0,2,'info')])
        self.syntax_demo=syntax;self.syntax_enabled=False;self.syntax_failed=False;self.syntax_calls=0;self.analyzer=SQLAnalyzer()
        if syntax:
            value="SELECT COUNT(*) AS total,\n       CAST(:id AS NUMBER), NVL(:name, '"+("sample"if en and ascii else"é 界"if en else"한글 é 界")+"')\nFROM sample_table\nWHERE id >= 1.2e-3D; -- "+self.word('실행하지 않는 견본','Example only')
            self.document.set_text(value);self.document.buffer.select(0,0);self.enable_syntax()
    def analyze(self,text,request):
        self.syntax_calls+=1
        if self.syntax_failed:raise ValueError('sample analysis failure')
        return self.analyzer.analyze_syntax(text,request)
    def enable_syntax(self):
        self.syntax_failed=False;self.document.set_syntax_analyzer(self.analyze);self.syntax_enabled=True
    def word(self,ko,en):return en if self.en else ko
    def draw(self,c,area,*,ascii=False):
        self.area=Rect(area.x,area.y,area.width,max(0,area.height-2));d=self.document;d.draw(c,self.area,ascii=ascii)
        status=(self.word('보기','Viewer')if d.buffer.read_only else self.word('편집','Editor'))+' | '+self.word('줄바꿈 ','Wrap ')+('on'if d.wrap else'off')+' | '+self.word('줄 번호 ','Numbers ')+('on'if d.line_numbers else'off')+' | '+self.word('비활성 ','Disabled ')+('on'if d.buffer.disabled else'off')
        if self.syntax_demo:
            status=self.word('구문 ','Syntax ')+('error'if d.syntax_error else'on'if self.syntax_enabled else'off')+' | '+self.word('분석 ','Calls ')+str(self.syntax_calls)+' | '+status
        if area.height>=2:c.write(area.x,area.y+area.height-2,status,'hint',width=area.width)
        if area.height:c.write(area.x,area.y+area.height-1,(self.word('a 구문 전환 | f 실패 | w 줄바꿈 | x 비활성','a analyzer | f failure | w wrap | x disabled')if self.syntax_demo else self.word('w 줄바꿈 | n 번호 | v 보기 | s 검색 | x 비활성 | m 마크업','w wrap | n numbers | v viewer | s search | x disabled | m markup')),'hint',width=area.width)
    def handle(self,action,height=10,text=''):
        command=text if action=='insert'else action;d=self.document
        if self.syntax_demo and command=='a':
            if self.syntax_enabled:d.set_syntax_analyzer(None);self.syntax_enabled=False
            else:self.enable_syntax()
        elif self.syntax_demo and command=='f':
            if d.buffer.read_only or d.buffer.disabled:return
            if self.syntax_failed:self.enable_syntax()
            elif self.syntax_enabled:self.syntax_failed=True;d.handle('insert',' ')
        elif command=='w':d.wrap=not d.wrap;d.reveal_cursor()
        elif command=='n':d.line_numbers=not d.line_numbers;d.reveal_cursor()
        elif command=='v':d.buffer.read_only=not d.buffer.read_only
        elif command=='x':d.buffer.disabled=not d.buffer.disabled
        elif command=='s':d.set_search_matches([]if d.search_matches else[DocumentRange(0,min(2,len(graphemes(d.buffer.value))))])
        elif command=='m':
            self.syntax_enabled=False;d.set_markup(self.word('[info]명시적 마크업[/]\n[[error]는 리터럴입니다.','[info]Explicit markup[/]\n[[error] stays literal.'));d.buffer.select(0,0)
        else:d.handle('newline'if action=='activate'else action,text)
    def pointer(self,x,y,button):
        if button==0 and self.area.contains(x,y):self.document.click(x-self.area.x,y-self.area.y,self.area.width,self.area.height)
