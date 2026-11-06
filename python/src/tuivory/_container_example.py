"""Host composes two configured containers and supplies keys and editor contents."""
from . import Container, ContainerOptions, LayoutItem, Track, Rect, Text

class ContainerDemo:

    def __init__(self, en=False, ascii=False):
        self.en = en
        self.opened = False
        self.ascii = False
        self.status = ''
        self.base = Container([LayoutItem('nav', track=Track(fixed=20)), LayoutItem('editor')], ContainerOptions(kind='row', gap=1, virtual_width=96))
        self.base.state.move_focus(self.base.items)
        self.layers = Container([LayoutItem('background')], ContainerOptions(kind='layers'))
        self.editor = Text(self.word('편집 영역 한글 界', 'Editor area ASCII' if ascii else 'Editor area Unicode 界'))

    def word(self, ko, en):
        return en if self.en else ko

    def draw(self, c, area, *, ascii=False):
        self.ascii = ascii
        self.ox = area.x
        self.oy = area.y

        def pane(id, child, focused):
            inner = child.panel(Rect(0, 0, child.width, child.height), self.word('탐색', 'Navigator') if id == 'nav' else self.word('편집', 'Editor'), focused, ascii)
            if id == 'nav':
                child.write(inner.x, inner.y, self.word('개요', 'Overview'), 'body', width=inner.width)
            else:
                self.editor.draw(child, inner, focused=focused)

        def layer(id, child, focused):
            if id == 'background':
                self.base.draw(child, Rect(0, 0, child.width, child.height), pane)
            else:
                inner = child.panel(Rect(0, 0, child.width, child.height), self.word('팝업', 'Modal'), False, ascii)
                child.write(inner.x, inner.y, self.word('배경 입력 차단', 'Background input blocked'), 'body', width=inner.width)
                child.write(inner.x, inner.y + 1, self.word('m / Esc 닫기', 'm / Esc close'), 'hint', width=inner.width)
        self.layers.draw(c, Rect(area.x, area.y, area.width, max(0, area.height - 1)), layer)
        if area.height:
            c.write(area.x, area.y + area.height - 1, self.status or self.word('스크롤: ', 'Scroll: ') + str(self.base.scroll_x), 'hint', width=area.width)

    def handle(self, action, height=10, text=''):
        command = text if action == 'insert' else action
        if command == 'm' or (command == 'cancel' and self.opened):
            self.opened = not self.opened if command == 'm' else False
            self.layers.set_items([LayoutItem('background')] + ([LayoutItem('popup', modal=True, centered=True, area=Rect(width=30, height=6))] if self.opened else []))
            self.status = self.word('팝업 열림', 'Popup open') if self.opened else self.word('팝업 닫힘', 'Popup closed')
        elif not self.opened:
            if command in ('h', 'l'):
                self.base.scroll_x = max(0, self.base.scroll_x + (4 if command == 'l' else -4))
                self.status = self.word('스크롤: ', 'Scroll: ') + str(self.base.scroll_x)
            elif command in ('next', 'previous'):
                self.base.state.move_focus(self.base.items, command == 'previous')
            elif self.base.state.focused == 'editor':
                self.editor.handle(action, text)

    def pointer(self, x, y, button):
        if button == 0 and self.layers.pointer(x, y, True, True) == 'background':
            self.base.pointer(x - self.ox, y - self.oy, True, True)
