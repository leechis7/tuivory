"""Example host composition: global keys, screen, callbacks and focus ownership."""
from . import Canvas, Rect, Menu, MenuItem, Focus, FocusTarget, Text, menu_placement


class MenuDemo:
    def __init__(self, en=False, context=False):
        self.en, self.context = en, context
        word = lambda ko, eng: eng if en else ko
        self.menu = Menu([
            MenuItem('file', word('파일', 'File'), mnemonic='f'),
            MenuItem('new', word('새 문서', 'New document'), parent='file', mnemonic='n', shortcut='Ctrl+N'),
            MenuItem('line', parent='file', separator=True),
            MenuItem('off', word('사용 불가', 'Unavailable'), parent='file', disabled=True),
            MenuItem('recent', word('최근 문서', 'Recent documents'), parent='file', mnemonic='r'),
            MenuItem('a', word('예제 A', 'Example A'), parent='recent', mnemonic='a'),
            MenuItem('more', word('더 보기', 'More'), parent='recent', mnemonic='m'),
            MenuItem('b', word('예제 B', 'Example B'), parent='more', mnemonic='b'),
            MenuItem('edit', word('편집', 'Edit'), mnemonic='e'),
            MenuItem('copy', word('복사', 'Copy'), parent='edit', mnemonic='c', shortcut='Ctrl+C'),
        ])
        self.menu.back_label = word('뒤로', 'Back')
        self.menu.empty_label = word('항목 없음', '(empty)')
        self.focus = Focus('root', [FocusTarget('editor')])
        self.editor = Text(word('메뉴를 닫으면 여기를 편집할 수 있습니다.', 'Close the menu to edit this text.'))
        self.anchor = None
        self.area = self.content = self.bar = self.editor_area = Rect()
        self.status = word('팝업 밖의 클릭은 배경에 전달되지 않습니다.', 'Clicks outside the popup are blocked.')
        self.open('' if context else 'file')

    def open(self, id):
        self.menu.open(id, 'editor')
        if self.menu.opened and self.focus.depth == 0:
            self.focus.open('popup', [FocusTarget('menu')])
        self.sync()

    def sync(self, event=None):
        if not self.menu.opened and self.focus.depth:
            self.focus.close('popup')
        if event and event.kind == 'activate':
            label = next(i.label for i in self.menu.items if i.id == event.id)
            self.status = ('Selected: ' if self.en else '선택: ') + label

    def draw(self, c: Canvas, area: Rect, *, ascii=False):
        self.area = area
        self.bar = Rect(area.x, area.y, area.width, 0 if self.context else 1)
        self.editor_area = Rect(area.x, area.y + self.bar.height, area.width, min(2, max(0, area.height - self.bar.height)))
        self.editor.draw(c, self.editor_area, focused=not self.menu.opened)
        start = self.editor_area.y + self.editor_area.height
        for y in range(start, area.y + max(0, area.height - 2)):
            c.write(area.x, y, ('.' if ascii else '界' if self.en else '가') * area.width, 'hint', width=area.width)
        if self.bar.height:
            self.menu.draw_bar(c, self.bar)
        c.write(area.x, area.y + max(0, area.height - 2), self.status, 'hint', width=area.width)
        c.write(area.x, area.y + max(0, area.height - 1), 'F10 menu | Shift+F10 / right click' if self.en else 'F10 메뉴 | Shift+F10 / 오른쪽 클릭', 'hint', width=area.width)
        anchor = self.anchor or Rect(area.x + (area.width // 2 if self.context else 1), area.y + (5 if self.context else 0), 1, 1)
        if self.context or self.anchor:
            c.write(anchor.x, anchor.y, '+', 'warning', width=1)
        if self.menu.opened:
            width, height = self.menu.content_size()
            popup = menu_placement(anchor, area, min(48, ((width + 5) // 2) * 2), height + 4)
            self.content = self.menu.draw_popup(c, popup, self.menu.title() or ('Context menu' if self.en else '문맥 메뉴'), ascii=ascii)
        else:
            self.content = Rect()

    def handle(self, action, height=10, text=''):
        if action == 'f10':
            if self.menu.opened:
                self.sync(self.menu.close())
            else:
                self.anchor = None
                self.open('' if self.context else 'file')
        elif action == 'shift_f10':
            self.anchor = Rect(self.area.x + self.area.width // 2, self.area.y + 4, 1, 1)
            self.open('')
        elif self.menu.opened:
            if action == 'cancel' and self.focus.request_close() is None:
                return
            self.sync(self.menu.handle('mnemonic' if action == 'insert' else action, text, self.content.height))
        elif not self.focus.route('root').blocked:
            self.editor.handle('newline' if action == 'activate' else action, text)

    def pointer(self, x, y, button):
        if button == 2 and self.area.contains(x, y):
            self.anchor = Rect(x, y, 1, 1)
            self.open('')
        elif button == 0:
            if self.menu.opened:
                if self.content.contains(x, y):
                    self.sync(self.menu.click(x - self.content.x, y - self.content.y, self.content.height))
                elif self.bar.contains(x, y):
                    event = self.menu.bar_click(x - self.bar.x, self.bar.width)
                    if event.kind == 'open_request':
                        self.anchor = None
                        self.open(event.id)
            elif self.bar.contains(x, y):
                event = self.menu.bar_click(x - self.bar.x, self.bar.width)
                if event.kind == 'open_request':
                    self.anchor = None
                    self.open(event.id)
            elif not self.focus.route('root').blocked and self.editor_area.contains(x, y):
                self.editor.click(x - self.editor_area.x, y - self.editor_area.y, self.editor_area.width, self.editor_area.height)
