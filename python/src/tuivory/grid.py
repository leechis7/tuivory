"""Independent data grid. Data changes are requests; the host supplies approved rows."""
from __future__ import annotations
from copy import deepcopy
from itertools import chain, islice
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Protocol
from .drawing import Canvas, Rect, cells, clip, graphemes, fold
from .models import ControlState, Event, unique
from .editing import Column, Record, Text


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"invalid {name}")
    return value


def parse_grid_tsv(text: str, max_cells: int = 10_000) -> list[list[str]]:
    """Strict quoted TSV; ignore blank physical rows, retain bare carriage returns."""
    _integer(max_cells, 1, 1_000_000, "cell limit")
    if len(text.encode('utf-8')) > 16 * 1024 * 1024:
        raise ValueError("paste exceeds byte limit")
    rows, row, value = [], [], []
    quoted = closed = started = False
    count = i = 0
    def finish_field():
        nonlocal count, value, closed, started
        count += 1
        if count > max_cells:
            raise ValueError("paste exceeds cell limit")
        row.append(''.join(value))
        value, closed, started = [], False, False
    while i < len(text):
        c = text[i]
        if quoted:
            if c == '"':
                if i + 1 < len(text) and text[i + 1] == '"':
                    value.append('"'); i += 2; continue
                quoted, closed = False, True
            else:
                value.append(c)
            i += 1; continue
        newline = c == '\n' or c == '\r' and i + 1 < len(text) and text[i + 1] == '\n'
        if c == '\t' or newline:
            if c == '\t' or row or started or closed or value:
                finish_field()
            if newline:
                if row:
                    rows.append(row); row = []
                if c == '\r': i += 1
        elif closed:
            raise ValueError("characters after closing quote")
        elif c == '"':
            if started or value:
                raise ValueError("quote inside unquoted field")
            quoted = started = True
        else:
            value.append(c); started = True
        i += 1
    if quoted:
        raise ValueError("unterminated quoted field")
    if row or started or closed or value:
        finish_field(); rows.append(row)
    if not rows or any(len(r) != len(rows[0]) for r in rows):
        raise ValueError("empty or ragged paste")
    return rows


def format_grid_tsv(rows: list[list[str]]) -> str:
    def quote(text):
        return '"' + text.replace('"', '""') + '"' if any(c in text for c in '\t\n\r"') or not text else text
    return '\n'.join('\t'.join(quote(v) for v in r) for r in rows)


@dataclass
class GridOptions:
    row_numbers: bool = False
    vertical_lines: bool = False
    horizontal_lines: bool = False
    striped: bool = False
    use_surface: bool = False
    hide_header: bool = False
    status_bar: bool = False
    ascii: bool = False
    highlight_cell: bool = True
    highlight_row: bool = False
    preserve_edited: bool = True
    show_cell_markers: bool = False
    disable_keyboard: bool = False
    disable_mouse: bool = False
    disable_editing: bool = False
    disable_copy: bool = False
    disable_resize: bool = False
    disable_header_sort: bool = False
    padding: int = 0
    row_spacing: int = 0
    gutter_width: int = 0
    max_copy_cells: int = 10_000
    selection: str = 'cell'
    status_fields: tuple[str, ...] = ('position', 'column', 'selection', 'sort', 'filter', 'loading', 'more', 'meta', 'error')

    def with_density(self, density: str):
        if density not in ('compact', 'normal', 'comfortable'):
            raise ValueError('invalid grid density')
        result = deepcopy(self)
        result.padding = int(density != 'compact')
        result.row_spacing = int(density == 'comfortable')
        return result


def grid_preset(name: str = 'simple') -> GridOptions:
    if name in ('', 'simple'): return GridOptions()
    if name == 'data':
        return GridOptions(row_numbers=True, vertical_lines=True, use_surface=True, status_bar=True, padding=1,
                           highlight_row=True, show_cell_markers=True)
    raise ValueError('unknown grid preset')


@dataclass
class GridColumnOptions:
    align: str = 'left'
    min_width: int = 1
    max_width: int = 4096
    auto_fit: bool = False
    expand: int = 0
    overflow: str = 'ellipsis'


@dataclass
class GridCellInfo:
    display: str = ''
    has_display: bool = False
    null: bool = False
    numeric: bool = False
    state: ControlState = field(default_factory=ControlState)
    metadata: str = ''


@dataclass(frozen=True)
class GridRange:
    anchor_row: str
    anchor_column: str
    end_row: str
    end_column: str


@dataclass
class GridLabels:
    null_text: str = 'NULL'
    loading: str = 'loading'
    empty: str = 'empty'
    range: str = 'range'
    more: str = 'more'


@dataclass
class GridDataStatus:
    total_rows: int = 0
    metadata: str = ''
    filter: str = ''
    error: str = ''
    loading: bool = False
    has_more: bool = False


@dataclass(frozen=True)
class GridSpan:
    id: str
    x: int
    width: int


@dataclass(frozen=True)
class GridGeometry:
    top: int
    left: int
    gutter: int
    header_rows: int
    footer_rows: int
    body_rows: int
    stride: int
    columns: tuple[GridSpan, ...]


@dataclass(frozen=True)
class GridValue:
    text: str = ''
    null: bool = False


@dataclass
class GridEditOptions:
    enabled: bool = False
    start_typing: bool = False
    allow_null: bool = False
    prepare: object = None


class GridSource(Protocol):
    def __len__(self) -> int: ...
    def row(self, index: int) -> Record: ...
    def index_of(self, id: str) -> int | None: ...


class MemoryRows:
    """Owned row snapshots, with constant-time stable-ID lookup."""
    def __init__(self, rows):
        rows = deepcopy(list(rows)); unique(rows)
        for r in rows:
            if not isinstance(r.id, str) or len(r.id.encode('utf-8'))>1_000_000 or len(r.cells)>65536 or any(not isinstance(k, str) or v is not None and not isinstance(v, str) for k, v in r.cells.items()):
                raise ValueError('invalid grid record')
            for v in r.cells.values():
                if v is not None and len(v.encode('utf-8'))>16*1024*1024: raise ValueError('grid cell exceeds byte limit')
        self._rows = rows
        self._indices = {r.id: i for i, r in enumerate(rows)}
    def __len__(self): return len(self._rows)
    def row(self, index): return deepcopy(self._rows[index])
    def index_of(self, id): return self._indices.get(id)


