"""The host chooses surface, literal contents and the global cycle key."""
from . import Surface,Rect,Badge,Chip,ControlState,Help,Shortcut,Text
class SurfaceDemo:
    def __init__(self,en=False):
        self.en=en;self.index=1;self.roles=['surface','editor','field','button.focus']
        self.input=Text(self.word('읽기 전용','Read only'));self.input.read_only=True
    def word(self,ko,en):return en if self.en else ko
    def draw(self,c,area,*,ascii=False):
        def paint(child):
            w=child.width
            for y,(text,role)in enumerate([(self.word('바탕 위 문구','Body on surface'),'body'),(self.word('보조 설명','Secondary'),'hint'),(self.word('정상 상태','Success'),'success')]):
                child.write(0,y,text,role,width=w)
            Chip('off',self.word('비활성','Disabled'),ControlState(disabled=True)).draw(child,Rect(0,3,w,1))
            Badge(label=self.word('선택','Selected'),count=0,state=ControlState(selected=True)).draw(child,Rect(0,4,w,1))
            Chip('edited',self.word('수정','Edited'),ControlState(edited=True)).draw(child,Rect(0,5,w,1))
            self.input.draw(child,Rect(0,6,w,1),focused=False)
            Help([Shortcut('s',self.word('바탕 변경','Change surface'))]).draw(child,Rect(0,8,w,1))
        Surface(self.roles[self.index]).draw(c,Rect(area.x,area.y,area.width,max(0,area.height-1)),paint)
        labels=['패널','편집','입력','포커스 버튼']if not self.en else['panel','editor','field','focused button']
        if area.height:c.write(area.x,area.y+area.height-1,self.word('바탕: ','Surface: ')+labels[self.index],'hint',width=area.width)
    def handle(self,action,height=10,text=''):
        if (text if action=='insert'else action)=='s':self.index=(self.index+1)%4
    def pointer(self,*args):pass
