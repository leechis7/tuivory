"""Application-owned focus, drop approval and pointer capture routing."""
from . import Tree, Node, Tabs, Tab, Rect, DragState, DragOptions, DragPointer, DropError

class DragDemo:
    def __init__(self, en=False, ascii=False):
        self.en=en; self.tab_focus=False; self.pending=None; self.message=''; self.area=Rect();self.tab_area=Rect();self.tree_area=Rect()
        self.tabs=Tabs([Tab('a',self.word('데이터','Data'),edited=True),Tab('b',self.word('로그','Logs')),Tab('c',self.word('작업','Tasks')),Tab('d',self.word('비활성','Disabled'),disabled=True)])
        self.tree=Tree([Node('root',self.word('작업 공간','Workspace'),branch=True),Node('a',self.word('보고서','Reports'),parent='root',branch=True),Node('a1',self.word('월별 보고서','Monthly report'),parent='a'),Node('b',self.word('보관함','Archive'),parent='root',branch=True),Node('b1',self.word('이전 자료','Previous data'),parent='b'),Node('c',self.word('메모','Notes'),parent='root')])
        self.tree.expanded={'root','a'};self.drag=DragState(True);self.options=DragOptions(auto_scroll=True,hover_expand=True)
    def word(self,ko,en):return en if self.en else ko
    @property
    def model(self):return self.tabs if self.tab_focus else self.tree
    def draw(self,c,area,*,ascii=False):
        self.area=area;self.tab_area=Rect(area.x,area.y,area.width,min(1,area.height));self.tree_area=Rect(area.x,area.y+min(2,area.height),area.width,max(0,area.height-6))
        if self.tab_focus:
            self.tree.draw(c,self.tree_area,focused=False,ascii=ascii);self.drag.draw(self.tabs,c,self.tab_area,focused=True,ascii=ascii)
        else:
            self.tabs.draw(c,self.tab_area,focused=False,ascii=ascii);self.drag.draw(self.tree,c,self.tree_area,focused=True,ascii=ascii)
        lines=[self.word('Tab 대상 전환 | [ 이전 / ] 다음 | i 안으로 / o 밖으로','Tab switch | [ previous / ] next | i inside / o outside'),self.word('마우스로 끌기 | d 드래그 켜기/끄기 | Esc 취소','Drag with mouse | d toggle dragging | Esc cancel')]
        if self.pending:
            r=self.pending;status=self.word('승인 대기: ','Pending approval: ')+r.source_id+' -> '+r.target_id+' ('+r.position+') | y / r'
        else:status=self.message or self.word('앱 승인 후에만 순서가 바뀝니다.','Order changes only after host approval.')
        lines += [status,self.word('드래그: ','Dragging: ')+('ON'if self.drag.enabled else'OFF')+' | '+self.drag.phase]
        for i,line in enumerate(lines):
            y=area.y+area.height-4+i
            if y>=area.y:c.write(area.x,y,line,'info'if i==2 else'hint',width=area.width)
    def submit(self,request):
        if request is not None:self.pending=request
    def handle(self,action,height=10,text=''):
        command=text if action=='insert'else action
        if self.pending:
            if command=='y':
                try:
                    next_model=self.model.apply_drop(self.pending)
                    if self.tab_focus:self.tabs=next_model
                    else:self.tree=next_model
                    self.message=self.word('앱이 이동을 승인했습니다.','Host approved the move.')
                except DropError as error:self.message=error.reason
                self.pending=None
            elif command=='r' or action=='cancel':self.pending=None;self.message=self.word('앱이 이동을 거절했습니다.','Host rejected the move.')
            return
        if action in ('next','previous'):
            self.drag.cancel();self.tab_focus=not self.tab_focus;return
        if action=='cancel':self.drag.cancel();return
        if command=='d':self.drag.enabled=not self.drag.enabled;self.drag.cancel();return
        if command in ('[',']','i','o'):
            self.drag.cancel()
            try:self.submit(self.model.keyboard_drop({'[':'previous',']':'next','i':'inside','o':'outside'}[command],self.options))
            except DropError as error:self.message=error.reason
            return
        self.drag.cancel()
        if self.tab_focus:self.tabs.handle({'left':'previous','right':'next'}.get(action,action))
        else:self.tree.handle(action,self.tree_area.height)
    def pointer(self,x,y,button,kind='down'):
        if self.pending or button&64 or button&3 not in (0,3):return
        if kind=='down':
            if self.tab_area.contains(x,y):target=True
            elif self.tree_area.contains(x,y):target=False
            else:return
            if target!=self.tab_focus:self.drag.cancel();self.tab_focus=target
        a=self.tab_area if self.tab_focus else self.tree_area
        if kind!='down'and not self.drag.captured:return
        request=self.drag.pointer(self.model,DragPointer(kind,x-a.x,y-a.y,a.width,a.height),self.options)
        outcome=self.drag.result;self.submit(request)
        if kind=='up'and outcome==''and a.contains(x,y):
            if self.tab_focus:self.tabs.click(x-a.x,a.width)
            else:self.tree.click(x-a.x,y-a.y,a.height)
