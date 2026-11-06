"""Example host supplies contents, global shortcuts and chip-removal approval."""
from . import (Rect, SpacingTokens, StackItem, stack_rects, Badge, Chip,
               ControlState, Shortcut, Help)


class LayoutDemo:
    def __init__(self,en=False):
        self.en=en;self.density='auto';self.active=True;self.hits=[];self.status=''
        self.filter=Chip('filter',self.word('최근','Recent'),removable=True)
        self.readonly=Chip('fixed',self.word('읽기 전용','Read only'),ControlState(read_only=True),True)
        self.disabled=Chip('off',self.word('비활성','Disabled'),ControlState(disabled=True),True)

    def word(self,ko,en):
        return en if self.en else ko

    def draw(self,c,area,*,ascii=False):
        self.hits=[]
        tokens=SpacingTokens.for_width(self.density,area.width)
        layout=stack_rects(Rect(area.x,area.y,area.width,max(0,area.height-1)),
                           [StackItem('badges',16,20,0),StackItem('support',24,40,1)],tokens)
        badges=[Badge(label=self.word('항목','Items'),count=123),
                Badge(label=self.word('선택','Selected'),count=0,state=ControlState(selected=True)),
                Badge(label=self.word('비활성','Disabled'),state=ControlState(disabled=True))]
        for named in layout.rects:
            if not named.rect.width or not named.rect.height:
                continue
            inner=c.panel(named.rect,self.word('배지','Badges')if named.id=='badges'else self.word('칩·단축키','Chips and shortcuts'),False,ascii)
            y=inner.y
            if named.id=='badges':
                for b in badges:
                    if y>=inner.y+inner.height:break
                    b.draw(c,Rect(inner.x,y,inner.width,1));y+=1+tokens.control_gap
            else:
                for chip in ([self.filter]if self.active else[])+[self.readonly,self.disabled]:
                    if y>=inner.y+inner.height:break
                    r=Rect(inner.x,y,inner.width,1);chip.draw(c,r)
                    for span in chip.line(inner.width).spans:
                        self.hits.append((Rect(inner.x+span.start,y,span.width,1),chip,span.disabled))
                    y+=1+tokens.control_gap
                Help([Shortcut('d',self.word('간격 변경','Change density'),10),
                      Shortcut('x',self.word('필터 제거','Remove filter'),5,not self.active),
                      Shortcut('r',self.word('사용 불가','Unavailable'),0,True)]).draw(c,Rect(inner.x,y,inner.width,max(0,inner.y+inner.height-y)))
        label=self.word('자동','auto')if self.density=='auto'else self.word('촘촘','compact')if self.density=='compact'else self.word('여유','comfortable')
        text=self.status or self.word('밀도: ','Density: ')+label+self.word(' | 숨긴 패널: ',' | Hidden panes: ')+str(len(layout.hidden))
        if area.height:c.write(area.x,area.y+area.height-1,text,'hint',width=area.width)

    def apply(self,event):
        if event.kind=='remove' and event.id=='filter' and self.active:
            self.active=False;self.hits=[];self.status=self.word('필터를 제거했습니다.','Filter removed.')

    def handle(self,action,height=10,text=''):
        command=text if action=='insert'else action
        if command in ('x','activate'):
            self.apply(self.filter.request_remove())
        elif command=='d':
            self.density='compact'if self.density=='comfortable'else'comfortable'
            self.hits=[];self.status=self.word('밀도: 촘촘','Density: compact')if self.density=='compact'else self.word('밀도: 여유','Density: comfortable')

    def pointer(self,x,y,button):
        if button!=0:return
        for rect,chip,disabled in self.hits:
            if rect.contains(x,y):
                if not disabled:self.apply(chip.request_remove())
                return
