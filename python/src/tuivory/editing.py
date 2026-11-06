"""Grapheme editing and host-approved grid operations; no database or clipboard I/O."""
from __future__ import annotations
import csv
import io
from dataclasses import dataclass, field
from .drawing import Canvas, Rect, cells, clip, graphemes
from .models import ControlState, Event, unique


class Text:
    def __init__(self, value: str = "", *, read_only: bool = False, secret: bool = False, multiline: bool = True):
        self.value = value
        self.cursor = self.anchor = len(graphemes(value))
        self.read_only, self.secret, self.multiline = read_only, secret, multiline
        self.scroll_x = self.scroll_y = 0
        self._undo: list[tuple[str, int, int]] = []
        self._redo: list[tuple[str, int, int]] = []

    def select(self, anchor: int, cursor: int) -> None:
        n = len(graphemes(self.value))
        self.anchor, self.cursor = max(0, min(n, anchor)), max(0, min(n, cursor))

    def _replace(self, text: str) -> None:
        if self.read_only:
            return
        self._undo.append((self.value, self.cursor, self.anchor))
        self._undo = self._undo[-100:]
        self._redo.clear()
        parts = graphemes(self.value)
        a, b = sorted((self.anchor, self.cursor))
        if not self.multiline:
            text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
        self.value = "".join(parts[:a]) + text + "".join(parts[b:])
        self.cursor = self.anchor = a + len(graphemes(text))

    def handle(self, action: str, text: str = "") -> Event:
        parts = graphemes(self.value)
        if action == "select_all":
            self.select(0, len(parts))
        elif action in ("copy", "cut"):
            a, b = sorted((self.anchor, self.cursor))
            event = Event("copy", text="" if self.secret else "".join(parts[a:b]))
            if action == "cut" and not self.secret:
                self._replace("")
            return event
        elif action in ("undo", "redo") and not self.read_only:
            src, dst = (self._undo, self._redo) if action == "undo" else (self._redo, self._undo)
            if src:
                dst.append((self.value, self.cursor, self.anchor))
                self.value, self.cursor, self.anchor = src.pop()
        elif action in ("left", "right", "home", "end"):
            target = {"left": self.cursor - 1, "right": self.cursor + 1, "home": 0, "end": len(parts)}[action]
            self.select(target, target)
        elif action in ("backspace", "delete"):
            if self.anchor == self.cursor:
                self.select(self.cursor - 1 if action == "backspace" else self.cursor,
                            self.cursor if action == "backspace" else self.cursor + 1)
            self._replace("")
        elif action in ("insert", "paste"):
            self._replace(text)
        elif action == "newline" and self.multiline:
            self._replace("\n")
        return Event("change", text="" if self.secret else self.value)

    def window(self, width: int) -> tuple[str, int, int]:
        parts = graphemes(self.value)
        if self.secret:
            parts = ["*" for _ in parts]
        cursor = max(0, min(len(parts), self.cursor))
        next_width = max(1, cells(parts[cursor])) if cursor < len(parts) else 1
        start = 0
        while start < cursor and cells("".join(parts[start:cursor])) + next_width > width:
            start += 1
        x = cells("".join(parts[start:cursor]))
        # An oversized grapheme is omitted, leaving a valid blank cursor cell.
        if next_width > width:
            return "", 0, 1
        return clip("".join(parts[start:]), width), x, next_width

    def draw(self, canvas: Canvas, rect: Rect, *, focused: bool = True, ascii: bool = False) -> None:
        canvas.fill(rect, "field" if not self.read_only else "surface")
        if not rect.width or not rect.height:
            return
        if not self.multiline:
            value, x, n = self.window(rect.width)
            canvas.write(rect.x, rect.y, value, "field", width=rect.width, preserve_background=True)
            if focused and not self.read_only:
                canvas.set_cursor(rect.x + x, rect.y, n)
            return
        before = "".join(graphemes(self.value)[:self.cursor])
        cursor_y = before.count("\n")
        cursor_x = cells(before.rsplit("\n", 1)[-1])
        self.scroll_y = max(min(self.scroll_y, cursor_y), cursor_y - rect.height + 1, 0)
        self.scroll_x = max(min(self.scroll_x, cursor_x), cursor_x - rect.width + 1, 0)
        rows = self.value.split("\n")
        for y, text in enumerate(rows[self.scroll_y:self.scroll_y + rect.height]):
            x = rect.x - self.scroll_x
            canvas.write(x, rect.y + y, "*" * len(graphemes(text)) if self.secret else text,
                         "field" if not self.read_only else "body", width=rect.width + self.scroll_x, preserve_background=True)
        if focused and not self.read_only:
            canvas.set_cursor(rect.x + cursor_x - self.scroll_x, rect.y + cursor_y - self.scroll_y)


