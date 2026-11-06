"""Feedback models use host clocks and return requests, without timers or I/O."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from .drawing import Canvas, Rect, cells, clean, clip

_SEVERITY = {'info': 0, 'success': 1, 'warning': 2, 'error': 3}
_MAX_NUMBER = (1 << 53) - 1


def _number(value):
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= _MAX_NUMBER:
        raise ValueError('expected a nonnegative safe integer')
    return value


@dataclass
class NoticeAction:
    id: str
    label: str = ''
    disabled: bool = False


@dataclass
class Notice:
    id: str
    text: str = ''
    severity: str = 'info'
    priority: int = 0
    expires_at: int = 0
    persistent: bool = False
    detail: str = ''
    actions: list[NoticeAction] = field(default_factory=list)


@dataclass(frozen=True)
class NoticeEvent:
    kind: str = ''
    id: str = ''
    action: str = ''


@dataclass(frozen=True)
class FeedbackSpan:
    start: int
    width: int
    text: str
    role: str
    action: str = ''
    disabled: bool = False


@dataclass
class FeedbackRow:
    id: str = ''
    text: str = ''
    role: str = 'body'
    focused: bool = False
    spans: list[FeedbackSpan] = field(default_factory=list)


def _draw(canvas: Canvas, rect: Rect, rows: list[FeedbackRow]):
    canvas.fill(rect)
    for y, row in enumerate(rows[:max(0, rect.height)]):
        canvas.write(rect.x, rect.y+y, row.text, row.role, width=rect.width, preserve_background=False)
        for span in row.spans:
            canvas.write(rect.x+span.start, rect.y+y, span.text, span.role,
                         width=span.width, preserve_background=False)


class NoticeQueue:
    def __init__(self, capacity=10):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or not 1 <= capacity <= 65536:
            raise ValueError('notice capacity must be 1..65536')
        self._capacity = capacity
        self._items: list[Notice] = []
        self.focused = ''
        self._width = 0
        self._hits: list[FeedbackRow] = []

    @property
    def capacity(self):
        return self._capacity

    @property
    def items(self):
        return deepcopy(self._items)

    @staticmethod
    def _pinned(notice):
        return notice.persistent or notice.severity == 'error' or bool(notice.actions)

    @staticmethod
    def _expired(notice, now):
        return not NoticeQueue._pinned(notice) and 0 < notice.expires_at <= now

    def push(self, notice):
        notice = deepcopy(notice)
        if not notice.id or notice.severity not in _SEVERITY:
            raise ValueError('invalid notice ID or severity')
        if not isinstance(notice.priority, int) or isinstance(notice.priority, bool) or not -(1 << 31) <= notice.priority < (1 << 31):
            raise ValueError('priority must be a signed 32-bit integer')
        _number(notice.expires_at)
        ids = [a.id for a in notice.actions]
        if len(ids) > 1024 or any(not i for i in ids) or len(set(ids)) != len(ids):
            raise ValueError('invalid notice actions')
        for i, old in enumerate(self._items):
            if old.id == notice.id:
                self._items[i] = notice
                self._hits = []
                return
        if len(self._items) >= self.capacity:
            candidates = [(i, n) for i, n in enumerate(self._items) if not self._pinned(n)]
            if not candidates:
                raise ValueError('notice queue full; important notices retained')
            at, old = min(candidates, key=lambda pair: (_SEVERITY[pair[1].severity], pair[1].priority))
            if (_SEVERITY[old.severity], old.priority) > (_SEVERITY[notice.severity], notice.priority):
                raise ValueError('notice queue full')
            if self.focused == old.id:
                self.focused = ''
            del self._items[at]
        if not self.focused or notice.severity == 'error':
            self.focused = notice.id
        self._items.append(notice)
        self._hits = []

    def visible(self, now=0):
        _number(now)
        return sorted(deepcopy([n for n in self._items if not self._expired(n, now)]),
                      key=lambda n: (-_SEVERITY[n.severity], -n.priority))

    def dismiss(self, id):
        at = next((i for i, n in enumerate(self._items) if n.id == id), None)
        if at is None:
            return False
        del self._items[at]
        if self.focused == id:
            self.focused = ''
        self._hits = []
        return True

    def expire(self, now):
        _number(now)
        events = [NoticeEvent('expired', n.id) for n in self._items if self._expired(n, now)]
        for event in events:
            self.dismiss(event.id)
        return events

    @staticmethod
    def _limit(count, height):
        height = max(0, min(4096, height))
        return max(1, height-1) if count > height and height > 0 else height

    def request_action(self, id, action, now=0):
        for n in self.visible(now):
            if n.id == id and any(a.id == action and not a.disabled for a in n.actions):
                return NoticeEvent('action', id, action)
        return NoticeEvent()

    def handle(self, action, now=0, height=10):
        action = {'down': 'next', 'up': 'previous'}.get(action, action)
        items = self.visible(now)
        items = items[:self._limit(len(items), height)]
        if not items or action not in ('next', 'previous', 'activate', 'dismiss'):
            return NoticeEvent()
        at = next((i for i, n in enumerate(items) if n.id == self.focused), 0)
        if action == 'next':
            at = min(at+1, len(items)-1)
        elif action == 'previous':
            at = max(0, at-1)
        n = items[at]
        self.focused = n.id
        if action == 'dismiss':
            return NoticeEvent('dismiss', n.id)
        if action == 'activate':
            a = next((a for a in n.actions if not a.disabled), None)
            if a:
                return NoticeEvent('action', n.id, a.id)
        return NoticeEvent()

    def layout(self, width, height, now=0):
        self._width = width = max(0, min(65535, width))
        height = max(0, min(4096, height))
        items = self.visible(now)
        limit = self._limit(len(items), height)
        rows = []
        for n in items[:limit]:
            mark = {'error': '[!]', 'warning': '[?]', 'success': '[+]', 'info': '[i]'}[n.severity]
            value = ('> ' if self.focused == n.id else '  ') + mark + ' ' + clean(n.text)
            if n.detail:
                value += ' / ' + clean(n.detail)
            parts = []
            for a in n.actions:
                part = ' [' + clean(a.label) + ']'
                parts.append((cells(value), part, a))
                value += part
            end = max(0, width-1) if cells(value) > width else width
            spans = []
            for start, part, a in parts:
                painted = clip(part, max(0, end-start))
                size = cells(painted)
                if size:
                    spans.append(FeedbackSpan(start, size, painted,
                                              'disabled' if a.disabled else n.severity, a.id, a.disabled))
            rows.append(FeedbackRow(n.id, clip(value, width, True), n.severity,
                                    self.focused == n.id, spans))
        if len(items) > limit and height > len(rows):
            rows.append(FeedbackRow(text=clip('+'+str(len(items)-limit), width, True), role='hint'))
        self._hits = rows
        return deepcopy(rows)

    def click(self, x, y, now=0):
        _number(now)
        if not (0 <= x < self._width and 0 <= y < len(self._hits)):
            return NoticeEvent()
        row = self._hits[y]
        if not row.id or not any(n.id == row.id for n in self.visible(now)):
            return NoticeEvent()
        for span in row.spans:
            if span.start <= x < span.start+span.width:
                if span.disabled:
                    return NoticeEvent()
                self.focused = row.id
                return self.request_action(row.id, span.action, now)
        self.focused = row.id
        return NoticeEvent('focus', row.id)

    def draw(self, canvas, rect, *, now=0, ascii=False):
        _draw(canvas, rect, self.layout(rect.width, rect.height, now))


@dataclass
class Progress:
    id: str = ''
    label: str = ''
    status: str = 'loading'
    message: str = ''
    cancel_label: str = ''
    current: int = 0
    total: int = 0
    cancellable: bool = False

    def request_cancel(self):
        return NoticeEvent('cancel', self.id) if self.id and self.cancellable and self.status in ('', 'loading') else NoticeEvent()

    def layout(self, width, frame=0):
        _number(self.current)
        _number(self.total)
        _number(frame)
        width = max(0, min(65535, width))
        status = self.status or 'loading'
        role = {'error': 'error', 'success': 'success', 'empty': 'hint', 'cancelled': 'hint',
                'ready': 'body', 'loading': 'info'}.get(status, 'error')
        value = status
        if status == 'loading':
            if self.total == 0:
                value = '|/-\\'[frame % 4]
            else:
                ratio = min(self.current, self.total) / self.total
                size = min(30, max(0, width-10))
                done = int(ratio*size)
                value = '['+'#'*done+'-'*(size-done)+'] '+str(int(ratio*100))+'%'
        if self.message:
            value += ' '+self.message
        rows = [FeedbackRow(self.id, clip(self.label, width, True), role),
                FeedbackRow(self.id, clip(value, width, True), role)]
        if self.request_cancel().kind and self.cancel_label:
            rows.append(FeedbackRow(self.id, clip(self.cancel_label, width, True), 'hint'))
        return rows

    def draw(self, canvas, rect, *, frame=0, ascii=False):
        _draw(canvas, rect, self.layout(rect.width, frame))


@dataclass
class DataState:
    kind: str = 'empty'
    text: str = ''
    detail: str = ''

    def layout(self, width):
        width = max(0, min(65535, width))
        role = {'ready': 'body', 'loading': 'info', 'empty': 'hint'}.get(self.kind, 'error')
        return [FeedbackRow(text=clip(self.text, width, True), role=role),
                FeedbackRow(text=clip(self.detail, width, True), role='hint')]

    def draw(self, canvas, rect, **_):
        _draw(canvas, rect, self.layout(rect.width))
