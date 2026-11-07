"""Application-owned rows, approval buttons, search mode and example keys."""
from copy import deepcopy
from . import (Grid,Column,Record,ControlState,GridEditOptions,GridColumnOptions,
               GridCellInfo,GridLabels,GridRange,grid_preset,Text,Rect)

class GridDemo:
    def __init__(self,en=False,ascii=False):
        self.en=en;self.area=Rect();self.search=None;self.detail=None;self.message='';self.pending=None;self.saved=None;self.density=False
        name=self.word('한글 👩‍💻','Unicode 👩‍💻'if not ascii else'ASCII sample')
        self.rows=[
            Record('r1',{'id':'01','name':name,'value':'1234','state':self.word('준비','Ready')}),
            Record('r2',{'id':'02','name':self.word('널 값','Null value'),'value':None,'state':'NULL'}),
            Record('r3',{'id':'03','name':self.word('비활성 행','Disabled row'),'value':'blocked','state':self.word('비활성','Disabled')},ControlState(disabled=True)),
            Record('r4',{'id':'04','name':self.word('읽기 전용','Read only'),'value':'read-only','state':self.word('읽기 전용','Read only')},ControlState(read_only=True)),
            Record('r5',{'id':'05','name':self.word('수정된 셀','Edited cell'),'value':'changed','state':self.word('수정됨','Edited')},cell_states={'value':ControlState(edited=True)}),
            Record('r6',{'id':'06','name':self.word('빈 문자열','Empty string'),'value':'','state':self.word('비어 있음','Empty')}),
            Record('r7',{'id':'07','name':'Find target','value':'long_value_for_horizontal_scrolling','state':self.word('검색 가능','Searchable')}),
            Record('r8',{'id':'08','name':self.word('오류 표시','Invalid cell'),'value':'invalid','state':self.word('오류','Invalid')},cell_states={'value':ControlState(invalid=True)})]
        self.grid=Grid([Column('id','ID',5,pin='left'),Column('name',self.word('이름','Name'),18,True),
                        Column('value',self.word('값','Value'),22,True),Column('state',self.word('상태','State'),12,pin='right')],self.rows)
        self.grid.set_options(grid_preset('data'))
        self.grid.set_labels(GridLabels(loading=self.word('로딩 중','loading'),empty=self.word('비어 있음','empty'),range=self.word('범위','range'),more=self.word('더 있음','more')))
        self.grid.set_edit_options(GridEditOptions(True,True,True))
        self.grid.set_column_options('value',GridColumnOptions(align='auto',overflow='scroll',expand=1))
        self.grid.set_cell_info(self.cell_info)
        self.grid.focus('r1','name')
    def word(self,ko,en):return en if self.en else ko
    def cell_info(self,row,column):
        value=row.cells.get(column.id)
        return GridCellInfo(display='1,234',has_display=column.id=='value'and value=='1234',numeric=column.id=='value'and value=='1234')
    def draw(self,c,area,*,ascii=False):
        self.area=Rect(area.x,area.y,area.width,max(0,area.height-3))
        self.grid.draw(c,self.area,focused=self.search is None and self.detail is None,ascii=ascii)
        if self.detail:
            inner=c.panel(self.area,self.word('원문 상세','Raw cell details'),True,ascii);self.detail.wrap=True;self.detail.draw(c,inner,focused=True,ascii=ascii)
        if area.height>=3:
            y=area.y+area.height-3
            if self.search is not None:
                prompt=self.word('검색: ','Find: ');c.write(area.x,y,prompt,'hint',width=area.width)
                from . import cells
                offset=min(area.width,cells(prompt));self.search.draw(c,Rect(area.x+offset,y,max(0,area.width-offset),1))
            else:c.write(area.x,y,self.message,'info',width=area.width)
        if area.height>=2:c.write(area.x,area.y+area.height-2,self.word('Enter 편집 | / 검색 | d 원문 | p 붙여넣기 | c 복사','Enter edit | / find | d details | p paste | c copy'),'hint',width=area.width)
        if area.height:c.write(area.x,area.y+area.height-1,self.word('대기: y 승인/r 거절 | Ctrl+N NULL | v 간격 | b 보기 저장/복원','Pending: y approve/r reject | Ctrl+N NULL | v density | b view'),'hint',width=area.width)
    def approve(self,accept):
        pending=self.pending
        if not pending:return
        kind,data=pending
        if not accept:
            if kind=='edit':self.grid.resolve_edit(data['id'],error=self.word('거절됨: 수정 후 다시 제출','Rejected: edit and retry'))
            else:self.grid.cancel_paste()
            self.message=self.word('앱이 요청을 거절했습니다.','Host rejected the request.');self.pending=None;return
        rows=deepcopy(self.rows)
        changes=[data]if kind=='edit'else data['changes']
        for change in changes:
            row=next((r for r in rows if r.id==change['row_id']),None)
            if row is not None:row.cells[change['column_id']]=change['value'];row.cell_states[change['column_id']]=ControlState(edited=True)
        accepted=self.grid.resolve_edit(data['id'],rows=rows)if kind=='edit'else self.grid.resolve_paste(data['id'],rows)
        if accepted:self.rows=rows
        self.message=self.word('앱이 요청을 승인했습니다.','Host approved the request.')if accepted else self.word('만료된 요청입니다.','Stale request.')
        self.pending=None
    def handle(self,action,height=10,text=''):
        command=text if action=='insert'else action
        if self.detail is not None:
            if action=='cancel':self.detail=None
            else:self.detail.handle(action,text)
            return
        if self.search is not None:
            if action=='cancel':self.search=None
            elif action=='activate':
                found=self.grid.find(self.search.value);self.search=None
                self.message=self.word('검색 일치','Match found')if found else self.word('검색 결과 없음','No match')
            else:self.search.handle(action,text)
            return
        if self.pending is not None:
            if command in ('y','r'):self.approve(command=='y')
            elif action=='cancel':
                if self.grid.edit:self.grid.handle('cancel')
                self.grid.cancel_paste();self.pending=None;self.message=self.word('요청 취소','Request cancelled')
            return
        if self.grid.edit is not None:
            event=self.grid.handle(action,max(0,self.area.height),text)
        elif command=='/':self.search=Text('',multiline=False);return
        elif command=='d':self.detail=self.grid.details();return
        elif command=='p':event=self.grid.paste('"paste\tname"\t"raw\nvalue"')
        elif command=='c':event=self.grid.copy_selection()
        elif command=='v':
            self.density=not self.density;self.grid.set_options(grid_preset('data').with_density('comfortable'if self.density else'normal'));return
        elif command=='b':
            if self.saved is None:self.saved=self.grid.save_view();self.message=self.word('보기 저장됨','View saved')
            else:self.grid.restore_view(self.saved);self.saved=None;self.message=self.word('보기 복원됨','View restored')
            return
        else:event=self.grid.handle(action,max(0,self.area.height),text)
        if event.kind in ('edit_submit','paste_request'):
            self.pending=('edit'if event.kind=='edit_submit'else'paste',deepcopy(event.data));self.message=self.word('승인 대기: y 승인 / r 거절','Pending approval: y approve / r reject')
        elif event.kind=='copy':self.message=self.word('복사 원문: ','Raw copy: ')+event.text
        elif event.kind in ('paste_rejected','edit_denied'):self.message=self.word('편집할 수 없는 셀입니다.','This cell cannot be edited.')
    def pointer(self,x,y,button):
        if button!=0 or self.detail is not None or self.search is not None or self.pending is not None:return
        a=self.area
        if a.contains(x,y):
            e=self.grid.click(x-a.x,y-a.y,a.width,a.height)
            if e.kind=='sort_request':
                self.message=self.word('정렬 요청: 앱이 처리합니다.','Sort requested: handled by the host.')