@dataclass
class Field:
    id: str
    kind: str = "text"
    label: str = ""
    value: str = ""
    help: str = ""
    error: str = ""
    required: bool = False
    checked: bool = False
    options: list[tuple[str, str]] = field(default_factory=list)
    state: ControlState = field(default_factory=ControlState)


class Form:
    def __init__(self, fields: list[Field]):
        unique(fields)
        if any(f.kind not in ("text", "password", "textarea", "checkbox", "radio", "select", "button") for f in fields):
            raise ValueError("unknown field kind")
        self.fields = list(fields)
        self.inputs = {f.id: Text(f.value, secret=f.kind == "password", multiline=f.kind == "textarea") for f in fields if f.kind in ("text", "password", "textarea")}
        self.focused = ""
        self.scroll = 0
        self._eligible()

    def _eligible(self) -> list[Field]:
        items = [f for f in self.fields if f.state.focusable]
        if self.focused not in [f.id for f in items]:
            self.focused = items[0].id if items else ""
        return items

    def value(self, id: str) -> str:
        f = next(f for f in self.fields if f.id == id)
        return self.inputs[id].value if id in self.inputs else f.value

    def handle(self, action: str, text: str = "") -> Event:
        items = self._eligible()
        if action == "cancel":
            return Event("cancel")
        if action == "submit":
            missing = [f.id for f in self.fields if not f.state.disabled and f.required and not self.value(f.id)]
            return Event("invalid" if missing else "submit", data=missing)
        if not items:
            return Event()
        i = next(i for i, f in enumerate(items) if f.id == self.focused)
        f = items[i]
        if action in ("next", "previous"):
            self.focused = items[(i + (1 if action == "next" else -1)) % len(items)].id
            return Event("focus", self.focused)
        if not f.state.activatable:
            return Event()
        if action == "activate" and f.kind == "button":
            return Event("activate", f.id)
        if not f.state.editable:
            return Event()
        if f.id in self.inputs:
            event = self.inputs[f.id].handle(action, text)
            # Passwords are available through explicit value(), never display/events.
            return Event(event.kind, f.id, event.text)
        if f.kind in ("checkbox", "radio") and action in ("activate", "toggle"):
            f.checked = not f.checked if f.kind == "checkbox" else True
            return Event("change", f.id, data=f.checked)
        if f.kind == "select" and action in ("left", "right", "up", "down", "activate") and f.options:
            ids = [id for id, _ in f.options]
            at = ids.index(f.value) if f.value in ids else 0
            f.value = ids[(at + (-1 if action in ("left", "up") else 1)) % len(ids)]
            return Event("change", f.id, f.value)
        return Event()

    def click(self, x: int, y: int, height: int = 10) -> Event:
        i = self.scroll + y
        if not 0 <= y < height or not 0 <= i < len(self.fields):
            return Event()
        f = self.fields[i]
        if f.state.disabled:
            return Event()
        self.focused = f.id
        if f.kind in ("button", "checkbox", "radio", "select"):
            return self.handle("activate")
        return Event("focus", f.id)

    def draw(self, canvas: Canvas, rect: Rect, *, focused: bool = True, ascii: bool = False) -> None:
        canvas.fill(rect)
        self._eligible()
        index = next((i for i, f in enumerate(self.fields) if f.id == self.focused), 0)
        self.scroll = max(0, min(self.scroll, index))
        if index >= self.scroll + max(1, rect.height):
            self.scroll = index - max(1, rect.height) + 1
        for y, f in enumerate(self.fields[self.scroll:self.scroll + rect.height]):
            current = focused and self.focused == f.id
            prefix = f.label + ": " if f.label else ""
            role = "disabled" if f.state.disabled else "error" if f.error else "body"
            canvas.write(rect.x, rect.y + y, clip(prefix, rect.width), role, focused=current, width=rect.width)
            start = min(cells(prefix), rect.width)
            width = rect.width - start
            if f.id in self.inputs:
                value, x, n = self.inputs[f.id].window(width)
                canvas.write(rect.x + start, rect.y + y, value.ljust(width - cells(value) + len(value)),
                             "disabled" if f.state.disabled else "field", width=width, preserve_background=True)
                if current and f.state.editable and width:
                    canvas.set_cursor(rect.x + start + x, rect.y + y, n)
            else:
                value = ("[x] " if f.checked else "[ ] ") + f.label if f.kind in ("checkbox", "radio") else (
                    f"[ {f.label} ]" if f.kind == "button" else dict(f.options).get(f.value, f.value))
                canvas.write(rect.x + start, rect.y + y, clip(value, width, True), role, focused=current, width=width)


