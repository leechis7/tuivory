"""One bilingual, database-free integrated example. python -m tuivory --help."""
import argparse
import json
from . import (Canvas, Palette, Rect, Tree, Node, Tabs, Tab, List, Item, Form, Field,
               Grid, Column, Record, Text, ControlState, Menu, Progress, DataState,
               Notices, Notice, Terminal)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', choices=['tree', 'tabs', 'list', 'form', 'grid', 'text', 'menu', 'feedback'], default='tree')
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
                  text=Text(word('한글과 이모지 👩‍💻\n여러 줄 편집', 'Unicode and emoji 👩‍💻\nMultiline editor')),
                  menu=Menu([Item('root', word('작업', 'Actions')), Item('run', word('실행', 'Run'), parent='root'), Item('off', word('비활성', 'Disabled'), disabled=True, parent='root')]),
                  feedback=Notices())
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
                if isinstance(model, Grid):
                    model.click(event.x - area.x, event.y - area.y, area.width, area.height)
                elif isinstance(model, Tabs):
                    model.click(event.x - area.x, area.width)
                else:
                    model.click(event.x - area.x, event.y - area.y, area.height)
            else:
                action = {'enter': 'activate', 'escape': 'cancel', 'text': 'insert', 'tab': 'next', 'shift_tab': 'previous', 'ctrl_n': 'null'}.get(event.key, event.key)
                if isinstance(model, (Form, Text)):
                    model.handle(action, event.text)
                elif isinstance(model, Tabs):
                    model.handle({'left': 'previous', 'right': 'next'}.get(action, action))
                elif isinstance(model, (Grid, List, Menu)):
                    model.handle(action, area.height, event.text)
                elif isinstance(model, Tree):
                    model.handle(action, area.height)

if __name__ == '__main__':
    main()
