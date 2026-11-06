"""Example host decides clocks, notice callbacks and cancellation approval."""
from . import Rect, Notice, NoticeAction, NoticeQueue, Progress, DataState, cells


class FeedbackDemo:
    def __init__(self, en=False):
        self.en = en
        self.now = self.frame = 0
        self.queue = NoticeQueue(4)
        self.queue.push(Notice('info',self.word('저장했습니다.','Saved.'),expires_at=5))
        self.queue.push(Notice('warning',self.word('선택한 항목이 없습니다.','No items selected.'),'warning',expires_at=20))
        self.queue.push(Notice('error',self.word('예제 작업 실패','Demo operation failed'),'error',detail=self.word('예제 데이터','Sample only'),
                               actions=[NoticeAction('off',self.word('사용 불가','Unavailable'),True),NoticeAction('retry',self.word('재시도','Retry'))]))
        self.progress = Progress('job',label=self.word('내보내기','Export'),message=self.word('처리 중','Working'),
                                 cancel_label=self.word('[ 취소 ]','[ Cancel ]'),current=40,total=100,cancellable=True)
        self.state = DataState('empty',self.word('결과 없음','No records'),self.word('앱이 데이터를 연결합니다.','The app supplies data.'))
        self.status = self.word('시간·요청 처리는 예제 앱이 결정합니다.','This host owns time and request handling.')
        self.notice_area = self.progress_area = Rect()

    def word(self,ko,en):
        return en if self.en else ko

    def draw(self,c,area,*,ascii=False):
        remaining=max(0,area.height-1);top=area.y
        def panel(limit,title):
            nonlocal remaining,top
            h=min(limit,remaining);r=c.panel(Rect(area.x,top,area.width,h),title,False,ascii)
            remaining-=h;top+=h
            return r
        self.notice_area=panel(5,self.word('알림','Notices'))
        self.queue.draw(c,self.notice_area,now=self.now)
        self.progress_area=panel(5,self.word('진행','Progress'))
        if self.progress.status=='cancelled':
            DataState('empty',self.word('내보내기 취소됨','Export cancelled'),self.word('앱이 취소 요청을 처리했습니다.','The host handled cancellation.')).draw(c,self.progress_area)
        else:
            self.progress.draw(c,self.progress_area,frame=self.frame)
        self.state.draw(c,panel(4,self.word('데이터 상태','Data state')))
        if area.height:
            c.write(area.x,area.y+area.height-1,self.status,'hint',width=area.width)

    def apply(self,event):
        if event.kind=='action' and event.action=='retry':
            self.queue.push(Notice(event.id,self.word('재시도 요청 처리','Retry accepted'),'success'))
            self.state=DataState('ready',self.word('준비 완료','Ready'),self.word('앱이 요청을 처리했습니다.','The host accepted the request.'))
            self.status=self.word('재시도 요청을 앱에서 처리했습니다.','Retry request handled by the host.')
        elif event.kind=='dismiss':
            self.queue.dismiss(event.id)
            self.status=self.word('알림을 닫았습니다.','Notice dismissed.')

    def cancel(self):
        event=self.progress.request_cancel()
        if event.kind=='cancel':
            self.progress.status='cancelled'
            self.status=self.word('취소 요청을 앱에서 처리했습니다.','Cancel request handled by the host.')

    def handle(self,action,height=10,text=''):
        command=text if action=='insert' else action
        if command=='t':
            self.now+=10;self.frame+=1
            count=len(self.queue.expire(self.now))
            self.status=self.word('만료한 알림: ','Expired notices: ')+str(count)
        elif command=='c':
            self.cancel()
        else:
            self.apply(self.queue.handle('dismiss' if action=='delete' else action,self.now,self.notice_area.height))

    def pointer(self,x,y,button):
        if button!=0:
            return
        if self.notice_area.contains(x,y):
            self.apply(self.queue.click(x-self.notice_area.x,y-self.notice_area.y,self.now))
        elif self.progress_area.contains(x,y) and y-self.progress_area.y==2 and x-self.progress_area.x<min(self.progress_area.width,cells(self.progress.cancel_label)):
            self.cancel()