class Control(Form):
    def __init__(self, field: Field):
        super().__init__([field])


@dataclass
class Column:
    id: str
    label: str = ""
    width: int = 12
    editable: bool = False
    hidden: bool = False
    pin: str = ""


@dataclass
class Record:
    id: str
    cells: dict[str, str | None] = field(default_factory=dict)
    state: ControlState = field(default_factory=ControlState)
    cell_states: dict[str, ControlState] = field(default_factory=dict)


class Grid:
    def __init__(self, columns: list[Column], rows: list[Record]):
        unique(columns)
        unique(rows)
        if any(c.width < 1 or c.pin not in ("", "left", "right") for c in columns):
            raise ValueError("invalid column width/pin")
        self.columns, self.rows = list(columns), list(rows)
        self.row = self.column = self.top = self.left = 0
        self.edit_enabled = False
        self.prepare = None  # Optional host callback(record, column) -> bool.
        self.edit: dict | None = None
        self._serial = self._revision = 0
        self._pending_paste: dict | None = None
        self.query = ""
        self.case_sensitive = False
        self.selected: tuple[int, int, int, int] | None = None

    def visible_columns(self) -> list[Column]:
        return sorted((c for c in self.columns if not c.hidden), key=lambda c: {"left": 0, "": 1, "right": 2}[c.pin])

    def _current(self) -> tuple[Record, Column] | None:
        cols = self.visible_columns()
        if not self.rows or not cols:
            return None
        self.row = max(0, min(len(self.rows) - 1, self.row))
        self.column = max(0, min(len(cols) - 1, self.column))
        return self.rows[self.row], cols[self.column]

    def set_rows(self, rows: list[Record]) -> None:
        unique(rows)
        current = self._current()
        id = current[0].id if current else ""
        self.rows = list(rows)
        self.row = next((i for i, r in enumerate(rows) if r.id == id), 0)
        self.edit = None
        self._pending_paste = None
        self._revision += 1

    def begin_edit(self, first: str | None = None) -> bool:
        current = self._current()
        if current is None or self.edit is not None or not self.edit_enabled:
            return False
        row, column = current
        state = row.cell_states.get(column.id, row.state)
        if not column.editable or not state.editable or self.prepare is not None and not self.prepare(row, column):
            return False
        self._serial += 1
        value = row.cells.get(column.id, "")
        self.edit = dict(id=self._serial, row_id=row.id, column_id=column.id,
                         original=value, null=value is None, buffer=Text(first if first is not None else value or "", multiline=False),
                         pending=False, error="", revision=self._revision)
        return True

    def resolve_edit(self, id: int, *, error: str = "", rows: list[Record] | None = None) -> bool:
        if not self.edit or not self.edit["pending"] or self.edit["id"] != id or self.edit["revision"] != self._revision:
            return False
        if error:
            self.edit["pending"], self.edit["error"] = False, error
            return True
        self.edit = None
        if rows is not None:
            self.set_rows(rows)
        return True

    def handle(self, action: str, height: int = 10, text: str = "") -> Event:
        if self.edit is not None:
            e = self.edit
            if action == "cancel":
                self.edit = None
                return Event("edit_cancel", e["row_id"])
            if e["pending"]:
                return Event()
            if action == "null":
                e["null"] = not e["null"]
                return Event("edit_change", e["row_id"])
            if action in ("submit", "activate"):
                current = self._current()
                if not current or (current[0].id, current[1].id) != (e["row_id"], e["column_id"]):
                    self.edit = None
                    return Event("edit_stale")
                state = current[0].cell_states.get(current[1].id, current[0].state)
                if not state.editable or not current[1].editable or self.prepare is not None and not self.prepare(*current):
                    return Event("edit_denied", e["row_id"])
                e["pending"] = True
                return Event("edit_submit", e["row_id"], data={k: e[k] for k in ("id", "row_id", "column_id")} | {"value": None if e["null"] else e["buffer"].value})
            if action in ("insert", "paste"):
                e["null"] = False
            if not e["null"]:
                e["buffer"].handle(action, text)
            return Event("edit_change", e["row_id"])
        current = self._current()
        if current is None:
            return Event()
        row, column = current
        if action == "activate":
            if self.edit_enabled:
                return Event("edit_begin" if self.begin_edit() else "edit_denied", row.id)
            return Event("edit", row.id, data={"column_id": column.id})
        if action == "copy":
            return Event("copy", row.id, row.cells.get(column.id) or "")
        if action == "details":
            return Event("details", row.id, data={"column_id": column.id, "value": row.cells.get(column.id)})
        if action in ("up", "down", "home", "end", "page_up", "page_down"):
            self.row = max(0, min(len(self.rows) - 1, {"up": self.row - 1, "down": self.row + 1, "home": 0, "end": len(self.rows) - 1, "page_up": self.row - max(1, height - 1), "page_down": self.row + max(1, height - 1)}[action]))
        if action in ("left", "right"):
            self.column = max(0, min(len(self.visible_columns()) - 1, self.column + (-1 if action == "left" else 1)))
        return Event("select", self.rows[self.row].id, data={"column_id": self.visible_columns()[self.column].id})

    def paste(self, text: str, max_cells: int = 10_000, null_text: str | None = None) -> Event:
        if self.edit or self._pending_paste or len(text.encode()) > 16 * 1024 * 1024:
            return Event("paste_rejected")
        values = list(csv.reader(io.StringIO(text), delimiter="\t", quotechar='"', strict=True))
        if not values or not values[0] or any(len(row) != len(values[0]) for row in values):
            return Event("paste_rejected")
        count = len(values) * len(values[0])
        cols = self.visible_columns()
        if not 0 < count <= max_cells or self.row + len(values) > len(self.rows) or self.column + len(values[0]) > len(cols):
            return Event("paste_rejected")
        changes = []
        for dy, line in enumerate(values):
            record = self.rows[self.row + dy]
            for dx, value in enumerate(line):
                column = cols[self.column + dx]
                state = record.cell_states.get(column.id, record.state)
                if not column.editable or not state.editable or self.prepare and not self.prepare(record, column):
                    return Event("paste_rejected")
                changes.append(dict(row_id=record.id, column_id=column.id, value=None if null_text is not None and value == null_text else value))
        self._serial += 1
        self._pending_paste = dict(id=self._serial, changes=changes, revision=self._revision)
        return Event("paste_request", data=self._pending_paste.copy())

    def resolve_paste(self, id: int, rows: list[Record] | None = None) -> bool:
        pending = self._pending_paste
        if pending is None or pending["id"] != id or pending["revision"] != self._revision:
            return False
        # Host must revalidate permissions and perform its own transaction.
        self._pending_paste = None
        if rows is not None:
            self.set_rows(rows)
        return True

    def find(self, query: str, *, previous: bool = False, max_cells: int = 100_000) -> bool:
        cols = self.visible_columns()
        if not query or not cols or not self.rows:
            return False
        total = len(cols) * len(self.rows)
        start = self.row * len(cols) + self.column
        for step in range(1, min(total, max(0, max_cells)) + 1):
            pos = (start + (-step if previous else step)) % total
            row, col = divmod(pos, len(cols))
            value = self.rows[row].cells.get(cols[col].id) or ""
            if query.casefold() in value.casefold():
                self.row, self.column = row, col
                return True
        return False

    def save_view(self) -> dict:
        current = self._current()
        return dict(columns=[dict(id=c.id, width=c.width, hidden=c.hidden, pin=c.pin) for c in self.columns],
                    row_id=current[0].id if current else "", column_id=current[1].id if current else "", top=self.top, left=self.left)

    def restore_view(self, state: dict) -> None:
        raw = state["columns"]
        by_id = {c.id: c for c in self.columns}
        if len(raw) != len(by_id) or {c["id"] for c in raw} != set(by_id) or all(c["hidden"] for c in raw):
            raise ValueError("incompatible view state")
        if any(c["width"] < 1 or c["pin"] not in ("", "left", "right") for c in raw):
            raise ValueError("invalid view state")
        for c in raw:
            target = by_id[c["id"]]
            target.width, target.hidden, target.pin = c["width"], c["hidden"], c["pin"]
        self.columns = [by_id[c["id"]] for c in raw]
        self.row = next((i for i, r in enumerate(self.rows) if r.id == state["row_id"]), 0)
        self.column = next((i for i, c in enumerate(self.visible_columns()) if c.id == state["column_id"]), 0)
        self.top, self.left = max(0, state["top"]), max(0, state["left"])
        self.edit = None

    def click(self, x: int, y: int, width: int, height: int) -> Event:
        if y <= 0 or y >= height or x < 0 or x >= width:
            return Event()
        row = self.top + y - 1
        if row >= len(self.rows):
            return Event()
        offset = 0
        for index, c in enumerate(self.visible_columns()):
            if offset <= x < offset + c.width + 1:
                if self.edit:
                    return Event()
                self.row, self.column = row, index
                return Event("select", self.rows[row].id, data={"column_id": c.id})
            offset += c.width + 1
        return Event()

    def draw(self, canvas: Canvas, rect: Rect, *, focused: bool = True, ascii: bool = False) -> None:
        canvas.fill(rect)
        current = self._current()
        if current is None or rect.width <= 0 or rect.height <= 0:
            return
        h = max(1, rect.height - 1)
        self.top = max(0, min(self.top, self.row))
        if self.row >= self.top + h:
            self.top = self.row - h + 1
        x = rect.x
        for ci, column in enumerate(self.visible_columns()):
            w = min(column.width, rect.x + rect.width - x)
            if w <= 0:
                break
            canvas.write(x, rect.y, clip(column.label or column.id, w, True), "header", width=w)
            for dy, row in enumerate(self.rows[self.top:self.top + h]):
                y = rect.y + 1 + dy
                state = row.cell_states.get(column.id, ControlState())
                current_cell = self.top + dy == self.row and ci == self.column
                value = row.cells.get(column.id, "")
                e = self.edit
                editing = e and e["row_id"] == row.id and e["column_id"] == column.id
                role = "disabled" if row.state.disabled or state.disabled else "error" if state.invalid else "edited" if state.edited else "selection" if current_cell else "body"
                if editing:
                    role = "hint" if e["pending"] else "error" if e["error"] else "field"
                    text, cursor_x, glyph_width = e["buffer"].window(max(0, w - int(state.edited)))
                    if e["null"]:
                        text = "NULL"
                    if focused and not e["null"] and not e["pending"] and w > int(state.edited):
                        canvas.set_cursor(x + int(state.edited) + cursor_x, y, glyph_width)
                else:
                    text = "NULL" if value is None else value
                text = ("*" if state.edited else "") + text
                text = clip(text, w)
                canvas.write(x, y, text + " " * max(0, w - cells(text)), role,
                             focused=focused and current_cell, width=w, preserve_background=True)
            x += column.width
            if x < rect.x + rect.width:
                for y in range(rect.y, rect.y + rect.height):
                    canvas.write(x, y, "|" if ascii else "│", "hint")
            x += 1
