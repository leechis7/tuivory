/** Independent grid state. Returned requests never write application data. */
import {
  Canvas,
  ControlState,
  Text,
  TextDocument,
  cells,
  clip,
  graphemes,
  fold,
  rect,
} from "./index.js";
import type { Event, Rect } from "./index.js";

type Dict<T> = { [id: string]: T };
const copy = <T>(v: T): T =>
  Array.isArray(v)
    ? (v.map(copy) as T)
    : v !== null && typeof v === "object"
      ? (Object.fromEntries(
          Object.entries(v).map(([k, x]) => [k, copy(x)]),
        ) as T)
      : v;
function integer(n: number, lo: number, hi: number, name: string): number {
  if (!Number.isSafeInteger(n) || n < lo || n > hi)
    throw new Error(`invalid ${name}`);
  return n;
}
function unique(items: { id: string }[]): void {
  if (
    items.some((i) => !i.id || typeof i.id !== "string") ||
    new Set(items.map((i) => i.id)).size !== items.length
  )
    throw new Error("IDs must be nonempty and unique");
}
const event = (kind = "", id = "", text = "", data: unknown = null): Event => ({
  kind,
  id,
  text,
  data,
});
const utf8Size = (s: string): number => {
  let n = 0;
  for (const c of s) {
    const p = c.codePointAt(0)!;
    if (p >= 0xd800 && p <= 0xdfff) throw new Error("invalid Unicode");
    n += p < 128 ? 1 : p < 2048 ? 2 : p < 65536 ? 3 : 4;
  }
  return n;
};
const clean = (s: string): string =>
  s.replace(/[\u0000-\u001f\u007f-\u009f]/g, " ");
