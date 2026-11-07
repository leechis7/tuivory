"""The example host accepts requests and owns modal lifetime and focus scopes."""
from . import Dialog,DialogButton,Shadow,ShadowOptions,Rect,Text,Focus,FocusTarget
class DialogDemo:
    def __init__(self,en=False):
        self.en=en;self.opened=False;self.disabled=False;self.card=Rect();self.area=Rect()
        self.focus=Focus('root',[FocusTarget('editor')]);self.editor=Text(self.word('대화상자를 닫으면 편집합니다.','Close the dialog to edit this text.'))
        self.dialog=Dialog(self.word('다시 연결','Reconnect'),self.word('작업을 다시 시도할까요?\n내용과 실행은 앱이 결정합니다.','Retry the operation?\nThe host supplies content and actions.'),self.buttons(),'cancel')
        self.status=self.word('아직 실행하지 않았습니다.','No action accepted.');self.open()
    def word(self,ko,en):return en if self.en else ko
    def buttons(self):return [DialogButton('retry',self.word('작업 다시 시도','Retry operation')),DialogButton('settings',self.word('연결 설정 열기','Open settings')),DialogButton('cancel',self.word('취소','Cancel'),self.disabled)]
    def open(self):
        if not self.opened:self.focus.open('dialog',[FocusTarget('buttons')]);self.opened=True
        self.dialog.focus('cancel')
    def accept(self,e):
        if e.kind in ('activate','cancel'):
            self.status=self.word('앱이 수락한 요청: ','Host accepted: ')+e.id;self.opened=False;self.focus.close('dialog');self.card=Rect()
    def draw(self,c,area,*,ascii=False):
        self.area=area;self.editor.draw(c,Rect(area.x,area.y,area.width,min(2,area.height)),focused=not self.opened)
        for y in range(area.y+2,area.y+max(0,area.height-2)):c.write(area.x,y,(':'if ascii else'界'if self.en else'가')*area.width,'hint',width=area.width)
        if area.height>=2:c.write(area.x,area.y+area.height-2,self.status,'hint',width=area.width)
        if area.height:c.write(area.x,area.y+area.height-1,self.word('m 열기 | x 취소 비활성 전환','m reopen | x toggle Cancel disabled'),'hint',width=area.width)
        if self.opened:
            w=min(41,area.width);h=min(12,max(0,area.height-2));bounds=Rect(area.x+(area.width-w)//2,area.y+max(0,(area.height-h)//2-1),w,h)
            self.card=Shadow(ShadowOptions('auto')).draw(c,bounds,lambda child:self.dialog.draw(child,Rect(0,0,child.width,child.height),ascii=ascii),ascii=ascii).card
    def handle(self,action,height=10,text=''):
        command=text if action=='insert'else action
        if command=='m':self.open()
        elif command=='x':self.disabled=not self.disabled;self.dialog.set_buttons(self.buttons())
        elif self.opened:self.accept(self.dialog.handle(action))
        else:self.editor.handle('newline'if action=='activate'else action,text)
    def pointer(self,x,y,button):
        if button!=0:return
        if self.opened:
            if self.card.contains(x,y):self.accept(self.dialog.click(x-self.card.x,y-self.card.y))
        elif self.area.contains(x,y):self.editor.click(x-self.area.x,y-self.area.y,self.area.width,min(2,self.area.height))
