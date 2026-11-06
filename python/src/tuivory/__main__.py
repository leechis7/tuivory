"""One bilingual, database-free integrated example. python -m tuivory --help."""
import argparse
import json
from . import (Canvas, Palette, Rect, Tree, Node, Tabs, Tab, List, Item, Form, Field,
               Grid, Column, Record, Text, ControlState, Menu, Progress, DataState,
               Notices, Notice, Terminal)


class WorkspaceDemo:
    """Example host composition, not a required application screen."""
    def __init__(self, tree, en):
        from . import Split
        self.tree, self.en, self.tab_focus = tree, en, False
        self.tabs = Tabs([Tab('overview', 'Overview' if en else '개요'),
                          Tab('draft', 'Draft document' if en else '초안 문서', edited=True, closable=True),
                          Tab('disabled', 'Disabled' if en else '비활성', disabled=True)])
        self.split = Split(16, 20, 24)
        self.areas = {}

    def draw(self, canvas, area, *, ascii=False):
        from . import path_runs, status_line, StatusItem
        self.areas['tabs'] = Rect(0, 0, area.width, 1)
        self.tabs.draw(canvas, Rect(area.x, area.y, area.width, 1), focused=self.tab_focus, ascii=ascii)
        path_runs([('root', 'Workspace' if self.en else '작업 공간'),
                   ('current', 'Components' if self.en else '컴포넌트')], area.width).draw(canvas, Rect(area.x, area.y + 1, area.width, 1))
        layout, body = self.split.layout(area.width), max(0, area.height - 3)
        right = Rect(area.x, area.y + 2, area.width, body)
        self.areas['tree'] = Rect()
        self.areas['divider'] = Rect()
        if not layout.compact:
            left = canvas.panel(Rect(area.x, area.y + 2, layout.first, body), 'Explorer' if self.en else '탐색', not self.tab_focus, ascii)
            self.areas['tree'] = Rect(left.x - area.x, left.y - area.y, left.width, left.height)
            self.tree.draw(canvas, left, focused=not self.tab_focus, ascii=ascii)
            self.areas['divider'] = Rect(layout.first, 2, 1, body)
            for y in range(body):
                canvas.write(area.x + layout.first, area.y + 2 + y, '|' if ascii else '│', 'focus.border', width=1)
            right = Rect(area.x + layout.first + 1, area.y + 2, layout.second, body)
        right = canvas.panel(right, 'Content' if self.en else '내용', False, ascii)
        canvas.write(right.x, right.y, 'Selected tab' if self.en else '선택한 탭', 'hint', width=right.width)
        canvas.write(right.x, right.y + 1, next(t.title for t in self.tabs.items if t.id == self.tabs.active), width=right.width)
        status_line([StatusItem('ready', 'Ready' if self.en else '준비', 'success', 10),
                     StatusItem('keys', 'Tab focus | < > resize' if self.en else 'Tab 포커스 | < > 크기', 'hint', 1)], area.width).draw(canvas, Rect(area.x, area.y + area.height - 1, area.width, 1))
        self.width = area.width

    def handle(self, action, height=10, text=''):
        if action in ('next', 'previous'):
            self.tab_focus = not self.tab_focus
        elif action == 'insert' and text in ('<', '>'):
            self.split.resize(self.width, self.split.preferred + (-1 if text == '<' else 1))
        elif self.tab_focus:
            self.tabs.handle({'left': 'previous', 'right': 'next'}.get(action, action))
        else:
            self.tree.handle(action, self.areas['tree'].height)

    def click(self, x, y, height=10):
        if self.areas['tabs'].contains(x, y):
            self.tab_focus = True
            return self.tabs.click(x, self.width)
        r = self.areas['tree']
        if r.contains(x, y):
            self.tab_focus = False
            return self.tree.click(x - r.x, y - r.y, r.height)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', choices=['tree', 'tabs', 'list', 'form', 'grid', 'text', 'menu', 'feedback', 'workspace'], default='tree')
    parser.add_argument('--lang', choices=['ko', 'en'], default='ko')
    parser.add_argument('--theme', choices=['dark', 'light', 'blackwhite'], default='dark')
    parser.add_argument('--colors', choices=['8', '16', '256', 'truecolor'], default='256')
    parser.add_argument('--ascii', action='store_true')
    parser.add_argument('--snapshot', action='store_true')
    parser.add_argument('--snapshot-ansi', action='store_true')
    parser.add_argument('--width', type=int, default=72)
    parser.add_argument('--height', type=int, default=18)
    args = parser.parse_args()
    ko = args.lang == 'ko'
    word = lambda a, b: a if ko else b
    tree = Tree([Node('root', word('작업 공간', 'Workspace'), branch=True),
                 Node('src', word('소스', 'Sources'), parent='root'),
                 Node('nested', word('컴포넌트', 'Components'), parent='src'),
                 Node('tree', word('트리', 'Tree'), parent='nested'),
                 Node('leaf', word('다섯 단계', 'Fifth level'), parent='tree'),
                 Node('docs', word('문서', 'Documentation'), parent='root')])
    tree.expanded = {'root', 'src', 'nested', 'tree'}
    models = dict(tree=tree,
                  tabs=Tabs([Tab('a', word('개요', 'Overview')), Tab('b', word('편집 중', 'Editing'), edited=True, closable=True), Tab('off', word('비활성', 'Disabled'), disabled=True)]),
                  list=List([Item('a', word('실행 가능', 'Available')), Item('off', word('비활성', 'Disabled'), disabled=True)]),
                  form=Form([Field('name', label=word('이름', 'Name'), value=word('한글 입력', 'Input')), Field('off', kind='checkbox', label=word('비활성', 'Disabled'), state=ControlState(disabled=True)), Field('run', kind='button', label=word('확인', 'Apply'))]),
                  grid=Grid([Column('name', word('이름', 'Name'), 24, True), Column('state', word('상태', 'State'), 16)], [Record('a', {'name': word('실제 커서', 'Real cursor'), 'state': 'OK'}), Record('b', {'name': 'CJK 한글 👩‍💻', 'state': 'NULL'})]),
                  text=Text(word('한글 é 界\n여러 줄을 편집합니다.', 'Grapheme text\nEdit with real cursor.' if args.ascii else 'Unicode é 界\nEdit with real cursor.')),
                  menu=Menu([Item('root', word('작업', 'Actions')), Item('run', word('실행', 'Run'), parent='root'), Item('off', word('비활성', 'Disabled'), disabled=True, parent='root')]),
                  feedback=Notices())
    models['workspace'] = WorkspaceDemo(tree, not ko)
    models['grid'].edit_enabled = True
    models['menu'].open('root')
    models['feedback'].push(Notice('ok', word('준비 완료', 'Ready'), 'success'))
    model = models[args.demo]
    themes, profiles = ['dark', 'light', 'blackwhite'], ['8', '16', '256', 'truecolor']
    theme, colors = args.theme, args.colors
    def draw(width, height):
        c = Canvas(width, height, Palette(theme, colors))
        area = c.panel(Rect(0, 0, width, max(0, height - 1)), word('Tuivory Python 예제', 'Tuivory Python example'), True, args.ascii)
        model.draw(c, area, ascii=args.ascii)
        if height:
            c.write(0, height - 1, word('Ctrl+Q 종료 · F1 테마 · F2 색상', 'Ctrl+Q quit · F1 theme · F2 colors').replace('·', '|' if args.ascii else '·'), 'hint', width=width)
        return c, area
    if args.snapshot or args.snapshot_ansi:
        c, _ = draw(args.width, args.height)
        if args.snapshot_ansi:
            print(c.ansi(), end='')
        else:
            print(json.dumps({'lines': c.lines(), 'cursor': c.cursor}, ensure_ascii=False))
        return
    with Terminal() as terminal:
        while True:
            c, area = draw(*terminal.size)
            terminal.write(c.ansi())
            event = terminal.read()
            if event is None:
                continue
            if event.key in ('ctrl_q', 'eof'):
                break
            if event.key == 'f1':
                theme = themes[(themes.index(theme) + 1) % len(themes)]
            elif event.key == 'f2':
                colors = profiles[(profiles.index(colors) + 1) % len(profiles)]
            elif event.key == 'mouse' and event.button == 0 and area.contains(event.x, event.y) and hasattr(model, 'click'):
                if isinstance(model, (Grid, Text)):
                    model.click(event.x - area.x, event.y - area.y, area.width, area.height)
                elif isinstance(model, Tabs):
                    model.click(event.x - area.x, area.width)
                else:
                    model.click(event.x - area.x, event.y - area.y, area.height)
            else:
                action = {'enter': 'activate', 'escape': 'cancel', 'text': 'insert', 'tab': 'next', 'shift_tab': 'previous', 'ctrl_n': 'null', 'ctrl_a':'select_all','ctrl_z':'undo','ctrl_y':'redo'}.get(event.key, event.key)
                if isinstance(model, (Form, Text)):
                    model.handle("newline" if isinstance(model,Text) and action=="activate" else action, event.text)
                elif isinstance(model, Tabs):
                    model.handle({'left': 'previous', 'right': 'next'}.get(action, action))
                elif isinstance(model, (Grid, List, Menu)):
                    model.handle(action, area.height, event.text)
                elif isinstance(model, Tree):
                    model.handle(action, area.height)
                elif isinstance(model, WorkspaceDemo):
                    model.handle(action, area.height, event.text)

if __name__ == '__main__':
    main()