export interface Column {
  id: string;
  label?: string;
  width?: number;
  editable?: boolean;
  hidden?: boolean;
  pin?: "" | "left" | "right";
}
export interface Record {
  id: string;
  cells: Dict<string | null>;
  state?: Partial<ControlState>;
  cellStates?: Dict<Partial<ControlState>>;
}
export interface GridSource {
  readonly length: number;
  row(index: number): Record;
  indexOf(id: string): number | undefined;
}
export class MemoryRows implements GridSource {
  private readonly items: Record[];
  private readonly indices: Map<string, number>;
  constructor(rows: Record[]) {
    unique(rows);
    for (const r of rows)
      if (utf8Size(r.id) > 1000000 || Object.keys(r.cells).length > 65536)
        throw new Error("invalid grid record");
    for (const r of rows)
      for (const v of Object.values(r.cells))
        if (v !== null) {
          if (typeof v !== "string") throw new Error("invalid grid value");
          if (utf8Size(v) > 16 * 1024 * 1024)
            throw new Error("grid cell exceeds byte limit");
        }
    this.items = copy(rows);
    this.indices = new Map(rows.map((r, i) => [r.id, i]));
  }
  get length(): number {
    return this.items.length;
  }
  row(i: number): Record {
    integer(i, 0, this.length - 1, "row index");
    return copy(this.items[i]);
  }
  indexOf(id: string): number | undefined {
    return this.indices.get(id);
  }
}
export function parseGridTSV(text: string, maxCells = 10000): string[][] {
  integer(maxCells, 1, 1000000, "cell limit");
  if (utf8Size(text) > 16 * 1024 * 1024)
    throw new Error("paste exceeds byte limit");
  const rows: string[][] = [];
  let row: string[] = [],
    value = "",
    quoted = false,
    closed = false,
    started = false,
    count = 0;
  const finish = () => {
    if (++count > maxCells) throw new Error("paste exceeds cell limit");
    row.push(value);
    value = "";
    closed = started = false;
  };
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          value += '"';
          i++;
          continue;
        }
        quoted = false;
        closed = true;
      } else value += c;
      continue;
    }
    const nl = c === "\n" || (c === "\r" && text[i + 1] === "\n");
    if (c === "\t" || nl) {
      if (c === "\t" || row.length || started || closed || value) finish();
      if (nl) {
        if (row.length) {
          rows.push(row);
          row = [];
        }
        if (c === "\r") i++;
      }
    } else if (closed) throw new Error("characters after closing quote");
    else if (c === '"') {
      if (started || value) throw new Error("quote inside unquoted field");
      quoted = started = true;
    } else {
      value += c;
      started = true;
    }
  }
  if (quoted) throw new Error("unterminated quoted field");
  if (row.length || started || closed || value) {
    finish();
    rows.push(row);
  }
  if (!rows.length || rows.some((r) => r.length !== rows[0].length))
    throw new Error("empty or ragged paste");
  return rows;
}
export function formatGridTSV(rows: string[][]): string {
  return rows
    .map((r) =>
      r
        .map((s) =>
          !s || /[\t\n\r"]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s,
        )
        .join("\t"),
    )
    .join("\n");
}
export class GridOptions {
  rowNumbers = false;
  verticalLines = false;
  horizontalLines = false;
  striped = false;
  useSurface = false;
  hideHeader = false;
  statusBar = false;
  ascii = false;
  highlightCell = true;
  highlightRow = false;
  preserveEdited = true;
  showCellMarkers = false;
  disableKeyboard = false;
  disableMouse = false;
  disableEditing = false;
  disableCopy = false;
  disableResize = false;
  disableHeaderSort = false;
  padding = 0;
  rowSpacing = 0;
  gutterWidth = 0;
  maxCopyCells = 10000;
  selection: "cell" | "row" | "range" = "cell";
  statusFields = [
    "position",
    "column",
    "selection",
    "sort",
    "filter",
    "loading",
    "more",
    "meta",
    "error",
  ];
  constructor(options: Partial<GridOptions> = {}) {
    Object.assign(this, copy(options));
  }
  withDensity(density: string): GridOptions {
    if (!["compact", "normal", "comfortable"].includes(density))
      throw new Error("invalid grid density");
    return new GridOptions({
      ...this,
      padding: Number(density !== "compact"),
      rowSpacing: Number(density === "comfortable"),
    });
  }
}
export function gridPreset(name = "simple"): GridOptions {
  if (name === "" || name === "simple") return new GridOptions();
  if (name === "data")
    return new GridOptions({
      rowNumbers: true,
      verticalLines: true,
      useSurface: true,
      statusBar: true,
      padding: 1,
      highlightRow: true,
      showCellMarkers: true,
    });
  throw new Error("unknown grid preset");
}
export class GridColumnOptions {
  align: "left" | "right" | "center" | "auto" = "left";
  minWidth = 1;
  maxWidth = 4096;
  autoFit = false;
  expand = 0;
  overflow: "clip" | "ellipsis" | "scroll" = "ellipsis";
  constructor(options: Partial<GridColumnOptions> = {}) {
    Object.assign(this, copy(options));
  }
}
export class GridCellInfo {
  display = "";
  hasDisplay = false;
  null = false;
  numeric = false;
  state: Partial<ControlState> = {};
  metadata = "";
  constructor(options: Partial<GridCellInfo> = {}) {
    Object.assign(this, copy(options));
  }
}
export interface GridRange {
  anchorRow: string;
  anchorColumn: string;
  endRow: string;
  endColumn: string;
}
export class GridLabels {
  nullText = "NULL";
  loading = "loading";
  empty = "empty";
  range = "range";
  more = "more";
  constructor(labels: Partial<GridLabels> = {}) {
    Object.assign(this, copy(labels));
  }
}
export class GridDataStatus {
  totalRows = 0;
  metadata = "";
  filter = "";
  error = "";
  loading = false;
  hasMore = false;
  constructor(options: Partial<GridDataStatus> = {}) {
    Object.assign(this, copy(options));
  }
}
export interface GridSpan {
  id: string;
  x: number;
  width: number;
}
export interface GridGeometry {
  top: number;
  left: number;
  gutter: number;
  headerRows: number;
  footerRows: number;
  bodyRows: number;
  stride: number;
  columns: GridSpan[];
}
export interface GridValue {
  text: string;
  null: boolean;
}
export interface GridEditOptions {
  enabled?: boolean;
  startTyping?: boolean;
  allowNull?: boolean;
  prepare?:
    ((row: Record, column: Column) => GridValue | boolean | null) | null;
}
export interface GridEdit {
  id: number;
  rowId: string;
  columnId: string;
  original: string | null;
  null: boolean;
  buffer: Text;
  pending: boolean;
  error: string;
  revision: number;
  move: string;
}
export interface GridChange {
  rowId: string;
  columnId: string;
  value: string | null;
}
export interface GridPasteRequest {
  id: number;
  changes: GridChange[];
  revision: number;
}
export interface GridViewState {
  columns: {
    id: string;
    width: number;
    hidden: boolean;
    pin: "" | "left" | "right";
  }[];
  columnOptions: Dict<Partial<GridColumnOptions>>;
  rowId: string;
  columnId: string;
  topRowId: string;
  leftColumnId: string;
  sortColumn: string;
  sortDirection: string;
  selection: GridRange | null;
  mode: "cell" | "row" | "range";
  filter: string;
}
type GridCaptureMode =
  | { kind: "resize"; column: string; startWidth: number; startX: number }
  | { kind: "column"; column: string; moved: boolean }
  | {
      kind: "range";
      anchorRow: string;
      anchorColumn: string;
      anchorIndex: number | undefined;
      whole: boolean;
    }
  | { kind: "edit"; editId: number };
type GridCapture = GridCaptureMode & {
  width: number;
  height: number;
  revision: number;
  signature: string;
};
type GridHit = {
  geo: GridGeometry;
  span: GridSpan | undefined;
  row: Record | null;
  gutter: boolean;
};
export class Grid {
  columns: Column[];
  private source: GridSource;
  row = 0;
  column = 0;
  top = 0;
  left = 0;
  editEnabled = false;
  allowNull = false;
  startTyping = false;
  prepare:
    ((row: Record, column: Column) => GridValue | boolean | null) | null = null;
  cellInfo: ((row: Record, column: Column) => GridCellInfo) | null = null;
  edit: GridEdit | null = null;
  private pasteRequest: GridPasteRequest | null = null;
  private serial = 0;
  private currentRevision = 0;
  private appliedRevision = 0;
  query = "";
  caseSensitive = false;
  useDisplay = false;
  selected: GridRange | null = null;
  sortColumn = "";
  sortDirection = "";
  status = new GridDataStatus();
  private labelConfig = new GridLabels();
  private config = new GridOptions();
  private columnConfig: Dict<GridColumnOptions> = {};
  private cellPan: Dict<number> = {};
  private hits: {
    width: number;
    height: number;
    geometry: GridGeometry;
    rows: Map<number, string>;
    signature: string;
  } | null = null;
  private capture: GridCapture | null = null;
  private paintKey = "";
  private callback = false;
  constructor(columns: Column[], rows: Record[] | GridSource) {
    if (columns.length > 65536) throw new Error("too many grid columns");
    unique(columns);
    for (const c of columns) {
      if (utf8Size(c.id) > 1000000 || utf8Size(c.label ?? "") > 1000000)
        throw new Error("invalid grid column text");
      integer(c.width ?? 12, 1, 4096, "column width");
      if (!["", "left", "right"].includes(c.pin ?? ""))
        throw new Error("invalid column pin");
    }
    this.columns = copy(columns);
    this.source = Array.isArray(rows) ? new MemoryRows(rows) : rows;
    integer(this.sourceSize(), 0, 1000000000, "row count");
  }
  get rows(): Record[] {
    return Array.from({ length: this.sourceSize() }, (_, i) => this.record(i));
  }
  get options(): GridOptions {
    return new GridOptions(this.config);
  }
  get revision(): number {
    return this.currentRevision;
  }
  get pendingPaste(): GridPasteRequest | null {
    return copy(this.pasteRequest);
  }
  get rowId(): string {
    return this.current()?.[0].id ?? "";
  }
  get columnId(): string {
    return this.current()?.[1].id ?? "";
  }
  visibleColumns(): Column[] {
    return this.columns
      .filter((c) => !c.hidden)
      .sort(
        (a, b) =>
          ({ left: 0, "": 1, right: 2 })[a.pin ?? ""] -
          { left: 0, "": 1, right: 2 }[b.pin ?? ""],
      );
  }
  private guard(): void {
    if (this.callback) throw new Error("grid mutation inside callback");
  }
  private sourceCall<T>(fn: () => T): T {
    if (this.callback) throw new Error("recursive grid source callback");
    this.callback = true;
    try {
      return copy(fn());
    } finally {
      this.callback = false;
    }
  }
  private sourceSize(): number {
    return integer(
      this.sourceCall(() => this.source.length),
      0,
      1000000000,
      "row count",
    );
  }
  private sourceIndex(id: string): number | undefined {
    const i = this.sourceCall(() => this.source.indexOf(id));
    if (i !== undefined) integer(i, 0, this.sourceSize() - 1, "source index");
    return i;
  }
  get labels(): GridLabels {
    return new GridLabels(this.labelConfig);
  }
  setLabels(labels: GridLabels): void {
    this.guard();
    const value = new GridLabels(labels);
    for (const text of Object.values(value))
      if (typeof text !== "string" || utf8Size(text) > 1000000)
        throw new Error("invalid grid label");
    this.labelConfig = value;
  }
  private record(i: number): Record {
    integer(i, 0, this.sourceSize() - 1, "row index");
    const r = this.sourceCall(() => this.source.row(i));
    if (!r.id || this.sourceIndex(r.id) !== i)
      throw new Error("inconsistent grid source IDs");
    return r;
  }
  private invoke<T>(fn: (r: Record, c: Column) => T, r: Record, c: Column): T {
    if (this.callback) throw new Error("recursive grid callback");
    this.callback = true;
    try {
      return fn(copy(r), copy(c));
    } finally {
      this.callback = false;
    }
  }
  private current(): [Record, Column] | null {
    const cols = this.visibleColumns(),
      n = this.sourceSize();
    if (!cols.length || !n) return null;
    this.row = Math.max(0, Math.min(n - 1, this.row));
    this.column = Math.max(0, Math.min(cols.length - 1, this.column));
    let r = this.record(this.row);
    if (r.state?.disabled) {
      let found = false,
        scanned = 0;
      for (let i = this.row + 1; i < n && scanned < 100000; i++, scanned++) {
        r = this.record(i);
        if (!r.state?.disabled) {
          this.row = i;
          found = true;
          break;
        }
      }
      if (!found)
        for (let i = this.row - 1; i >= 0 && scanned < 100000; i--, scanned++) {
          r = this.record(i);
          if (!r.state?.disabled) {
            this.row = i;
            found = true;
            break;
          }
        }
      if (!found) return null;
    }
    return [r, cols[this.column]];
  }
  private info(r: Record, c: Column): GridCellInfo {
    const info = new GridCellInfo(
        this.cellInfo ? this.invoke(this.cellInfo, r, c) : {},
      ),
      a = r.state ?? {},
      b = r.cellStates?.[c.id] ?? {},
      d = info.state;
    info.state = new ControlState({
      disabled: !!(a.disabled || b.disabled || d.disabled),
      read_only: !!(a.read_only || b.read_only || d.read_only),
      busy: !!(a.busy || b.busy || d.busy),
      selected: !!(a.selected || b.selected || d.selected),
      edited: !!(a.edited || b.edited || d.edited),
      invalid: !!(a.invalid || b.invalid || d.invalid),
    });
    info.null = info.null || r.cells[c.id] === null;
    return info;
  }
  private prepared(r: Record, c: Column): GridValue | null {
    const result = this.prepare ? this.invoke(this.prepare, r, c) : true;
    if (result === null || result === false) return null;
    if (result === true)
      return { text: r.cells[c.id] ?? "", null: this.info(r, c).null };
    if (
      typeof result !== "object" ||
      typeof result.text !== "string" ||
      typeof result.null !== "boolean"
    )
      throw new Error("invalid grid preparation result");
    utf8Size(result.text);
    return copy(result);
  }
  private editable(r: Record, c: Column): boolean {
    return (
      !this.config.disableEditing &&
      !c.hidden &&
      !!c.editable &&
      new ControlState(this.info(r, c).state).editable &&
      this.prepared(r, c) !== null
    );
  }
  setEditOptions(options: GridEditOptions): void {
    if (
      options.prepare !== undefined &&
      options.prepare !== null &&
      typeof options.prepare !== "function"
    )
      throw new Error("invalid grid prepare callback");
    this.invalidate();
    this.editEnabled = !!options.enabled;
    this.startTyping = !!options.startTyping;
    this.allowNull = !!options.allowNull;
    this.prepare = options.prepare ?? null;
  }
  setCellInfo(callback: ((r: Record, c: Column) => GridCellInfo) | null): void {
    if (callback !== null && typeof callback !== "function")
      throw new Error("invalid cell info callback");
    this.invalidate();
    this.cellInfo = callback;
  }
  details(): TextDocument | null {
    const p = this.current();
    if (!p || this.info(...p).state.disabled) return null;
    return TextDocument.viewer(p[0].cells[p[1].id] ?? "");
  }
  private invalidate(): void {
    if (this.callback) throw new Error("grid mutation inside callback");
    this.currentRevision++;
    this.edit = this.pasteRequest = this.hits = this.capture = null;
  }
  setRows(rows: Record[]): void {
    this.setSource(new MemoryRows(rows));
  }
  setSource(source: GridSource): void {
    if (this.callback) throw new Error("grid mutation inside callback");
    integer(
      this.sourceCall(() => source.length),
      0,
      1000000000,
      "row count",
    );
    const id = this.current()?.[0].id ?? "",
      i = id ? this.sourceCall(() => source.indexOf(id)) : undefined;
    if (i !== undefined) {
      integer(i, 0, this.sourceCall(() => source.length) - 1, "source index");
      if (this.sourceCall(() => source.row(i)).id !== id)
        throw new Error("inconsistent grid source IDs");
    }
    const selection = this.selected;
    this.source = source;
    this.row = i ?? 0;
    this.selected = null;
    if (selection)
      try {
        this.setSelection(selection);
      } catch {}
    this.invalidate();
  }
  focus(rowId: string, columnId: string): boolean {
    this.guard();
    const i = this.sourceIndex(rowId),
      cols = this.visibleColumns(),
      j = cols.findIndex((c) => c.id === columnId);
    if (i === undefined || j < 0 || i < 0 || i >= this.sourceSize())
      return false;
    const r = this.record(i);
    if (r.id !== rowId || r.state?.disabled) return false;
    if (
      this.edit &&
      (rowId !== this.edit.rowId || columnId !== this.edit.columnId)
    )
      this.edit = null;
    this.row = i;
    this.column = j;
    return true;
  }
  setOptions(options: GridOptions): void {
    const o = new GridOptions(options);
    integer(o.padding, 0, 8, "padding");
    integer(o.rowSpacing, 0, 4, "row spacing");
    integer(o.gutterWidth, 0, 128, "gutter width");
    integer(o.maxCopyCells, 1, 1000000, "copy limit");
    const allowed = [
      "position",
      "column",
      "selection",
      "sort",
      "filter",
      "loading",
      "more",
      "meta",
      "error",
    ];
    if (
      !["cell", "row", "range"].includes(o.selection) ||
      new Set(o.statusFields).size !== o.statusFields.length ||
      o.statusFields.some((f) => !allowed.includes(f))
    )
      throw new Error("invalid grid options");
    this.invalidate();
    this.config = o;
  }
  setColumnOptions(id: string, options: GridColumnOptions): void {
    const c = this.columns.find((c) => c.id === id);
    if (!c) throw new Error("unknown column");
    const o = new GridColumnOptions(options);
    integer(o.minWidth, 1, 4096, "minimum width");
    integer(o.maxWidth, o.minWidth, 4096, "maximum width");
    integer(o.expand, 0, 4096, "expansion");
    if (
      !["left", "right", "center", "auto"].includes(o.align) ||
      !["clip", "ellipsis", "scroll"].includes(o.overflow)
    )
      throw new Error("invalid column options");
    this.invalidate();
    this.columnConfig[id] = o;
    c.width = Math.max(o.minWidth, Math.min(o.maxWidth, c.width ?? 12));
  }
  setColumnLayout(
    layout: { id: string; hidden?: boolean; pin?: "" | "left" | "right" }[],
  ): void {
    unique(layout);
    if (
      layout.length !== this.columns.length ||
      layout.some(
        (x) =>
          !this.columns.some((c) => c.id === x.id) ||
          !["", "left", "right"].includes(x.pin ?? ""),
      )
    )
      throw new Error("incompatible column layout");
    const byId = new Map(this.columns.map((c) => [c.id, copy(c)]));
    for (const item of layout) {
      const c = byId.get(item.id)!;
      c.hidden = !!item.hidden;
      c.pin = item.pin ?? "";
    }
    const current = this.current();
    this.invalidate();
    this.columns = layout.map((x) => byId.get(x.id)!);
    if (current) this.focus(current[0].id, current[1].id);
  }
  private workValid(request: {
    rowId: string;
    columnId: string;
    revision: number;
  }): boolean {
    if (request.revision !== this.currentRevision) return false;
    const i = this.sourceIndex(request.rowId),
      c = this.visibleColumns().find((c) => c.id === request.columnId);
    if (i === undefined || !c || i < 0 || i >= this.sourceSize()) return false;
    const r = this.record(i);
    return r.id === request.rowId && this.editable(r, c);
  }
  beginEdit(first?: string): boolean {
    this.guard();
    const current = this.current();
    if (
      !current ||
      this.edit ||
      this.pasteRequest ||
      !this.editEnabled ||
      !this.editable(...current)
    )
      return false;
    const [r, c] = current,
      prepared = this.prepared(r, c);
    if (!prepared) return false;
    const value = prepared.text;
    this.edit = {
      id: ++this.serial,
      rowId: r.id,
      columnId: c.id,
      original: value,
      null: first === undefined ? prepared.null : false,
      buffer: new Text(first ?? value, { multiline: false }),
      pending: false,
      error: "",
      revision: this.currentRevision,
      move: "",
    };
    this.hits = null;
    return true;
  }
  resolveEdit(id: number, error = "", rows?: Record[]): boolean {
    this.guard();
    const e = this.edit;
    if (!e || !e.pending || e.id !== id || e.revision !== this.currentRevision)
      return false;
    if (!this.workValid(e)) {
      this.edit = null;
      return false;
    }
    const replacement = rows ? new MemoryRows(rows) : null;
    if (error) {
      e.pending = false;
      e.error = error;
      return true;
    }
    this.edit = null;
    if (replacement) this.setSource(replacement);
    this.focus(e.rowId, e.columnId);
    if (e.move && this.moveEditable(e.move === "previous")) this.beginEdit();
    return true;
  }
  private moveEditable(previous = false): boolean {
    const cols = this.visibleColumns();
    if (!cols.length) return false;
    const step = previous ? -1 : 1,
      start = this.row * cols.length + this.column;
    for (
      let p = start + step, scanned = 0;
      p >= 0 && p < this.sourceSize() * cols.length && scanned < 100000;
      p += step, scanned++
    ) {
      const i = Math.floor(p / cols.length),
        j = p % cols.length,
        r = this.record(i);
      if (this.editable(r, cols[j])) return this.focus(r.id, cols[j].id);
    }
    return false;
  }
  handle(action: string, height = 10, text = ""): Event {
    this.guard();
    integer(height, 0, 4096, "height");
    if (this.config.disableKeyboard) return event();
    this.capture = null;
    if (
      !this.edit &&
      [
        "select_up",
        "select_down",
        "select_left",
        "select_right",
        "select_home",
        "select_end",
        "select_page_up",
        "select_page_down",
      ].includes(action)
    )
      return this.extendNavigation(action.slice(7), height);
    const e = this.edit;
    if (e) {
      if (action === "cancel") {
        this.edit = null;
        return event("edit_cancel", e.rowId);
      }
      if (!this.workValid(e)) {
        this.edit = null;
        return event("edit_stale");
      }
      if (e.pending) return event();
      if (action === "null") {
        if (!this.allowNull) return event();
        e.null = !e.null;
        e.error = "";
      } else if (["submit", "activate", "next", "previous"].includes(action)) {
        e.id = ++this.serial;
        e.pending = true;
        e.error = "";
        e.move = ["next", "previous"].includes(action) ? action : "";
        return event("edit_submit", e.rowId, "", {
          id: e.id,
          row_id: e.rowId,
          column_id: e.columnId,
          value: e.null ? null : e.buffer.value,
        });
      } else {
        if (["insert", "paste", "backspace", "delete"].includes(action)) {
          e.null = false;
          e.error = "";
        }
        const out = !e.null ? e.buffer.handle(action, text) : event();
        if (["copy", "cut"].includes(out.kind)) return out;
      }
      return event("edit_change", e.rowId);
    }
    const current = this.current();
    if (!current) return event();
    const [r, c] = current;
    if (["activate", "edit"].includes(action))
      return event(this.beginEdit() ? "edit_begin" : "edit_denied", r.id);
    if (action === "insert" && text && this.startTyping)
      return event(this.beginEdit(text) ? "edit_begin" : "edit_denied", r.id);
    if (action === "copy") return this.copySelection();
    if (action === "details")
      return this.info(r, c).state.disabled
        ? event()
        : event("details", r.id, "", {
            column_id: c.id,
            value: r.cells[c.id] ?? "",
          });
    if (
      ["sort", "filter", "search", "page_next", "page_previous"].includes(
        action,
      )
    )
      return this.request(action.replace("page_", ""), text);
    const moves: Dict<number> = {
      up: this.row - 1,
      down: this.row + 1,
      home: 0,
      end: this.sourceSize() - 1,
      page_up: this.row - Math.max(1, height - 1),
      page_down: this.row + Math.max(1, height - 1),
    };
    if (action in moves) {
      const direction = ["up", "home", "page_up"].includes(action) ? -1 : 1;
      let target = Math.max(0, Math.min(this.sourceSize() - 1, moves[action]));
      while (target >= 0 && target < this.sourceSize()) {
        if (!this.record(target).state?.disabled) {
          this.row = target;
          break;
        }
        target += direction;
      }
    } else if (["left", "right"].includes(action))
      this.column = Math.max(
        0,
        Math.min(
          this.visibleColumns().length - 1,
          this.column + (action === "left" ? -1 : 1),
        ),
      );
    else if (action !== "select") return event();
    const p = this.current();
    return p ? event("select", p[0].id, "", { column_id: p[1].id }) : event();
  }
  paste(text: string, maxCells = 10000, nullText?: string): Event {
    this.guard();
    if (this.edit || this.pasteRequest) return event("paste_rejected");
    let values: string[][];
    try {
      values = parseGridTSV(text, maxCells);
    } catch {
      return event("paste_rejected");
    }
    const cols = this.visibleColumns();
    if (
      !cols.length ||
      this.row + values.length > this.sourceSize() ||
      this.column + values[0].length > cols.length
    )
      return event("paste_rejected");
    const changes: GridChange[] = [];
    for (let dy = 0; dy < values.length; dy++) {
      const r = this.record(this.row + dy);
      for (let dx = 0; dx < values[dy].length; dx++) {
        const c = cols[this.column + dx],
          v = values[dy][dx];
        if (!this.editable(r, c)) return event("paste_rejected");
        changes.push({
          rowId: r.id,
          columnId: c.id,
          value: nullText !== undefined && v === nullText ? null : v,
        });
      }
    }
    this.pasteRequest = {
      id: ++this.serial,
      changes,
      revision: this.currentRevision,
    };
    return event("paste_request", "", "", copy(this.pasteRequest));
  }
  resolvePaste(id: number, rows?: Record[]): boolean {
    this.guard();
    const p = this.pasteRequest;
    if (!p || p.id !== id || p.revision !== this.currentRevision) return false;
    if (
      !p.changes.every((c) => this.workValid({ ...c, revision: p.revision }))
    ) {
      this.pasteRequest = null;
      return false;
    }
    const replacement = rows ? new MemoryRows(rows) : null;
    this.pasteRequest = null;
    if (replacement) this.setSource(replacement);
    return true;
  }
  cancelPaste(): void {
    this.guard();
    this.pasteRequest = null;
  }
  find(query: string, previous = false, maxCells = 100000): boolean {
    this.guard();
    integer(maxCells, 1, 1000000, "find limit");
    const cols = this.visibleColumns(),
      total = cols.length * this.sourceSize();
    if (!query || !total || this.edit || this.pasteRequest) return false;
    this.query = query;
    const needle = this.caseSensitive ? query : fold(query),
      start = this.row * cols.length + this.column;
    for (let step = 1; step <= Math.min(total, maxCells); step++) {
      const at = (start + (previous ? -step : step) + total) % total,
        i = Math.floor(at / cols.length),
        j = at % cols.length,
        r = this.record(i),
        c = cols[j],
        info = this.info(r, c);
      if (info.state.disabled) continue;
      const value =
        this.useDisplay && info.hasDisplay
          ? info.display
          : this.useDisplay && info.null
            ? this.labelConfig.nullText
            : (r.cells[c.id] ?? "");
      if ((this.caseSensitive ? value : fold(value)).includes(needle)) {
        this.row = i;
        this.column = j;
        return true;
      }
    }
    return false;
  }
  request(kind: string, text = ""): Event {
    this.guard();
    if (!["sort", "filter", "search", "next", "previous"].includes(kind))
      throw new Error("unknown grid request");
    if (kind === "sort" && this.config.disableHeaderSort) return event();
    const current = this.current();
    this.invalidate();
    return event(kind + "_request", current?.[0].id ?? "", text, {
      revision: this.currentRevision,
      column_id: current?.[1].id ?? "",
    });
  }
  applySource(revision: number, source: GridSource): boolean {
    if (revision !== this.currentRevision || revision <= this.appliedRevision)
      return false;
    this.setSource(source);
    this.appliedRevision = revision;
    return true;
  }
  setSelection(selection: GridRange | null): void {
    this.guard();
    if (selection === null) {
      this.selected = null;
      return;
    }
    const cols = new Set(this.visibleColumns().map((c) => c.id));
    for (const [rid, cid] of [
      [selection.anchorRow, selection.anchorColumn],
      [selection.endRow, selection.endColumn],
    ]) {
      const i = this.sourceIndex(rid);
      if (
        i === undefined ||
        i < 0 ||
        i >= this.sourceSize() ||
        this.record(i).id !== rid ||
        !cols.has(cid)
      )
        throw new Error("unknown range ID");
    }
    this.selected = copy(selection);
  }
  private selectionBounds(): [number, number, number, number] | null {
    const cols = this.visibleColumns();
    if (!cols.length || !this.sourceSize()) return null;
    if (this.selected) {
      const s = this.selected,
        rows = [this.sourceIndex(s.anchorRow), this.sourceIndex(s.endRow)],
        cs = [
          cols.findIndex((c) => c.id === s.anchorColumn),
          cols.findIndex((c) => c.id === s.endColumn),
        ];
      if (rows.some((x) => x === undefined) || cs.some((x) => x < 0))
        return null;
      return [
        Math.min(...(rows as number[])),
        Math.min(...cs),
        Math.max(...(rows as number[])),
        Math.max(...cs),
      ];
    }
    return [
      this.row,
      this.config.selection === "row" ? 0 : this.column,
      this.row,
      this.config.selection === "row" ? cols.length - 1 : this.column,
    ];
  }
  copySelection(display = false, nullText = "NULL"): Event {
    if (this.config.disableCopy) return event();
    const bounds = this.selectionBounds();
    if (!bounds) return event();
    const [a, b, c, d] = bounds,
      cols = this.visibleColumns();
    if (
      Math.min(a, b) < 0 ||
      c >= this.sourceSize() ||
      d >= cols.length ||
      (c - a + 1) * (d - b + 1) > this.config.maxCopyCells
    )
      return event("copy_rejected");
    const values: string[][] = [];
    let byteCount = 0;
    for (let i = a; i <= c; i++) {
      const r = this.record(i),
        line: string[] = [];
      for (let j = b; j <= d; j++) {
        const col = cols[j],
          info = this.info(r, col);
        if (info.state.disabled) return event("copy_rejected");
        const value =
          display && info.hasDisplay
            ? info.display
            : info.null
              ? nullText
              : (r.cells[col.id] ?? "");
        byteCount += utf8Size(value);
        if (byteCount > 16 * 1024 * 1024) return event("copy_rejected");
        line.push(value);
      }
      values.push(line);
    }
    return event("copy", "", formatGridTSV(values));
  }
  resizeColumn(id: string, width: number): boolean {
    if (this.config.disableResize) return false;
    const c = this.columns.find((c) => c.id === id);
    if (!c) return false;
    integer(width, 1, 4096, "column width");
    const o = this.columnConfig[id] ?? new GridColumnOptions();
    this.invalidate();
    c.width = Math.max(o.minWidth, Math.min(o.maxWidth, width));
    return true;
  }
  autoFitColumn(id: string, height = 20): boolean {
    integer(height, 0, 4096, "height");
    const c = this.columns.find((c) => c.id === id);
    if (!c || this.config.disableResize) return false;
    let w = cells(c.label || c.id);
    for (
      let i = this.top;
      i < Math.min(this.sourceSize(), this.top + height);
      i++
    ) {
      const r = this.record(i),
        info = this.info(r, c),
        v = info.hasDisplay
          ? info.display
          : info.null
            ? this.labelConfig.nullText
            : (r.cells[id] ?? "");
      w = Math.max(
        w,
        cells(v) + (info.state.edited && this.config.showCellMarkers ? 2 : 0),
      );
    }
    return this.resizeColumn(
      id,
      Math.min(4096, Math.max(1, w + 2 * this.config.padding)),
    );
  }
  panCell(id: string, offset: number): void {
    this.guard();
    integer(offset, 0, 1000000, "cell pan");
    if (!this.columns.some((c) => c.id === id))
      throw new Error("unknown column");
    this.cellPan[id] = offset;
  }
  geometry(width: number, height: number): GridGeometry {
    integer(width, 0, 65535, "width");
    integer(height, 0, 4096, "height");
    integer(this.top, 0, 1000000000, "top row");
    integer(this.left, 0, 1000000, "left column");
    const o = this.config,
      headerRows = Number(!o.hideHeader && height > 0),
      footerRows = Number(o.statusBar && height > headerRows),
      stride = 1 + o.rowSpacing + Number(o.horizontalLines),
      bodyRows = Math.ceil(
        Math.max(0, height - headerRows - footerRows) / stride,
      ),
      current = this.current();
    if (current && bodyRows) {
      this.top = Math.min(this.top, this.row);
      if (this.row >= this.top + bodyRows) this.top = this.row - bodyRows + 1;
    }
    const gutter = Math.min(
        width,
        Math.max(
          o.gutterWidth,
          o.rowNumbers ? String(Math.max(1, this.sourceSize())).length + 1 : 0,
        ),
      ),
      cols = copy(this.visibleColumns()),
      sep = Number(o.verticalLines),
      left = cols.filter((c) => c.pin === "left"),
      right = cols.filter((c) => c.pin === "right"),
      normal = cols.filter((c) => !c.pin);
    const automatic = cols.filter((c) => this.columnConfig[c.id]?.autoFit);
    if (automatic.length) {
      const records: Array<Record> = [];
      for (
        let i = this.top;
        i < Math.min(this.sourceSize(), this.top + Math.min(bodyRows, 256));
        i++
      )
        records.push(this.record(i));
      let sampled = 0;
      for (const c of automatic) {
        const co = this.columnConfig[c.id];
        let w = cells(c.label || c.id) + 2 * o.padding;
        for (const r of records) {
          if (sampled >= 100000) break;
          sampled++;
          const info = this.info(r, c),
            value = info.hasDisplay
              ? info.display
              : info.null
                ? this.labelConfig.nullText
                : (r.cells[c.id] ?? "");
          w = Math.max(
            w,
            cells(value) +
              2 * o.padding +
              (info.state.edited && o.showCellMarkers ? 2 : 0),
          );
        }
        c.width = Math.max(co.minWidth, Math.min(co.maxWidth, w));
      }
    }
    this.left = Math.min(this.left, Math.max(0, normal.length - 1));
    const column = current ? cols[this.column] : null;
    if (column && normal.includes(column)) {
      const at = normal.indexOf(column),
        capacity = Math.max(
          0,
          width -
            gutter -
            [...left, ...right].reduce((s, c) => s + (c.width ?? 12) + sep, 0),
        );
      this.left = Math.min(this.left, at);
      while (
        this.left < at &&
        normal
          .slice(this.left, at + 1)
          .reduce((s, c) => s + (c.width ?? 12) + sep, 0) > capacity
      )
        this.left++;
    }
    let x = gutter;
    const rightWidth = Math.min(
        Math.max(0, width - gutter),
        right.reduce((s, c) => s + (c.width ?? 12) + sep, 0),
      ),
      end = width - rightWidth;
    let spans: GridSpan[] = [];
    for (const c of [...left, ...normal.slice(this.left)]) {
      const w = Math.min(c.width ?? 12, Math.max(0, end - x));
      if (w) spans.push({ id: c.id, x, width: w });
      x += w + sep;
      if (x >= end) break;
    }
    x = Math.max(gutter, end);
    for (const c of right) {
      const w = Math.min(c.width ?? 12, Math.max(0, width - x));
      if (w) spans.push({ id: c.id, x, width: w });
      x += w + sep;
      if (x >= width) break;
    }
    const room = Math.max(
        0,
        end -
          Math.max(
            gutter,
            ...spans.filter((s) => s.x < end).map((s) => s.x + s.width + sep),
          ),
      ),
      weights = new Map(
        spans
          .filter((s) => s.x < end)
          .map((s) => [s.id, this.columnConfig[s.id]?.expand ?? 0]),
      ),
      total = [...weights.values()].reduce((a, b) => a + b, 0);
    if (room && total) {
      let shift = 0,
        remaining = room;
      spans = spans.map((s) => {
        if (s.x >= end) return s;
        const co = this.columnConfig[s.id] ?? new GridColumnOptions(),
          extra = Math.min(
            remaining,
            co.maxWidth - s.width,
            Math.floor((room * (weights.get(s.id) ?? 0)) / total),
          ),
          out = { id: s.id, x: s.x + shift, width: s.width + extra };
        shift += extra;
        remaining -= extra;
        return out;
      });
    }
    return {
      top: this.top,
      left: this.left,
      gutter,
      headerRows,
      footerRows,
      bodyRows,
      stride,
      columns: spans,
    };
  }
  private editorWindow(
    value: string,
    cursor: number,
    width: number,
  ): [string, number, number, number] {
    const gs = graphemes(value),
      at = Math.max(0, Math.min(gs.length, cursor)),
      reserve = Math.min(
        width,
        Math.max(1, at < gs.length ? cells(gs[at]) : 1),
      );
    let start = at,
      x = 0;
    while (start > 0) {
      const w = cells(gs[start - 1]);
      if (x + w > width - reserve) break;
      start--;
      x += w;
    }
    let text = "",
      used = 0;
    for (const raw of gs.slice(start)) {
      const g = clean(raw),
        w = cells(g);
      if (used + w > width) break;
      text += g;
      used += w;
    }
    const glyph = Math.max(1, at < gs.length ? cells(gs[at]) : 1);
    return [text, x, glyph > width ? 1 : glyph, start];
  }
  editCursor(width: number, height: number): [number, number, number] | null {
    const e = this.edit;
    if (!e || e.pending || e.null || !this.workValid(e)) return null;
    const geo = this.geometry(width, height),
      i = this.sourceIndex(e.rowId),
      span = geo.columns.find((s) => s.id === e.columnId);
    if (i === undefined || !span || i < geo.top || i >= geo.top + geo.bodyRows)
      return null;
    const c = this.columns.find((c) => c.id === span.id)!,
      info = this.info(this.record(i), c),
      extra = info.state.edited && this.config.showCellMarkers ? 2 : 0,
      room = span.width - 2 * this.config.padding - extra,
      y = geo.headerRows + (i - geo.top) * geo.stride;
    if (room <= 0 || y >= height - geo.footerRows) return null;
    const [, x, glyph] = this.editorWindow(
      e.buffer.value,
      e.buffer.cursor,
      room,
    );
    return [span.x + this.config.padding + extra + x, y, glyph];
  }
  private display(
    r: Record,
    c: Column,
    info: GridCellInfo,
    width: number,
    editing: boolean,
  ): string {
    if (editing)
      return this.edit!.null
        ? this.labelConfig.nullText
        : this.editorWindow(
            this.edit!.buffer.value,
            this.edit!.buffer.cursor,
            width,
          )[0];
    let text = info.hasDisplay
      ? info.display
      : info.null
        ? this.labelConfig.nullText
        : (r.cells[c.id] ?? "");
    const co = this.columnConfig[c.id] ?? new GridColumnOptions();
    if (co.overflow === "scroll") {
      const offset = this.cellPan[c.id] ?? 0;
      let used = 0,
        out = "";
      for (const g of graphemes(text)) {
        const n = cells(g);
        if (used >= offset) out += g;
        else if (used + n > offset) out += " ".repeat(used + n - offset);
        used += n;
      }
      text = out;
    }
    text = clip(text, width, co.overflow !== "clip");
    const spare = Math.max(0, width - cells(text)),
      align = co.align === "auto" && info.numeric ? "right" : co.align;
    return align === "right"
      ? " ".repeat(spare) + text
      : align === "center"
        ? " ".repeat(Math.floor(spare / 2)) +
          text +
          " ".repeat(spare - Math.floor(spare / 2))
        : text + " ".repeat(spare);
  }
  statusText(): string {
    const p = this.current(),
      s = this.status;
    integer(s.totalRows, 0, 1000000000, "total rows");
    const f: Dict<string> = {
      position: `${p ? this.row + 1 : 0}/${s.totalRows || this.sourceSize()}`,
      column: p ? p[1].label || p[1].id : "",
      selection: this.selected ? this.labelConfig.range : "",
      sort: (this.sortColumn + " " + this.sortDirection).trim(),
      filter: s.filter,
      loading: s.loading ? this.labelConfig.loading : "",
      more: s.hasMore ? this.labelConfig.more : "",
      meta: s.metadata,
      error: this.edit?.error || s.error,
    };
    return (
      f.error ||
      this.config.statusFields
        .map((k) => f[k])
        .filter(Boolean)
        .join(" | ")
    );
  }
  private columnSignature(): string {
    return JSON.stringify(
      this.columns.map((c) => [
        c.id,
        c.width ?? 12,
        !!c.hidden,
        c.pin ?? "",
        !!c.editable,
      ]),
    );
  }
  draw(canvas: Canvas, r: Rect, focused = true, ascii = false): void {
    integer(r.x, 0, 1000000000, "x");
    integer(r.y, 0, 1000000000, "y");
    const geo = this.geometry(r.width, r.height),
      o = this.config,
      child = new Canvas(
        r.width,
        r.height,
        canvas.palette,
        o.useSurface ? "surface" : canvas.surfaceRole,
      ),
      currentColumnId = this.columnId;
    const hitRows = new Map<number, string>(),
      signature = this.columnSignature();
    const sep = ascii || o.ascii ? "|" : "│",
      horizontal = ascii || o.ascii ? "-" : "─",
      cols = new Map(this.columns.map((c) => [c.id, c])),
      bounds = this.selectionBounds(),
      visible = this.visibleColumns();
    if (geo.headerRows) {
      child.fill(rect(0, 0, r.width, 1), "grid.header");
      for (const span of geo.columns) {
        const c = cols.get(span.id)!;
        let title = c.label || c.id;
        if (this.sortColumn === c.id)
          title += this.sortDirection === "desc" ? " v" : " ^";
        const text = clip(title, span.width, true);
        child.write(
          span.x,
          0,
          text + " ".repeat(Math.max(0, span.width - cells(text))),
          "grid.header",
          false,
          span.width,
        );
      }
    }
    for (let dy = 0; dy < geo.bodyRows; dy++) {
      const i = geo.top + dy,
        y = geo.headerRows + dy * geo.stride;
      if (y >= r.height - geo.footerRows || i >= this.sourceSize()) break;
      const row = this.record(i);
      hitRows.set(i, row.id);
      if (geo.gutter) {
        const n = o.rowNumbers ? String(i + 1) : "";
        child.write(
          0,
          y,
          n.padStart(Math.max(0, geo.gutter - 1)) + " ",
          row.state?.disabled ? "disabled" : "hint",
          false,
          geo.gutter,
        );
      }
      for (const span of geo.columns) {
        const c = cols.get(span.id)!,
          info = this.info(row, c),
          state = info.state,
          selected = i === this.row && c.id === currentColumnId,
          j = visible.findIndex((v) => v.id === c.id),
          inRange =
            !!bounds &&
            bounds[0] <= i &&
            i <= bounds[2] &&
            bounds[1] <= j &&
            j <= bounds[3],
          editing =
            !!this.edit &&
            row.id === this.edit.rowId &&
            c.id === this.edit.columnId &&
            this.workValid(this.edit);
        let role = state.disabled
          ? "disabled"
          : state.invalid
            ? "error"
            : state.edited && o.preserveEdited
              ? "edited"
              : (selected && o.highlightCell) ||
                  (o.highlightRow && i === this.row) ||
                  (inRange && this.selected)
                ? "selection"
                : o.striped && i % 2
                  ? "surface"
                  : "body";
        if (editing)
          role = this.edit!.pending
            ? "hint"
            : this.edit!.error
              ? "error"
              : "field";
        const pad = Math.min(o.padding, Math.floor(span.width / 2)),
          marker = state.edited && o.showCellMarkers ? "* " : "",
          room = Math.max(0, span.width - 2 * pad - marker.length),
          text = this.display(row, c, info, room, editing),
          value =
            " ".repeat(pad) +
            marker +
            text +
            " ".repeat(
              Math.max(0, span.width - pad - marker.length - cells(text)),
            );
        child.write(
          span.x,
          y,
          value,
          role,
          focused && selected && !state.disabled,
          span.width,
        );
        const edit = this.edit;
        if (editing && edit && !edit.pending && !edit.null) {
          const buf = edit.buffer,
            lo = Math.min(buf.anchor, buf.cursor),
            hi = Math.max(buf.anchor, buf.cursor);
          if (lo < hi) {
            const [, , , start] = this.editorWindow(
              buf.value,
              buf.cursor,
              room,
            );
            let x = 0,
              index = start;
            for (const raw of graphemes(buf.value).slice(start)) {
              const glyph = clean(raw),
                w = cells(glyph);
              if (x + w > room) break;
              if (lo <= index && index < hi)
                child.write(
                  span.x + pad + marker.length + x,
                  y,
                  glyph,
                  "selection",
                  false,
                  w,
                );
              x += w;
              index++;
            }
          }
        }
      }
      if (o.horizontalLines) {
        const yy = y + 1 + o.rowSpacing;
        if (yy < r.height - geo.footerRows)
          child.write(
            geo.gutter,
            yy,
            horizontal.repeat(Math.max(0, r.width - geo.gutter)),
            "hint",
            false,
            r.width - geo.gutter,
          );
      }
    }
    if (!this.sourceSize() && geo.headerRows < r.height - geo.footerRows)
      child.write(
        geo.gutter,
        geo.headerRows,
        clip(
          this.status.error ||
            (this.status.loading
              ? this.labelConfig.loading
              : this.labelConfig.empty),
          Math.max(0, r.width - geo.gutter),
        ),
        this.status.error ? "error" : "hint",
        false,
        r.width - geo.gutter,
      );
    if (o.verticalLines)
      for (const span of geo.columns) {
        const x = span.x + span.width;
        if (x < r.width)
          for (let y = 0; y < r.height - geo.footerRows; y++)
            child.write(
              x,
              y,
              sep,
              y < geo.headerRows ? "grid.header" : "hint",
              false,
              1,
            );
      }
    if (geo.footerRows)
      child.write(
        0,
        r.height - 1,
        clip(this.statusText(), r.width, true),
        this.status.error || this.edit?.error ? "error" : "hint",
        false,
        r.width,
      );
    const cursor = focused ? this.editCursor(r.width, r.height) : null;
    if (cursor) child.setCursor(...cursor);
    canvas.blit(child, rect(0, 0, r.width, r.height), r.x, r.y);
    const key = JSON.stringify([
      r.x,
      r.y,
      r.width,
      r.height,
      canvas.palette.theme,
      canvas.palette.colors,
      canvas.surfaceRole,
      ascii,
      focused,
    ]);
    if (!focused || (this.paintKey && this.paintKey !== key))
      this.capture = null;
    this.paintKey = key;
    this.hits = {
      width: r.width,
      height: r.height,
      geometry: geo,
      rows: hitRows,
      signature,
    };
  }
  click(x: number, y: number, width: number, height: number): Event {
    this.guard();
    if (
      this.config.disableMouse ||
      this.edit ||
      this.pasteRequest ||
      !this.hits ||
      this.hits.width !== width ||
      this.hits.height !== height ||
      this.hits.signature !== this.columnSignature() ||
      x < 0 ||
      x >= width ||
      y < 0 ||
      y >= height
    )
      return event();
    const geo = this.hits.geometry,
      span = geo.columns.find((s) => s.x <= x && x < s.x + s.width);
    if (!span) return event();
    if (y < geo.headerRows) {
      if (this.config.disableHeaderSort) return event();
      this.column = this.visibleColumns().findIndex((c) => c.id === span.id);
      return this.request("sort");
    }
    const dy = y - geo.headerRows;
    if (dy % geo.stride || y >= height - geo.footerRows) return event();
    const i = geo.top + Math.floor(dy / geo.stride);
    if (i >= this.sourceSize()) return event();
    const r = this.record(i);
    if (this.hits.rows.get(i) !== r.id) return event();
    const c = this.columns.find((c) => c.id === span.id)!;
    if (this.info(r, c).state.disabled || !this.focus(r.id, c.id))
      return event();
    return event("select", r.id, "", { column_id: c.id });
  }
  get pointerCaptured(): boolean {
    return this.capture !== null;
  }
  private armGrid(width: number, height: number, mode: GridCaptureMode): void {
    this.capture = {
      width,
      height,
      revision: this.currentRevision,
      signature: this.columnSignature(),
      ...mode,
    };
  }
  private rangeAnchor(current: [Record, Column]): [string, string] {
    const selection = this.selected;
    return selection && this.selectionBounds()
      ? [selection.anchorRow, selection.anchorColumn]
      : [current[0].id, current[1].id];
  }
  private extendNavigation(action: string, height: number): Event {
    const current = this.current();
    if (!current) return event();
    const [anchorRow, anchorColumn] = this.rangeAnchor(current),
      row = this.row,
      column = this.column;
    const result = this.handle(action, height),
      after = this.current();
    if (result.kind !== "select" || !after) return result;
    if (this.info(...after).state.disabled) {
      this.row = row;
      this.column = column;
      return event();
    }
    this.setSelection({
      anchorRow,
      anchorColumn,
      endRow: after[0].id,
      endColumn: after[1].id,
    });
    return result;
  }
  private gridHit(
    x: number,
    y: number,
    width: number,
    height: number,
  ): GridHit | null {
    const hits = this.hits;
    if (
      !hits ||
      hits.width !== width ||
      hits.height !== height ||
      hits.signature !== this.columnSignature() ||
      x < 0 ||
      y < 0 ||
      x >= width ||
      y >= height
    )
      return null;
    const geo = hits.geometry,
      span = geo.columns.find((s) => s.x <= x && x < s.x + s.width);
    if (y < geo.headerRows) return { geo, span, row: null, gutter: false };
    const dy = y - geo.headerRows;
    if (dy % geo.stride || y >= height - geo.footerRows) return null;
    const index = geo.top + Math.floor(dy / geo.stride),
      seen = hits.rows.get(index);
    if (!seen) return null;
    const row = index < this.sourceSize() ? this.record(index) : null;
    if (!row || row.id !== seen) {
      if (this.capture?.kind === "range" || this.capture?.kind === "edit")
        this.capture = null;
      return null;
    }
    const gutter = !span && x < geo.gutter && this.config.rowNumbers;
    return span || gutter ? { geo, span, row, gutter } : null;
  }
  private editPointer(
    action: string,
    x: number,
    y: number,
    width: number,
    height: number,
    extend: boolean,
  ): Event {
    const e = this.edit;
    if (!e || e.pending || e.null || !this.workValid(e)) {
      this.capture = null;
      return event();
    }
    if (action === "move" && this.capture?.kind !== "edit") return event();
    if (!["down", "move", "click", "double"].includes(action)) return event();
    const hit = this.gridHit(x, y, width, height);
    if (
      !hit?.span ||
      !hit.row ||
      hit.row.id !== e.rowId ||
      hit.span.id !== e.columnId
    )
      return action === "move" ? event() : event("edit_blocked");
    const col = this.columns.find((c) => c.id === hit.span!.id)!;
    const extra =
      this.config.showCellMarkers && this.info(hit.row, col).state.edited
        ? 2
        : 0;
    const pad = this.config.padding + extra,
      room = hit.span.width - 2 * this.config.padding - extra;
    if (room <= 0) return event();
    const buf = e.buffer,
      [, , , start] = this.editorWindow(buf.value, buf.cursor, room);
    const offset = Math.max(0, Math.min(room, x - hit.span.x - pad));
    let used = 0,
      pos = start;
    for (const g of graphemes(buf.value).slice(start)) {
      const w = cells(clean(g));
      if (used + w > offset) break;
      used += w;
      pos++;
    }
    buf.select(extend || action === "move" ? buf.anchor : pos, pos);
    if (action === "down")
      this.armGrid(width, height, { kind: "edit", editId: e.id });
    return event("edit_select", e.rowId, "", { column_id: hit.span.id });
  }
  /** Local coordinates. Route captured moves and releases even outside the grid. */
  pointer(
    action: string,
    x: number,
    y: number,
    width: number,
    height: number,
    extend = false,
  ): Event {
    this.guard();
    if (
      ![
        "down",
        "move",
        "up",
        "cancel",
        "click",
        "double",
        "wheel_up",
        "wheel_down",
        "wheel_left",
        "wheel_right",
      ].includes(action)
    )
      return event();
    integer(x, -1000000000, 1000000000, "pointer x");
    integer(y, -1000000000, 1000000000, "pointer y");
    integer(width, 0, 65535, "width");
    integer(height, 0, 4096, "height");
    let capture = this.capture;
    if (
      capture &&
      (capture.width !== width ||
        capture.height !== height ||
        capture.revision !== this.currentRevision ||
        capture.signature !== this.columnSignature())
    )
      capture = this.capture = null;
    if (this.config.disableMouse || this.pasteRequest || action === "cancel") {
      this.capture = null;
      return event();
    }
    if (action === "up") {
      this.capture = null;
      if (capture?.kind === "column" && !capture.moved) {
        const hit = this.gridHit(x, y, width, height);
        if (hit && !hit.row && hit.span?.id === capture.column)
          return this.click(x, y, width, height);
      }
      return event();
    }
    if (action === "down") capture = this.capture = null;
    if (this.edit) {
      if (capture?.kind === "edit" && capture.editId !== this.edit.id)
        this.capture = null;
      return this.editPointer(action, x, y, width, height, extend);
    }
    if (action.startsWith("wheel_")) {
      this.capture = null;
      return this.handle(action.slice(6), height);
    }
    if (action === "move" && !capture) return event();
    if (action === "move" && capture?.kind === "resize") {
      const id = capture.column,
        col = this.columns.find((v) => v.id === id)!,
        o = this.columnConfig[id] ?? new GridColumnOptions();
      const value = Math.max(
        o.minWidth,
        Math.min(o.maxWidth, capture.startWidth + x - capture.startX),
      );
      if (value !== (col.width ?? 12) && this.resizeColumn(id, value)) {
        this.armGrid(width, height, {
          kind: "resize",
          column: id,
          startWidth: capture.startWidth,
          startX: capture.startX,
        });
        return event("resize", "", "", { column_id: id, width: value });
      }
      return event();
    }
    if (action === "move" && capture?.kind === "column") {
      const id = capture.column,
        span = this.geometry(width, height).columns.find(
          (s) => s.x <= x && x < s.x + s.width,
        );
      if (span && span.id !== id) {
        const source = this.columns.findIndex((v) => v.id === id),
          target = this.columns.findIndex((v) => v.id === span.id);
        if (
          (this.columns[source].pin ?? "") === (this.columns[target].pin ?? "")
        ) {
          const order = [...this.columns];
          order.splice(target, 0, order.splice(source, 1)[0]);
          this.setColumnLayout(order);
          this.armGrid(width, height, {
            kind: "column",
            column: id,
            moved: true,
          });
          return event("columns", "", "", { column_id: id });
        }
      }
      return event();
    }
    const hit = this.gridHit(x, y, width, height);
    if (!hit) return event();
    const { geo, span, row, gutter } = hit;
    if (!row) {
      if (action === "down") {
        const divider =
          this.config.verticalLines && !this.config.disableResize
            ? geo.columns.find((s) => s.x + s.width === x)
            : undefined;
        if (divider) {
          const id = divider.id,
            col = this.columns.find((v) => v.id === id)!;
          this.armGrid(width, height, {
            kind: "resize",
            column: id,
            startX: x,
            startWidth: col.width ?? 12,
          });
          return event("resize_start", "", "", { column_id: id });
        }
        if (span)
          this.armGrid(width, height, {
            kind: "column",
            column: span.id,
            moved: false,
          });
        return event();
      }
      return ["click", "double"].includes(action)
        ? this.click(x, y, width, height)
        : event();
    }
    if (action === "move" && capture?.kind !== "range") return event();
    const current = this.current(),
      cols = this.visibleColumns(),
      column = span?.id ?? current?.[1].id ?? "",
      col = cols.find((v) => v.id === column);
    if (!col || this.info(row, col).state.disabled) return event();
    let [anchorRow, anchorColumn] =
        extend && current ? this.rangeAnchor(current) : [row.id, column],
      whole = gutter || this.config.selection === "row";
    if (action === "move" && capture?.kind === "range") {
      const at = this.sourceIndex(capture.anchorRow);
      if (
        at === undefined ||
        at !== capture.anchorIndex ||
        at >= this.sourceSize() ||
        this.record(at).id !== capture.anchorRow
      ) {
        this.capture = null;
        return event();
      }
      anchorRow = capture.anchorRow;
      anchorColumn = capture.anchorColumn;
      whole = capture.whole;
    }
    if (!this.focus(row.id, column)) return event();
    if (action === "double") return this.handle("activate", height);
    if (whole || extend || action === "move")
      this.setSelection({
        anchorRow,
        anchorColumn: whole ? cols[0].id : anchorColumn,
        endRow: row.id,
        endColumn: whole ? cols.at(-1)!.id : column,
      });
    else if (action === "down" || action === "click") this.selected = null;
    if (action === "down")
      this.armGrid(width, height, {
        kind: "range",
        anchorRow,
        anchorColumn,
        anchorIndex: this.sourceIndex(anchorRow),
        whole,
      });
    return event("select", row.id, "", { column_id: column });
  }
  saveView(): GridViewState {
    const p = this.current(),
      normal = this.visibleColumns().filter((c) => !c.pin);
    return {
      columns: this.columns.map((c) => ({
        id: c.id,
        width: c.width ?? 12,
        hidden: !!c.hidden,
        pin: c.pin ?? "",
      })),
      columnOptions: copy(this.columnConfig),
      rowId: p?.[0].id ?? "",
      columnId: p?.[1].id ?? "",
      topRowId: this.top < this.sourceSize() ? this.record(this.top).id : "",
      leftColumnId: normal[this.left]?.id ?? "",
      sortColumn: this.sortColumn,
      sortDirection: this.sortDirection,
      selection: copy(this.selected),
      mode: this.config.selection,
      filter: this.status.filter,
    };
  }
  restoreView(state: GridViewState): void {
    this.guard();
    const data = copy(state),
      temp = new Grid(this.columns, []);
    temp.setColumnLayout(data.columns);
    for (const item of data.columns) {
      integer(item.width, 1, 4096, "column width");
      temp.columns.find((c) => c.id === item.id)!.width = item.width;
    }
    for (const [id, options] of Object.entries(data.columnOptions ?? {}))
      temp.setColumnOptions(id, new GridColumnOptions(options));
    if (
      !["", ...temp.columns.map((c) => c.id)].includes(data.sortColumn ?? "") ||
      !["", "asc", "desc"].includes(data.sortDirection ?? "") ||
      !["cell", "row", "range"].includes(data.mode ?? "cell")
    )
      throw new Error("invalid grid view state");
    const top = this.sourceIndex(data.topRowId ?? "");
    if (top !== undefined) this.record(top);
    if (data.selection) {
      const cols = new Set(temp.visibleColumns().map((c) => c.id)),
        s = data.selection;
      if (!cols.has(s.anchorColumn) || !cols.has(s.endColumn))
        throw new Error("hidden range column");
      for (const id of [s.anchorRow, s.endRow]) {
        const i = this.sourceIndex(id);
        if (i === undefined || this.record(i).id !== id)
          throw new Error("unknown range row");
      }
    }
    this.invalidate();
    this.columns = temp.columns;
    this.columnConfig = temp.columnConfig;
    this.config.selection = data.mode ?? "cell";
    this.top = top ?? 0;
    const normal = this.visibleColumns().filter((c) => !c.pin);
    this.left = Math.max(
      0,
      normal.findIndex((c) => c.id === data.leftColumnId),
    );
    this.sortColumn = data.sortColumn ?? "";
    this.sortDirection = data.sortDirection ?? "";
    this.status.filter = data.filter ?? "";
    this.selected = data.selection ?? null;
    this.focus(data.rowId ?? "", data.columnId ?? "");
  }
}