class GridRowDraft(str, Enum):
    NORMAL = 'normal'
    ADDED = 'added'
    MODIFIED = 'modified'
    DELETED = 'deleted'


class Grid:
    def __init__(self, columns: list[Column], rows):
        self.columns = deepcopy(list(columns)); unique(self.columns)
        if len(self.columns)>65536: raise ValueError("too many grid columns")
        for c in self.columns:
            if not isinstance(c.id,str) or not isinstance(c.label,str) or len(c.id.encode('utf-8'))>1_000_000 or len(c.label.encode('utf-8'))>1_000_000: raise ValueError('invalid grid column text')
            _integer(c.width, 1, 4096, 'column width')
            if c.pin not in ('', 'left', 'right'): raise ValueError('invalid column pin')
        self._source = rows if hasattr(rows, 'row') and hasattr(rows, 'index_of') else MemoryRows(rows)
        self._callback = False
        _integer(self._size(), 0, 1_000_000_000, 'row count')
        self.row = self.column = self.top = self.left = 0
        self.edit_enabled = False
        self.allow_null = False
        self.start_typing = False
        self.prepare = self.cell_info = self._row_draft = None
        self._dim_deletes = False
        self.edit = self._pending_paste = None
        self._serial = self._revision = self._applied_revision = 0
        self.query = ''
        self.case_sensitive = False
        self.use_display = False
        self.selected = None
        self.sort_column = self.sort_direction = ''
        self._options = GridOptions()
        self._column_options = {}
        self._cell_pan = {}
        self.status = GridDataStatus()
        self._labels = GridLabels()
        self._hits = self._capture = self._paint_key = None
        self._callback = False

    @property
    def rows(self): return [self._record(i) for i in range(self._size())]
    @property
    def options(self): return deepcopy(self._options)
    @property
    def revision(self): return self._revision
    @property
    def pending_paste(self): return deepcopy(self._pending_paste)
    @property
    def row_id(self):
        p = self._current(); return p[0].id if p else ''
    @property
    def column_id(self):
        p = self._current(); return p[1].id if p else ''

    def _guard(self):
        if self._callback: raise ValueError('grid mutation inside callback')

    def _source_call(self, method, *args):
        if self._callback: raise ValueError('recursive grid source callback')
        self._callback = True
        try: return deepcopy(method(*args))
        finally: self._callback = False

    def _size(self):
        return _integer(self._source_call(lambda: len(self._source)), 0, 1_000_000_000, 'row count')

    def _index(self, id):
        result = self._source_call(self._source.index_of, id)
        if result is not None: _integer(result, 0, self._size()-1, 'source index')
        return result

    @property
    def labels(self): return deepcopy(self._labels)

    def set_labels(self, labels):
        self._guard()
        if not isinstance(labels,GridLabels): raise ValueError('invalid grid labels')
        candidate=deepcopy(labels)
        for value in vars(candidate).values():
            if not isinstance(value,str) or len(value.encode('utf-8'))>1_000_000: raise ValueError('invalid grid label')
        self._labels=candidate

    def _record(self, i):
        _integer(i, 0, self._size() - 1, 'row index')
        r = self._source_call(self._source.row, i)
        if not r.id or self._index(r.id) != i:
            raise ValueError('inconsistent grid source IDs')
        return r

    def _invoke(self, callback, *args):
        if self._callback: raise ValueError('recursive grid callback')
        self._callback = True
        try: return callback(*(deepcopy(a) for a in args))
        finally: self._callback = False

    def visible_columns(self):
        return sorted((c for c in self.columns if not c.hidden), key=lambda c: {'left':0, '':1, 'right':2}[c.pin])

    def _current(self):
        cols, n = self.visible_columns(), self._size()
        if not cols or not n: return None
        self.row = max(0, min(n - 1, self.row))
        self.column = max(0, min(len(cols) - 1, self.column))
        record = self._record(self.row)
        if record.state.disabled:
            for i in islice(chain(range(self.row + 1, n), range(self.row - 1, -1, -1)), 100_000):
                record = self._record(i)
                if not record.state.disabled:
                    self.row = i; break
            else: return None
        return record, cols[self.column]

    def _info(self, record, column):
        info = self._invoke(self.cell_info, record, column) if self.cell_info else GridCellInfo()
        if not isinstance(info, GridCellInfo): raise ValueError('invalid grid cell info')
        info = deepcopy(info)
        state = record.cell_states.get(column.id, ControlState())
        info.state = ControlState(**{k: bool(getattr(record.state, k) or getattr(state, k) or getattr(info.state, k)) for k in vars(ControlState())})
        info.null = info.null or record.cells.get(column.id, '') is None
        return info

    def _prepared(self, r, c):
        value = r.cells.get(c.id, '')
        result = self._invoke(self.prepare, r, c) if self.prepare else True
        if result is None or result is False: return None
        if isinstance(result, GridValue):
            result.text.encode('utf-8')
            return result
        if result is True: return GridValue(value or '', self._info(r,c).null)
        raise ValueError('invalid grid preparation result')

    def _editable(self, r, c):
        return not self._options.disable_editing and not c.hidden and c.editable and self._info(r, c).state.editable and self._prepared(r,c) is not None

    def set_edit_options(self, options):
        if options.prepare is not None and not callable(options.prepare): raise ValueError('invalid grid prepare callback')
        self._invalidate()
        self.edit_enabled, self.start_typing, self.allow_null = bool(options.enabled), bool(options.start_typing), bool(options.allow_null)
        self.prepare = options.prepare

    def set_row_draft(self, lookup, dim_deletes=False):
        """Look up pending changes by stable row ID; None clears the provider."""
        if self._callback or (lookup is not None and not callable(lookup)):
            raise ValueError('invalid row draft lookup')
        self._row_draft, self._dim_deletes = lookup, bool(dim_deletes)

    def set_cell_info(self, callback):
        if callback is not None and not callable(callback): raise ValueError('invalid cell info callback')
        self._invalidate(); self.cell_info = callback

    def details(self):
        from .documents import TextDocument
        current = self._current()
        if not current or self._info(*current).state.disabled: return None
        r,c = current
        return TextDocument.viewer(r.cells.get(c.id,'') or '')

    def _invalidate(self):
        if self._callback: raise ValueError('grid mutation inside callback')
        self._revision += 1
        self.edit = self._pending_paste = self._hits = self._capture = None

    def set_rows(self, rows): self.set_source(MemoryRows(rows))
    def set_source(self, source):
        if self._callback: raise ValueError('grid mutation inside callback')
        _integer(self._source_call(lambda:len(source)), 0, 1_000_000_000, 'row count')
        current = self._current()
        id = current[0].id if current else ''
        i = self._source_call(source.index_of, id) if id else None
        if i is not None:
            _integer(i, 0, self._source_call(lambda:len(source)) - 1, 'source index')
            if self._source_call(source.row, i).id != id: raise ValueError('inconsistent grid source IDs')
        selection = self.selected
        self._source = source
        self.row = i if i is not None else 0
        self.selected = None
        if isinstance(selection, GridRange):
            try: self.set_selection(selection)
            except ValueError: pass
        self._invalidate()

    def focus(self, row_id, column_id):
        self._guard()
        i = self._index(row_id)
        cols = self.visible_columns()
        j = next((j for j, c in enumerate(cols) if c.id == column_id), None)
        if i is None or j is None or not 0 <= i < self._size(): return False
        r = self._record(i)
        if r.id != row_id or r.state.disabled: return False
        if self.edit and (row_id, column_id) != (self.edit['row_id'], self.edit['column_id']): self.edit = None
        self.row, self.column = i, j
        return True

    def set_options(self, options):
        o = deepcopy(options)
        _integer(o.padding, 0, 8, 'padding'); _integer(o.row_spacing, 0, 4, 'row spacing')
        _integer(o.gutter_width, 0, 128, 'gutter width'); _integer(o.max_copy_cells, 1, 1_000_000, 'copy limit')
        allowed = {'position','column','selection','sort','filter','loading','more','meta','error'}
        if o.selection not in ('cell','row','range') or len(o.status_fields) != len(set(o.status_fields)) or any(f not in allowed for f in o.status_fields):
            raise ValueError('invalid grid options')
        self._invalidate(); self._options = o

    def set_column_options(self, id, options):
        if not any(c.id == id for c in self.columns): raise ValueError('unknown column')
        o = deepcopy(options)
        _integer(o.min_width, 1, 4096, 'minimum width'); _integer(o.max_width, o.min_width, 4096, 'maximum width')
        _integer(o.expand, 0, 4096, 'expansion')
        if o.align not in ('left','right','center','auto') or o.overflow not in ('clip','ellipsis','scroll'):
            raise ValueError('invalid column options')
        self._invalidate(); self._column_options[id] = o
        c = next(c for c in self.columns if c.id == id); c.width = max(o.min_width, min(o.max_width, c.width))

    def set_column_layout(self, layout):
        data = deepcopy(list(layout)); ids = [x['id'] for x in data]
        if len(ids) != len(self.columns) or set(ids) != {c.id for c in self.columns} or len(set(ids)) != len(ids):
            raise ValueError('incompatible column layout')
        by_id = {c.id: deepcopy(c) for c in self.columns}
        for item in data:
            c = by_id[item['id']]
            c.hidden, c.pin = bool(item.get('hidden', False)), item.get('pin', '')
            if c.pin not in ('','left','right'): raise ValueError('invalid column pin')
        current = self._current()
        self._invalidate(); self.columns = [by_id[id] for id in ids]
        if current: self.focus(current[0].id, current[1].id)

    def _work_valid(self, request):
        if request['revision'] != self._revision: return False
        i = self._index(request['row_id'])
        c = next((c for c in self.visible_columns() if c.id == request['column_id']), None)
        if i is None or c is None or not 0 <= i < self._size(): return False
        r = self._record(i)
        return r.id == request['row_id'] and self._editable(r, c)

    def begin_edit(self, first=None):
        self._guard()
        current = self._current()
        if current is None or self.edit or self._pending_paste or not self.edit_enabled or not self._editable(*current): return False
        r, c = current; prepared = self._prepared(r,c)
        if prepared is None: return False
        value = prepared.text
        self._serial += 1
        self.edit = dict(id=self._serial, row_id=r.id, column_id=c.id, original=value,
                         null=prepared.null if first is None else False,
                         buffer=Text(value or '' if first is None else first, multiline=False),
                         pending=False, error='', revision=self._revision, move='')
        self._hits = None
        return True

    def resolve_edit(self, id, *, error='', rows=None):
        self._guard()
        e = self.edit
        if not e or not e['pending'] or e['id'] != id or e['revision'] != self._revision: return False
        if not self._work_valid(e): self.edit = None; return False
        replacement = MemoryRows(rows) if rows is not None else None
        if error:
            e['pending'], e['error'] = False, error
            return True
        row_id, column_id, move = e['row_id'], e['column_id'], e['move']
        self.edit = None
        if replacement is not None: self.set_source(replacement)
        self.focus(row_id, column_id)
        if move and self._move_editable(move == 'previous'): self.begin_edit()
        return True

    def _move_editable(self, previous=False):
        cols = self.visible_columns()
        if not cols: return False
        at = self.row * len(cols) + self.column
        step = -1 if previous else 1
        for pos in islice(range(at + step, -1 if previous else self._size() * len(cols), step), 100_000):
            i, j = divmod(pos, len(cols)); r = self._record(i)
            if self._editable(r, cols[j]): return self.focus(r.id, cols[j].id)
        return False

    def handle(self, action, height=10, text=''):
        self._guard()
        _integer(height, 0, 4096, 'height')
        if self._options.disable_keyboard: return Event()
        self._capture=None
        if not self.edit and action in ('select_up','select_down','select_left','select_right','select_home','select_end','select_page_up','select_page_down'):
            return self._extend_navigation(action[7:],height)
        e = self.edit
        if e:
            if action == 'cancel': self.edit = None; return Event('edit_cancel', e['row_id'])
            if not self._work_valid(e): self.edit = None; return Event('edit_stale')
            if e['pending']: return Event()
            if action == 'null':
                if not self.allow_null: return Event()
                e['null'] = not e['null']; e['error'] = ''
            elif action in ('submit','activate','next','previous'):
                self._serial += 1
                e['id'], e['pending'], e['error'] = self._serial, True, ''
                e['move'] = action if action in ('next','previous') else ''
                return Event('edit_submit', e['row_id'], data={k:e[k] for k in ('id','row_id','column_id')} | {'value':None if e['null'] else e['buffer'].value})
            else:
                if action in ('insert','paste','backspace','delete'): e['null'] = False; e['error'] = ''
                event = e['buffer'].handle(action, text) if not e['null'] else Event()
                if event.kind in ('copy','cut'): return event
            return Event('edit_change', e['row_id'])
        current = self._current()
        if not current: return Event()
        r, c = current
        if action in ('activate','edit'): return Event('edit_begin' if self.begin_edit() else 'edit_denied', r.id)
        if action == 'insert' and text and self.start_typing: return Event('edit_begin' if self.begin_edit(text) else 'edit_denied', r.id)
        if action == 'copy': return self.copy_selection()
        if action == 'details':
            return Event() if self._info(r,c).state.disabled else Event('details', r.id, data={'column_id':c.id,'value':r.cells.get(c.id,'')})
        if action in ('sort','filter','search','page_next','page_previous'):
            return self.request(action.removeprefix('page_') if action.startswith('page_') else action, text)
        moves = {'up':self.row-1, 'down':self.row+1, 'home':0, 'end':self._size()-1,
                 'page_up':self.row-max(1,height-1), 'page_down':self.row+max(1,height-1)}
        if action in moves:
            direction = -1 if action in ('up','home','page_up') else 1
            target = max(0, min(self._size()-1, moves[action]))
            while 0 <= target < self._size():
                if not self._record(target).state.disabled: self.row = target; break
                target += direction
        elif action in ('left','right'):
            self.column = max(0,min(len(self.visible_columns())-1,self.column+(-1 if action=='left' else 1)))
        elif action not in ('select',): return Event()
        p = self._current()
        return Event('select', p[0].id, data={'column_id':p[1].id}) if p else Event()

    def paste(self, text, max_cells=10_000, null_text=None):
        self._guard()
        if self.edit or self._pending_paste: return Event('paste_rejected')
        try: values = parse_grid_tsv(text, max_cells)
        except ValueError: return Event('paste_rejected')
        cols = self.visible_columns()
        if not cols or self.row + len(values) > self._size() or self.column + len(values[0]) > len(cols): return Event('paste_rejected')
        changes = []
        for dy, line in enumerate(values):
            r = self._record(self.row + dy)
            for dx, value in enumerate(line):
                c = cols[self.column + dx]
                if not self._editable(r,c): return Event('paste_rejected')
                changes.append(dict(row_id=r.id, column_id=c.id, value=None if null_text is not None and value == null_text else value))
        self._serial += 1
        self._pending_paste = dict(id=self._serial, changes=changes, revision=self._revision)
        return Event('paste_request', data=deepcopy(self._pending_paste))

    def resolve_paste(self, id, rows=None):
        self._guard()
        p = self._pending_paste
        if not p or p['id'] != id or p['revision'] != self._revision: return False
        if not all(self._work_valid(c | {'revision':p['revision']}) for c in p['changes']):
            self._pending_paste = None; return False
        replacement = MemoryRows(rows) if rows is not None else None
        self._pending_paste = None
        if replacement is not None: self.set_source(replacement)
        return True

    def cancel_paste(self):
        self._guard(); self._pending_paste = None

    def find(self, query, *, previous=False, max_cells=100_000):
        self._guard()
        _integer(max_cells,1,1_000_000,'find limit')
        cols = self.visible_columns(); total = len(cols)*self._size()
        if not query or not total or self.edit or self._pending_paste: return False
        self.query = query
        needle = query if self.case_sensitive else fold(query)
        start = self.row*len(cols)+self.column
        for step in range(1,min(total,max_cells)+1):
            at = (start+(-step if previous else step)) % total
            i,j = divmod(at,len(cols)); r = self._record(i); c = cols[j]
            info = self._info(r,c)
            if info.state.disabled: continue
            value = info.display if self.use_display and info.has_display else self._labels.null_text if self.use_display and info.null else r.cells.get(c.id,'') or ''
            if needle in (value if self.case_sensitive else fold(value)):
                self.row,self.column = i,j; return True
        return False

    def request(self, kind, text=''):
        self._guard()
        if kind not in ('sort','filter','search','next','previous'): raise ValueError('unknown grid request')
        if kind == 'sort' and self._options.disable_header_sort: return Event()
        current = self._current()
        self._invalidate()
        return Event(kind + '_request', current[0].id if current else '', text,
                     {'revision':self._revision,'column_id':current[1].id if current else ''})

    def apply_source(self, revision, source):
        if revision != self._revision or revision <= self._applied_revision: return False
        self.set_source(source)
        self._applied_revision = revision
        return True

    def set_selection(self, selection):
        self._guard()
        if selection is None: self.selected = None; return
        if not isinstance(selection,GridRange): raise ValueError('invalid grid range')
        cols = {c.id for c in self.visible_columns()}
        for rid,cid in ((selection.anchor_row,selection.anchor_column),(selection.end_row,selection.end_column)):
            i = self._index(rid)
            if i is None or not 0 <= i < self._size() or self._record(i).id != rid or cid not in cols: raise ValueError('unknown range ID')
        self.selected = selection

    def _selection_bounds(self):
        cols = self.visible_columns()
        if not cols or not self._size(): return None
        if self.selected:
            s = self.selected
            if not isinstance(s,GridRange):
                a,b,c,d = s
                return min(a,c),min(b,d),max(a,c),max(b,d)
            rows = [self._index(s.anchor_row),self._index(s.end_row)]
            cs = [next((i for i,c in enumerate(cols) if c.id==id),None) for id in (s.anchor_column,s.end_column)]
            if None in rows or None in cs: return None
            return min(rows),min(cs),max(rows),max(cs)
        return self.row,0 if self._options.selection=='row' else self.column,self.row,len(cols)-1 if self._options.selection=='row' else self.column

    def copy_selection(self, *, display=False, null_text='NULL'):
        if self._options.disable_copy: return Event()
        bounds = self._selection_bounds()
        if bounds is None: return Event()
        a,b,c,d = bounds; cols = self.visible_columns()
        if min(a,b)<0 or c>=self._size() or d>=len(cols) or (c-a+1)*(d-b+1)>self._options.max_copy_cells: return Event('copy_rejected')
        values=[]; byte_count=0
        for i in range(a,c+1):
            r=self._record(i); line=[]
            for j in range(b,d+1):
                col=cols[j]; info=self._info(r,col)
                if info.state.disabled: return Event('copy_rejected')
                value=info.display if display and info.has_display else null_text if info.null else r.cells.get(col.id,'') or ''
                byte_count+=len(value.encode('utf-8'))
                if byte_count>16*1024*1024: return Event('copy_rejected')
                line.append(value)
            values.append(line)
        return Event('copy',text=format_grid_tsv(values))

    def resize_column(self, id, width):
        if self._options.disable_resize: return False
        c = next((c for c in self.columns if c.id == id), None)
        if c is None: return False
        _integer(width,1,4096,'column width')
        o = self._column_options.get(id,GridColumnOptions())
        self._invalidate(); c.width=max(o.min_width,min(o.max_width,width))
        return True

    def auto_fit_column(self, id, height=20):
        _integer(height,0,4096,'height')
        c=next((c for c in self.columns if c.id==id),None)
        if c is None or self._options.disable_resize: return False
        w=cells(c.label or c.id)
        for i in range(self.top,min(self._size(),self.top+height)):
            r=self._record(i); info=self._info(r,c)
            value=info.display if info.has_display else self._labels.null_text if info.null else r.cells.get(id,'') or ''
            w=max(w,cells(value)+(2 if info.state.edited and self._options.show_cell_markers else 0))
        return self.resize_column(id,min(4096,max(1,w+2*self._options.padding)))

    def pan_cell(self, id, offset):
        self._guard()
        _integer(offset,0,1_000_000,'cell pan')
        if not any(c.id==id for c in self.columns): raise ValueError('unknown column')
        self._cell_pan[id]=offset

    def geometry(self, width, height):
        _integer(width,0,65535,'width'); _integer(height,0,4096,'height')
        _integer(self.top,0,1_000_000_000,'top row'); _integer(self.left,0,1_000_000,'left column')
        o=self._options
        header=int(not o.hide_header and height>0)
        footer=int(o.status_bar and height>header)
        stride=1+o.row_spacing+int(o.horizontal_lines)
        available=max(0,height-header-footer)
        count=(available+stride-1)//stride
        current=self._current()
        if current and count:
            self.top=min(self.top,self.row)
            if self.row>=self.top+count: self.top=self.row-count+1
        gutter=min(width,max(o.gutter_width,len(str(max(1,self._size())))+1 if o.row_numbers else 0))
        cols=deepcopy(self.visible_columns()); sep=int(o.vertical_lines)
        automatic=[c for c in cols if self._column_options.get(c.id,GridColumnOptions()).auto_fit]
        if automatic:
            records=[self._record(i) for i in range(self.top,min(self._size(),self.top+min(count,256)))]
            sampled=0
            for c in automatic:
                co=self._column_options[c.id]; w=cells(c.label or c.id)+2*o.padding
                for r in records:
                    if sampled>=100_000: break
                    sampled+=1; info=self._info(r,c)
                    value=info.display if info.has_display else self._labels.null_text if info.null else r.cells.get(c.id,'') or ''
                    w=max(w,cells(value)+2*o.padding+(2 if info.state.edited and o.show_cell_markers else 0))
                c.width=max(co.min_width,min(co.max_width,w))

        left=[c for c in cols if c.pin=='left']; right=[c for c in cols if c.pin=='right']; normal=[c for c in cols if not c.pin]
        self.left=min(self.left,max(0,len(normal)-1))
        current_column=cols[self.column] if current else None
        if current_column in normal:
            at=normal.index(current_column)
            self.left=min(self.left,at)
            capacity=max(0,width-gutter-sum(c.width+sep for c in left+right))
            while self.left<at and sum(c.width+sep for c in normal[self.left:at+1])>capacity:
                self.left+=1
        spans=[]; x=gutter
        # Pinned columns keep their side even when the scrollable group is clipped.
        right_width=min(max(0,width-gutter),sum(c.width+sep for c in right))
        end=width-right_width
        for c in left+normal[self.left:]:
            w=min(c.width,max(0,end-x))
            if w: spans.append(GridSpan(c.id,x,w))
            x+=w+sep
            if x>=end: break
        x=max(gutter,end)
        for c in right:
            w=min(c.width,max(0,width-x))
            if w: spans.append(GridSpan(c.id,x,w))
            x+=w+sep
            if x>=width: break
        # Expansion only uses remaining free space, after pinning and clipping.
        room=max(0,end-max((s.x+s.width+sep for s in spans if s.x<end),default=gutter))
        weights={s.id:self._column_options.get(s.id,GridColumnOptions()).expand for s in spans if s.x<end}
        total=sum(weights.values())
        if room and total:
            expanded=[]; shift=0; remaining=room
            for s in spans:
                if s.x>=end: expanded.append(s); continue
                co=self._column_options.get(s.id,GridColumnOptions())
                extra=min(remaining,co.max_width-s.width,room*weights.get(s.id,0)//total)
                expanded.append(GridSpan(s.id,s.x+shift,s.width+extra)); shift+=extra; remaining-=extra
            spans=expanded
        return GridGeometry(self.top,self.left,gutter,header,footer,count,stride,tuple(spans))

    def _editor_window(self, value, cursor, width):
        gs=graphemes(value); at=max(0,min(len(gs),cursor)); start=at; x=0
        reserve=min(width,max(1,cells(gs[at]) if at<len(gs) else 1))
        while start>0:
            w=cells(gs[start-1])
            if x+w>width-reserve: break
            start-=1; x+=w
        text=''; used=0
        from .drawing import clean
        for g in gs[start:]:
            g=clean(g); w=cells(g)
            if used+w>width: break
            text+=g; used+=w
        glyph=max(1,cells(gs[at]) if at<len(gs) else 1)
        return text,x,1 if glyph>width else glyph,start

    def edit_cursor(self, width, height):
        e=self.edit
        if not e or e['pending'] or e['null'] or not self._work_valid(e): return None
        geo=self.geometry(width,height)
        i=self._index(e['row_id'])
        span=next((s for s in geo.columns if s.id==e['column_id']),None)
        if i is None or span is None or not geo.top<=i<geo.top+geo.body_rows: return None
        c=next(c for c in self.columns if c.id==span.id)
        info=self._info(self._record(i),c)
        extra=2 if info.state.edited and self._options.show_cell_markers else 0
        room=span.width-2*self._options.padding-extra
        y=geo.header_rows+(i-geo.top)*geo.stride
        if room<=0 or y>=height-geo.footer_rows: return None
        _,x,glyph,_=self._editor_window(e['buffer'].value,e['buffer'].cursor,room)
        return span.x+self._options.padding+extra+x,y,glyph

    def _display(self,r,c,info,width,editing=False):
        e=self.edit
        if editing:
            return self._labels.null_text if e['null'] else self._editor_window(e['buffer'].value,e['buffer'].cursor,width)[0]
        text=info.display if info.has_display else self._labels.null_text if info.null else r.cells.get(c.id,'') or ''
        co=self._column_options.get(c.id,GridColumnOptions())
        if co.overflow=='scroll':
            offset=self._cell_pan.get(c.id,0); used=0; out=''
            for g in graphemes(text):
                n=cells(g)
                if used>=offset: out+=g
                elif used+n>offset: out+=' '*(used+n-offset)
                used+=n
            text=out
        text=clip(text,width,co.overflow!='clip')
        spare=max(0,width-cells(text))
        align='right' if co.align=='auto' and info.numeric else co.align
        return ' '*spare+text if align=='right' else ' '*(spare//2)+text+' '*(spare-spare//2) if align=='center' else text+' '*spare

    def status_text(self):
        p=self._current(); s=self.status
        _integer(s.total_rows,0,1_000_000_000,'total rows')
        fields={'position':f'{self.row+1 if p else 0}/{s.total_rows or self._size()}',
                'column':p[1].label or p[1].id if p else '', 'selection':self._labels.range if self.selected else '',
                'sort':(self.sort_column+' '+self.sort_direction).strip(), 'filter':s.filter,
                'loading':self._labels.loading if s.loading else '', 'more':self._labels.more if s.has_more else '',
                'meta':s.metadata, 'error':self.edit['error'] if self.edit and self.edit['error'] else s.error}
        if fields['error']: return fields['error']
        return ' | '.join(fields[k] for k in self._options.status_fields if fields[k])

    def _column_signature(self):
        return tuple((c.id,c.width,c.hidden,c.pin,c.editable) for c in self.columns)

    def draw(self, canvas, rect, *, focused=True, ascii=False):
        _integer(rect.x,0,1_000_000_000,'x'); _integer(rect.y,0,1_000_000_000,'y')
        geo=self.geometry(rect.width,rect.height); o=self._options
        child=Canvas(rect.width,rect.height,canvas.palette,'surface' if o.use_surface else canvas.surface_role)
        current_column_id=self.column_id
        hit_rows={}; signature=self._column_signature()
        sep='|' if ascii or o.ascii else '│'; horizontal='-' if ascii or o.ascii else '─'
        cols={c.id:c for c in self.columns}; bounds=self._selection_bounds()
        if geo.header_rows:
            child.fill(Rect(0,0,rect.width,1),'grid.header')
            for span in geo.columns:
                c=cols[span.id]; title=c.label or c.id
                if self.sort_column==c.id: title+=(' v' if self.sort_direction=='desc' else ' ^')
                child.write(span.x,0,clip(title,span.width,True),'grid.header',width=span.width)
        for dy in range(geo.body_rows):
            i=geo.top+dy; y=geo.header_rows+dy*geo.stride
            if y>=rect.height-geo.footer_rows or i>=self._size(): break
            r=self._record(i); hit_rows[i]=r.id
            draft=self._invoke(self._row_draft,r.id) if self._row_draft else GridRowDraft.NORMAL
            if geo.gutter:
                number=str(i+1) if o.row_numbers else ''
                marker={GridRowDraft.ADDED: '+', GridRowDraft.MODIFIED: '*', GridRowDraft.DELETED: '-' if ascii or o.ascii else '−'}.get(draft,'') if o.row_numbers else ''
                room=max(0,geo.gutter-1)
                number=number[-room:] if marker and room else '' if marker else number
                child.write(0,y,marker+number.rjust(room)+('' if marker else ' '),'disabled' if r.state.disabled else 'hint',width=geo.gutter)
            for span in geo.columns:
                c=cols[span.id]; info=self._info(r,c); state=info.state
                selected=i==self.row and c.id==current_column_id
                j=next(j for j,col in enumerate(self.visible_columns()) if col.id==c.id)
                in_range=bounds is not None and bounds[0]<=i<=bounds[2] and bounds[1]<=j<=bounds[3]
                editing=self.edit is not None and (r.id,c.id)==(self.edit['row_id'],self.edit['column_id']) and self._work_valid(self.edit)
                role='disabled' if state.disabled else 'error' if state.invalid else 'grid.active' if selected and o.highlight_cell else 'edited' if state.edited and o.preserve_edited else 'grid.range' if (o.highlight_row and i==self.row or in_range and self.selected) else 'surface' if o.striped and i%2 else 'body'
                if editing: role='hint' if self.edit['pending'] else 'error' if self.edit['error'] else 'field'
                pad=min(o.padding,span.width//2); marker='* ' if state.edited and (o.show_cell_markers or role=='grid.active') else ''
                room=max(0,span.width-2*pad-len(marker))
                text=self._display(r,c,info,room,editing)
                value=' '*pad+marker+text+' '*max(0,span.width-pad-len(marker)-cells(text))
                child.write(span.x,y,value,role,width=span.width)
                if draft == GridRowDraft.DELETED and self._dim_deletes and not editing and not state.edited and role in ('body','surface'):
                    for cell in child.data[y][span.x:span.x+span.width]:
                        cell.style=replace(cell.style,dim=True)
                if editing and not self.edit['pending'] and not self.edit['null']:
                    buf=self.edit['buffer'];lo,hi=sorted((buf.anchor,buf.cursor))
                    if lo<hi:
                        _,_,_,start=self._editor_window(buf.value,buf.cursor,room);x=0
                        from .drawing import clean
                        for index,glyph in enumerate(graphemes(buf.value)[start:],start):
                            glyph=clean(glyph);w=cells(glyph)
                            if x+w>room:break
                            if lo<=index<hi:child.write(span.x+pad+len(marker)+x,y,glyph,'selection',width=w)
                            x+=w
            if o.horizontal_lines:
                yy=y+1+o.row_spacing
                if yy<rect.height-geo.footer_rows: child.write(geo.gutter,yy,horizontal*max(0,rect.width-geo.gutter),'hint',width=rect.width-geo.gutter)
        if not self._size() and geo.header_rows<rect.height-geo.footer_rows:
            child.write(geo.gutter,geo.header_rows,clip(self.status.error or (self._labels.loading if self.status.loading else self._labels.empty),max(0,rect.width-geo.gutter)), 'error' if self.status.error else 'hint',width=rect.width-geo.gutter)
        if o.vertical_lines:
            for span in geo.columns:
                x=span.x+span.width
                if x<rect.width:
                    for y in range(rect.height-geo.footer_rows): child.write(x,y,sep,'grid.header' if y<geo.header_rows else 'hint',width=1)
        if geo.footer_rows: child.write(0,rect.height-1,clip(self.status_text(),rect.width,True),'error' if self.status.error or self.edit and self.edit['error'] else 'hint',width=rect.width)
        cursor=self.edit_cursor(rect.width,rect.height) if focused else None
        if cursor: child.set_cursor(*cursor)
        canvas.blit(child,Rect(0,0,rect.width,rect.height),rect.x,rect.y)
        key=(rect.x,rect.y,rect.width,rect.height,canvas.palette.theme,canvas.palette.colors,canvas.surface_role,bool(ascii),bool(focused))
        if not focused or self._paint_key is not None and self._paint_key!=key:self._capture=None
        self._paint_key=key
        self._hits=(rect.width,rect.height,geo,hit_rows,signature)

    def click(self,x,y,width,height):
        self._guard()
        if self._options.disable_mouse or self.edit or self._pending_paste or not self._hits or self._hits[:2]!=(width,height): return Event()
        if self._hits[4]!=self._column_signature(): return Event()
        if not 0<=x<width or not 0<=y<height: return Event()
        geo=self._hits[2]
        span=next((s for s in geo.columns if s.x<=x<s.x+s.width),None)
        if span is None: return Event()
        if y<geo.header_rows:
            if self._options.disable_header_sort: return Event()
            self.column=next(i for i,c in enumerate(self.visible_columns()) if c.id==span.id)
            return self.request('sort')
        dy=y-geo.header_rows
        if dy%geo.stride or y>=height-geo.footer_rows: return Event()
        i=geo.top+dy//geo.stride
        if i>=self._size(): return Event()
        r=self._record(i)
        if self._hits[3].get(i)!=r.id: return Event()
        c=next(c for c in self.columns if c.id==span.id)
        if self._info(r,c).state.disabled: return Event()
        if not self.focus(r.id,c.id): return Event()
        return Event('select',r.id,data={'column_id':c.id})

    @property
    def pointer_captured(self):
        return self._capture is not None

    def _capture_grid(self,kind,width,height,**values):
        self._capture=dict(kind=kind,width=width,height=height,revision=self._revision,signature=self._column_signature(),**values)

    def _range_anchor(self, current):
        selected=self.selected
        if isinstance(selected,GridRange) and self._selection_bounds() is not None:return selected.anchor_row,selected.anchor_column
        return current[0].id,current[1].id

    def _extend_navigation(self,action,height):
        current=self._current()
        if current is None:return Event()
        anchor_row,anchor_col=self._range_anchor(current)
        row,column=self.row,self.column
        result=self.handle(action,height)
        after=self._current()
        if result.kind!='select' or after is None:return result
        if self._info(*after).state.disabled:
            self.row,self.column=row,column
            return Event()
        self.set_selection(GridRange(anchor_row,anchor_col,after[0].id,after[1].id))
        return result

    def _grid_hit(self,x,y,width,height):
        if not self._hits or self._hits[:2]!=(width,height) or self._hits[4]!=self._column_signature():return None
        if not 0<=x<width or not 0<=y<height:return None
        geo=self._hits[2]
        span=next((s for s in geo.columns if s.x<=x<s.x+s.width),None)
        if y<geo.header_rows:return geo,span,None,False
        dy=y-geo.header_rows
        if dy%geo.stride or y>=height-geo.footer_rows:return None
        index=geo.top+dy//geo.stride
        if index>=self._size():return None
        row=self._record(index)
        if self._hits[3].get(index)!=row.id:return None
        gutter=span is None and x<geo.gutter and self._options.row_numbers
        if span is None and not gutter:return None
        return geo,span,row,gutter

    def _edit_pointer(self,action,x,y,width,height,extend):
        e=self.edit
        if not e or e['pending']or e['null']or not self._work_valid(e):
            self._capture=None;return Event()
        if action=='move' and (not self._capture or self._capture['kind']!='edit'):return Event()
        if action not in ('down','move','click','double'):return Event()
        hit=self._grid_hit(x,y,width,height)
        if not hit or not hit[1] or not hit[2] or (hit[2].id,hit[1].id)!=(e['row_id'],e['column_id']):
            return Event('edit_blocked') if action!='move' else Event()
        _,span,row,_=hit;c=next(c for c in self.columns if c.id==span.id)
        extra=2 if self._options.show_cell_markers and self._info(row,c).state.edited else 0
        pad=self._options.padding+extra;room=span.width-2*self._options.padding-extra
        if room<=0:return Event()
        buf=e['buffer'];_,_,_,start=self._editor_window(buf.value,buf.cursor,room)
        offset=max(0,min(room,x-span.x-pad));used=0;pos=start
        from .drawing import clean
        for g in graphemes(buf.value)[start:]:
            w=cells(clean(g))
            if used+w>offset:break
            used+=w;pos+=1
        buf.select(buf.anchor if extend or action=='move' else pos,pos)
        if action=='down':self._capture_grid('edit',width,height,edit_id=e['id'])
        return Event('edit_select',e['row_id'],data={'column_id':span.id})

    def pointer(self,action,x,y,width,height,extend=False):
        """Route local pointer input; drag captures receive move/up outside bounds."""
        self._guard()
        if action not in ('down','move','up','cancel','click','double','wheel_up','wheel_down','wheel_left','wheel_right'):return Event()
        _integer(x,-1_000_000_000,1_000_000_000,'pointer x');_integer(y,-1_000_000_000,1_000_000_000,'pointer y')
        _integer(width,0,65535,'width');_integer(height,0,4096,'height')
        c=self._capture
        if c and (c['revision']!=self._revision or c['signature']!=self._column_signature() or (c['width'],c['height'])!=(width,height)):
            self._capture=c=None
        if self._options.disable_mouse or self._pending_paste or action=='cancel':
            self._capture=None;return Event()
        if action=='up':
            self._capture=None
            if c and c['kind']=='column' and not c['moved']:
                hit=self._grid_hit(x,y,width,height)
                if hit and hit[2]is None and hit[1]and hit[1].id==c['column']:return self.click(x,y,width,height)
            return Event()
        if action=='down':self._capture=c=None
        if self.edit:
            if c and c['kind']=='edit' and c['edit_id']!=self.edit['id']:self._capture=c=None
            return self._edit_pointer(action,x,y,width,height,extend)
        if action.startswith('wheel_'):
            self._capture=None
            return self.handle(action[6:],height)
        if action=='move' and not c:return Event()
        if action=='move' and c['kind']=='resize':
            col=next(v for v in self.columns if v.id==c['column']);o=self._column_options.get(col.id,GridColumnOptions())
            value=max(o.min_width,min(o.max_width,c['start_width']+x-c['start_x']))
            if value!=col.width and self.resize_column(col.id,value):
                self._capture_grid('resize',width,height,column=col.id,start_width=c['start_width'],start_x=c['start_x'])
                return Event('resize',data={'column_id':col.id,'width':value})
            return Event()
        if action=='move' and c['kind']=='column':
            span=next((s for s in self.geometry(width,height).columns if s.x<=x<s.x+s.width),None)
            if span and span.id!=c['column']:
                ids=[v.id for v in self.columns];source=ids.index(c['column']);target=ids.index(span.id)
                if self.columns[source].pin==self.columns[target].pin:
                    order=list(self.columns);order.insert(target,order.pop(source))
                    self.set_column_layout([dict(id=v.id,hidden=v.hidden,pin=v.pin)for v in order])
                    self._capture_grid('column',width,height,column=c['column'],moved=True)
                    return Event('columns',data={'column_id':c['column']})
            return Event()
        hit=self._grid_hit(x,y,width,height)
        if not hit:
            if action=='move' and c and c['kind']=='range' and self._hits and self._hits[:2]==(width,height):
                geo=self._hits[2];dy=y-geo.header_rows
                if 0<=x<width and 0<=dy and not dy%geo.stride and y<height-geo.footer_rows:
                    index=geo.top+dy//geo.stride;seen=self._hits[3].get(index)
                    if seen and (index>=self._size() or self._record(index).id!=seen):self._capture=None
            return Event()
        geo,span,row,gutter=hit
        if row is None:
            if action=='down':
                divider=next((s for s in geo.columns if s.x+s.width==x),None) if self._options.vertical_lines and not self._options.disable_resize else None
                if divider:
                    col=next(v for v in self.columns if v.id==divider.id)
                    self._capture_grid('resize',width,height,column=col.id,start_x=x,start_width=col.width)
                    return Event('resize_start',data={'column_id':col.id})
                if span:self._capture_grid('column',width,height,column=span.id,moved=False)
                return Event()
            return self.click(x,y,width,height) if action in ('click','double') else Event()
        if action=='move' and c['kind']!='range':return Event()
        current=self._current();cols=self.visible_columns()
        column=span.id if span else current[1].id if current else ''
        col=next((v for v in cols if v.id==column),None)
        if col is None or self._info(row,col).state.disabled:return Event()
        if action=='move':
            at=self._index(c['anchor_row'])
            if at!=c['anchor_index']or at is None or at>=self._size()or self._record(at).id!=c['anchor_row']:
                self._capture=None;return Event()
            anchor_row,anchor_col=c['anchor_row'],c['anchor_column'];whole=c['whole']
        else:
            anchor_row,anchor_col=self._range_anchor(current)if extend and current else(row.id,column)
            whole=gutter or self._options.selection=='row'
        if not self.focus(row.id,column):return Event()
        if action=='double':return self.handle('activate',height)
        if whole or extend or action=='move':
            self.set_selection(GridRange(anchor_row,cols[0].id if whole else anchor_col,row.id,cols[-1].id if whole else column))
        elif action in ('down','click'):self.selected=None
        if action=='down':
            self._capture_grid('range',width,height,anchor_row=anchor_row,anchor_column=anchor_col,anchor_index=self._index(anchor_row),whole=whole)
        return Event('select',row.id,data={'column_id':column})

    def save_view(self):
        p=self._current(); cols=self.visible_columns()
        return dict(columns=[dict(id=c.id,width=c.width,hidden=c.hidden,pin=c.pin) for c in self.columns],
                    column_options={k:vars(deepcopy(v)) for k,v in self._column_options.items()},
                    row_id=p[0].id if p else '',column_id=p[1].id if p else '',
                    top_row_id=self._record(self.top).id if self.top<self._size() else '',
                    left_column_id=next((c.id for i,c in enumerate(c for c in cols if not c.pin) if i==self.left),''),
                    sort_column=self.sort_column,sort_direction=self.sort_direction,
                    selection=vars(self.selected) if isinstance(self.selected,GridRange) else None,
                    mode=self._options.selection,filter=self.status.filter)

    def restore_view(self, state):
        self._guard()
        data=deepcopy(state)
        # Validate on an isolated model before touching this model or pending work.
        temp=Grid(self.columns,[])
        temp.set_column_layout(data['columns'])
        for item in data['columns']:
            _integer(item['width'],1,4096,'column width')
            next(c for c in temp.columns if c.id==item['id']).width=item['width']
        for id,options in data.get('column_options',{}).items(): temp.set_column_options(id,GridColumnOptions(**options))
        if data.get('sort_column','') not in ('',*[c.id for c in temp.columns]) or data.get('sort_direction','') not in ('','asc','desc') or data.get('mode','cell') not in ('cell','row','range'):
            raise ValueError('invalid grid view state')
        top=self._index(data.get('top_row_id',''))
        if top is not None: self._record(top)
        selected=GridRange(**data['selection']) if data.get('selection') else None
        if selected:
            cols={c.id for c in temp.visible_columns()}
            if selected.anchor_column not in cols or selected.end_column not in cols: raise ValueError('hidden range column')
            for id in (selected.anchor_row,selected.end_row):
                i=self._index(id)
                if i is None or self._record(i).id!=id: raise ValueError('unknown range row')
        self._invalidate(); self.columns=temp.columns; self._column_options=temp._column_options
        self._options.selection=data.get('mode','cell')
        self.top=top if top is not None else 0
        normal=[c for c in self.visible_columns() if not c.pin]
        self.left=next((i for i,c in enumerate(normal) if c.id==data.get('left_column_id','')),0)
        self.sort_column,self.sort_direction=data.get('sort_column',''),data.get('sort_direction','')
        self.status.filter=data.get('filter',''); self.selected=selected
        self.focus(data.get('row_id',''),data.get('column_id',''))
