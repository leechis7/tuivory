import foldData from "./casefold.json" with { type: "json" };
type Dict<K extends PropertyKey, V> = { [P in K]: V };
/** Independent TypeScript implementation. No native or other-language runtime. */
import tokens from "./tokens.json" with { type: "json" };
import unicode from "./unicode-width.json" with { type: "json" };

export type Theme = "dark" | "light" | "blackwhite";
export type Colors = "8" | "16" | "256" | "truecolor";
export interface Event {
  kind: string;
  id: string;
  text?: string;
  data?: unknown;
}
const event = (kind = "", id = "", text = "", data?: unknown): Event => ({
  kind,
  id,
  text,
  data,
});
const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value));
const segmenter = new Intl.Segmenter(undefined, { granularity: "grapheme" });
export const graphemes = (text: string): string[] =>
  [...segmenter.segment(text)].map((s) => s.segment);
export const clean = (text: string): string =>
  text.replace(/[\x00-\x1f\x7f-\x9f]/g, " ");
function inRanges(cp: number, ranges: number[][]): boolean {
  let lo = 0,
    hi = ranges.length - 1;
  while (lo <= hi) {
    const m = (lo + hi) >>> 1,
      r = ranges[m];
    if (cp < r[0]) hi = m - 1;
    else if (cp > r[1]) lo = m + 1;
    else return true;
  }
  return false;
}
function clusterWidth(g: string): number {
  const points = [...g].map((c) => c.codePointAt(0)!);
  let total = 0,
    cluster = 0,
    base = -1,
    lastWidth = 0,
    baseAvailable = false,
    virama = false;
  for (let i = 0; i < points.length; i++) {
    const cp = points[i];
    if (cp === 0x200d) {
      if (!virama && i + 1 < points.length) {
        i++;
        lastWidth = 0;
      }
      if (!virama) virama = false;
      continue;
    }
    if (cp === 0xfe0f && baseAvailable) {
      if (inRanges(base, unicode.vs16)) cluster = 2;
      baseAvailable = false;
      continue;
    }
    if (cp === 0xfe0e && baseAvailable) {
      if (lastWidth === 2 && inRanges(base, unicode.vs15)) total--;
      baseAvailable = false;
      continue;
    }
    if (cp >= 0x1f1e6 && cp <= 0x1f1ff) {
      let n = 0;
      for (
        let j = i - 1;
        j >= 0 && points[j] >= 0x1f1e6 && points[j] <= 0x1f1ff;
        j--
      )
        n++;
      if (n % 2 === 1) {
        base = cp;
        continue;
      }
    } else if (
      cp >= 0x1f3fb &&
      cp <= 0x1f3ff &&
      inRanges(base, unicode.pictographic)
    )
      continue;
    const w = inRanges(cp, unicode.zero)
      ? 0
      : inRanges(cp, unicode.wide)
        ? 2
        : 1;
    if (w) {
      if (virama) cluster = 2;
      else {
        total += cluster;
        cluster = w;
      }
      base = cp;
      lastWidth = w;
      baseAvailable = true;
      virama = false;
    } else if (inRanges(cp, unicode.virama)) virama = true;
    else if (baseAvailable && inRanges(cp, unicode.spacing_mc)) {
      cluster = 2;
      baseAvailable = false;
      virama = false;
    } else virama = false;
  }
  return total + cluster;
}
export const cells = (text: string): number =>
  graphemes(clean(text)).reduce((sum, g) => sum + clusterWidth(g), 0);
export function clip(text: string, width: number, ellipsis = false): string {
  text = clean(text);
  if (width <= 0) return "";
  if (cells(text) <= width) return text;
  let out = "",
    used = 0;
  for (const g of graphemes(text)) {
    const n = clusterWidth(g);
    if (used + n > width - Number(ellipsis)) break;
    out += g;
    used += n;
  }
  return out + (ellipsis ? "~" : "");
}
export interface Style {
  foreground: string;
  background: string;
  bold: boolean;
  dim: boolean;
  underline: boolean;
}
export class Palette {
  readonly roles: Dict<
    string,
    { foreground: string; background: string; fontWeight: string }
  >;
  constructor(
    readonly theme: Theme = "dark",
    readonly colors: Colors = "256",
  ) {
    const palette = (tokens.palettes as Dict<string, typeof this.roles>)[
      `${theme}-${colors}`
    ];
    if (!palette) throw new Error(`unknown palette: ${theme}-${colors}`);
    this.roles = clone(palette);
  }
  style(role = "body", focused = false): Style {
    const t = this.roles[role];
    if (!t) throw new Error(`unknown role: ${role}`);
    return {
      foreground: t.foreground,
      background: t.background,
      bold: t.fontWeight === "bold",
      dim: role === "disabled",
      underline: focused,
    };
  }
}
export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}
export const rect = (x = 0, y = 0, width = 0, height = 0): Rect => ({
  x,
  y,
  width,
  height,
});
export interface Cell {
  text: string;
  style: Style;
  owner: number;
}
export function sgr(style: Style): string {
  const color = (v: string, bg: boolean): string => {
    const base = bg ? 48 : 38;
    if (v.startsWith("#"))
      return `${base};2;${[1, 3, 5].map((i) => parseInt(v.slice(i, i + 2), 16)).join(";")}`;
    const n = Number(v);
    return n < 8
      ? String((bg ? 40 : 30) + n)
      : n < 16
        ? String((bg ? 100 : 90) + n - 8)
        : `${base};5;${n}`;
  };
  return `\x1b[0;${color(style.foreground, false)};${color(style.background, true)}${style.bold ? ";1" : ""}${style.dim ? ";2" : ""}${style.underline ? ";4" : ""}m`;
}
export class Canvas {
  readonly data: Cell[][];
  cursor: [number, number] | null = null;
  constructor(
    readonly width: number,
    readonly height: number,
    readonly palette = new Palette(),
  ) {
    if (
      !Number.isInteger(width) ||
      !Number.isInteger(height) ||
      width < 0 ||
      height < 0 ||
      width * height > 1e6
    )
      throw new Error("invalid dimensions");
    this.data = Array.from({ length: height }, () =>
      Array.from({ length: width }, () => ({
        text: " ",
        style: palette.style("surface"),
        owner: -1,
      })),
    );
  }
  private erase(x: number, y: number): void {
    const row = this.data[y],
      start = row[x].owner >= 0 ? row[x].owner : x;
    let end = start + 1;
    while (end < this.width && row[end].owner === start) end++;
    for (let i = start; i < end; i++)
      row[i] = { text: " ", style: row[i].style, owner: -1 };
  }
  write(
    x: number,
    y: number,
    text: string,
    role = "body",
    focused = false,
    width = this.width - x,
    preserve = false,
  ): void {
    if (y < 0 || y >= this.height) return;
    const limit = Math.min(this.width, x + Math.max(0, width)),
      style = this.palette.style(role, focused);
    if (
      !preserve &&
      [
        "body",
        "hint",
        "info",
        "success",
        "warning",
        "error",
        "header",
      ].includes(role)
    )
      style.background = this.palette.style("surface").background;
    for (const g of graphemes(clean(text))) {
      const n = clusterWidth(g);
      if (n === 0) continue;
      if (x >= limit) break;
      if (x < 0 || x + n > limit) {
        for (let i = Math.max(0, x); i < Math.min(limit, x + n); i++) {
          this.erase(i, y);
          this.data[y][i] = { text: " ", style, owner: -1 };
        }
        x += n;
        continue;
      }
      for (let i = x; i < x + n; i++) this.erase(i, y);
      this.data[y][x] = { text: g, style, owner: -1 };
      for (let i = x + 1; i < x + n; i++)
        this.data[y][i] = { text: "", style, owner: x };
      x += n;
    }
  }
  fill(r: Rect, role = "surface"): void {
    for (
      let y = Math.max(0, r.y);
      y < Math.min(this.height, r.y + r.height);
      y++
    )
      this.write(
        r.x,
        y,
        " ".repeat(Math.max(0, r.width)),
        role,
        false,
        r.width,
        true,
      );
  }
  panel(r: Rect, title = "", focused = false, ascii = false): Rect {
    this.fill(r);
    if (r.width < 2 || r.height < 2) return rect(r.x, r.y);
    const [a, b, c, d, h, v] = ascii
      ? ["+", "+", "+", "+", "-", "|"]
      : focused
        ? ["╔", "╗", "╚", "╝", "═", "║"]
        : ["┌", "┐", "└", "┘", "─", "│"];
    const role = focused ? "focus.border" : "hint";
    this.write(r.x, r.y, a + h.repeat(r.width - 2) + b, role);
    this.write(r.x, r.y + r.height - 1, c + h.repeat(r.width - 2) + d, role);
    for (let y = r.y + 1; y < r.y + r.height - 1; y++) {
      this.write(r.x, y, v, role);
      this.write(r.x + r.width - 1, y, v, role);
    }
    this.write(r.x + 2, r.y, clip(title, r.width - 4), role);
    return rect(r.x + 1, r.y + 1, r.width - 2, r.height - 2);
  }
  setCursor(x: number, y: number, glyphWidth = 1): void {
    this.cursor =
      x >= 0 &&
      x + Math.max(1, glyphWidth) <= this.width &&
      y >= 0 &&
      y < this.height
        ? [x, y]
        : null;
  }
  lines(): string[] {
    return this.data.map((row) => row.map((c) => c.text).join(""));
  }
  ansi(originX = 0, originY = 0): string {
    let out = "\x1b[?25l";
    this.data.forEach((row, y) => {
      out += `\x1b[${originY + y + 1};${originX + 1}H`;
      let previous = "";
      for (const c of row) {
        if (c.owner >= 0) continue;
        const s = sgr(c.style);
        if (s !== previous) {
          out += s;
          previous = s;
        }
        out += c.text;
      }
    });
    out += "\x1b[0m";
    if (this.cursor)
      out += `\x1b[${originY + this.cursor[1] + 1};${originX + this.cursor[0] + 1}H\x1b[?25h`;
    return out;
  }
}
export class ControlState {
  disabled = false;
  read_only = false;
  busy = false;
  selected = false;
  edited = false;
  invalid = false;
  constructor(state: Partial<ControlState> = {}) {
    Object.assign(this, state);
  }
  get focusable(): boolean {
    return !this.disabled;
  }
  get activatable(): boolean {
    return !this.disabled && !this.busy;
  }
  get editable(): boolean {
    return this.activatable && !this.read_only;
  }
  get role(): string {
    return this.disabled
      ? "disabled"
      : this.invalid
        ? "error"
        : this.selected
          ? "selection"
          : this.edited
            ? "edited"
            : "body";
  }
  get markers(): string {
    return [
      this.disabled ? "-" : "",
      this.invalid ? "!" : "",
      this.selected ? ">" : "",
      this.edited ? "*" : "",
      this.busy ? "~" : "",
      this.read_only ? "=" : "",
    ].join("");
  }
}
function unique(items: { id: string }[]): void {
  const ids = items.map((i) => i.id);
  if (ids.some((id) => !id) || new Set(ids).size !== ids.length)
    throw new Error("IDs must be nonempty and unique");
}
export interface Node {
  id: string;
  name?: string;
  parent?: string;
  secondary?: string;
  icon?: string;
  ascii_icon?: string;
  count?: number;
  branch?: boolean;
}
export class Tree {
  readonly nodes: readonly Node[];
  readonly depth = new Map<string, number>();
  readonly branches = new Set<string>();
  readonly byId: Map<string, Node>;
  selected = "";
  expanded = new Set<string>();
  scroll = 0;
  horizontal = 0;
  constructor(nodes: Node[]) {
    unique(nodes);
    this.nodes = Object.freeze(nodes.map((node) => Object.freeze({ ...node })));
    this.byId = new Map(this.nodes.map((n) => [n.id, n]));
    let stack: string[] = [];
    for (const n of this.nodes) {
      if (n.parent) {
        if (!stack.includes(n.parent))
          throw new Error("tree requires contiguous preorder");
        stack = stack.slice(0, stack.indexOf(n.parent) + 1);
        this.branches.add(n.parent);
      } else stack = [];
      if (stack.length > 128) throw new Error("tree depth exceeds 128");
      this.depth.set(n.id, stack.length);
      stack.push(n.id);
      if (n.branch) this.branches.add(n.id);
    }
    this.reconcile(1);
  }
  visible(): Node[] {
    const visible = new Set<string>();
    return this.nodes.filter((n) => {
      if (!n.parent || (visible.has(n.parent) && this.expanded.has(n.parent))) {
        visible.add(n.id);
        return true;
      }
      return false;
    });
  }
  private reconcile(height: number): Node[] {
    this.expanded = new Set(
      [...this.expanded].filter((id) => this.branches.has(id)),
    );
    const rows = this.visible(),
      ids = rows.map((n) => n.id);
    while (
      this.selected &&
      !ids.includes(this.selected) &&
      this.byId.has(this.selected)
    )
      this.selected = this.byId.get(this.selected)!.parent ?? "";
    if (!ids.includes(this.selected)) this.selected = ids[0] ?? "";
    const i = ids.indexOf(this.selected),
      h = Math.max(1, height);
    this.scroll = Math.max(0, Math.min(this.scroll, rows.length - h));
    if (i >= 0) {
      if (i < this.scroll) this.scroll = i;
      if (i >= this.scroll + h) this.scroll = i - h + 1;
    }
    return rows;
  }
  handle(action: string, height = 10): Event {
    const rows = this.reconcile(height);
    if (!rows.length) return event();
    const old = this.selected,
      i = rows.findIndex((n) => n.id === old),
      node = rows[i];
    let target = i;
    const moves: Dict<string, number> = {
      up: i - 1,
      down: i + 1,
      home: 0,
      end: rows.length - 1,
      page_up: i - Math.max(1, height),
      page_down: i + Math.max(1, height),
    };
    if (action in moves)
      target = Math.max(0, Math.min(rows.length - 1, moves[action]));
    else if (action === "pan_left")
      this.horizontal = Math.max(0, this.horizontal - 4);
    else if (action === "pan_right")
      this.horizontal = Math.min(65535, this.horizontal + 4);
    else if (action === "activate") return event("activate", old);
    else if (action === "left") {
      if (this.expanded.delete(old)) {
        this.reconcile(height);
        return event("collapse", old);
      }
      if (node.parent) this.selected = node.parent;
    } else if (["right", "toggle"].includes(action) && this.branches.has(old)) {
      if (action === "toggle" && this.expanded.delete(old)) {
        this.reconcile(height);
        return event("collapse", old);
      }
      if (!this.expanded.has(old)) {
        this.expanded.add(old);
        this.reconcile(height);
        return event("expand", old);
      }
      if (rows[i + 1]?.parent === old) target++;
    }
    if (target !== i) this.selected = rows[target].id;
    this.reconcile(height);
    return this.selected !== old ? event("select", this.selected) : event();
  }
  click(x: number, y: number, height = 10): Event {
    const rows = this.reconcile(height);
    if (y < 0 || y >= height || this.scroll + y >= rows.length) return event();
    const n = rows[this.scroll + y],
      old = this.selected;
    this.selected = n.id;
    if (x >= 2 && x + this.horizontal === 2 + 2 * this.depth.get(n.id)!) {
      const e = this.handle("toggle", height);
      if (e.kind) return e;
    }
    return old !== n.id ? event("select", n.id) : event();
  }
  draw(c: Canvas, r: Rect, focused = true, ascii = false): void {
    c.fill(r);
    const rows = this.reconcile(r.height);
    rows.slice(this.scroll, this.scroll + r.height).forEach((n, y) => {
      const selected = n.id === this.selected;
      const arrow = this.branches.has(n.id)
        ? this.expanded.has(n.id)
          ? ascii
            ? "v"
            : "▾"
          : ascii
            ? ">"
            : "▸"
        : " ";
      const icon = ascii ? n.ascii_icon : n.icon;
      let text =
        "  ".repeat(this.depth.get(n.id)!) +
        arrow +
        " " +
        (icon ? icon + " " : "") +
        (n.name ?? "") +
        (n.secondary ? "  " + n.secondary : "") +
        (n.count !== undefined ? ` (${n.count})` : "");
      let skipped = 0;
      const parts = graphemes(text);
      while (parts.length && skipped < this.horizontal)
        skipped += cells(parts.shift()!);
      text =
        (selected ? "> " : "  ") +
        clip(parts.join(""), Math.max(0, r.width - 2), true);
      c.write(
        r.x,
        r.y + y,
        text,
        selected ? "selection" : "body",
        focused && selected,
        r.width,
      );
    });
  }
}
export interface Tab {
  id: string;
  title?: string;
  edited?: boolean;
  closable?: boolean;
  disabled?: boolean;
}
export interface TabCell {
  id: string;
  text: string;
  start: number;
  width: number;
  active: boolean;
  focused: boolean;
  disabled: boolean;
}
export class Tabs {
  readonly items: Tab[];
  active = "";
  focused = "";
  first = 0;
  constructor(items: Tab[]) {
    unique(items);
    this.items = clone(items);
    this.eligible();
  }
  private eligible(): Tab[] {
    const items = this.items.filter((t) => !t.disabled),
      ids = items.map((t) => t.id);
    if (!ids.includes(this.active)) this.active = ids[0] ?? "";
    if (!ids.includes(this.focused)) this.focused = this.active;
    return items;
  }
  handle(action: string): Event {
    const items = this.eligible();
    if (!items.length) return event();
    const i = items.findIndex((t) => t.id === this.focused);
    if (action === "activate") {
      this.active = this.focused;
      return event("activate", this.active);
    }
    if (action === "close")
      return items[i].closable ? event("close", this.focused) : event();
    const target: Dict<string, number> = {
      previous: Math.max(0, i - 1),
      next: Math.min(items.length - 1, i + 1),
      first: 0,
      last: items.length - 1,
    };
    if (action in target && target[action] !== i) {
      this.focused = items[target[action]].id;
      return event("focus", this.focused);
    }
    return event();
  }
  layout(width: number): TabCell[] {
    this.eligible();
    if (width <= 2 || !this.items.length) return [];
    const target = Math.max(
      0,
      this.items.findIndex((t) => t.id === this.focused),
    );
    this.first = Math.max(0, Math.min(this.first, target));
    const size = (t: Tab) =>
      Math.min(24, Math.max(6, cells(t.title ?? "") + 5));
    const sum = (start: number) =>
      this.items.slice(start, target + 1).reduce((n, t) => n + size(t), 0);
    while (this.first < target && sum(this.first) > width - 2) this.first++;
    while (this.first > 0 && sum(this.first - 1) <= width - 2) this.first--;
    const out: TabCell[] = [];
    let x = 1;
    for (const tab of this.items.slice(this.first)) {
      if (x >= width - 1) break;
      const w = Math.min(size(tab), width - 1 - x);
      if (w < 4 && out.length) break;
      const active = tab.id === this.active,
        focused = tab.id === this.focused,
        suffix = (tab.edited ? " *" : "") + (tab.closable ? " x" : "");
      const text = clip(
        (focused ? ">" : " ") +
          (active ? "[" : " ") +
          clip(tab.title ?? "", Math.max(0, w - 3 - suffix.length), true) +
          suffix +
          (active ? "]" : " "),
        w,
        true,
      );
      out.push({
        id: tab.id,
        text,
        start: x,
        width: w,
        active,
        focused,
        disabled: tab.disabled ?? false,
      });
      x += w;
    }
    return out;
  }
  click(x: number, width: number): Event {
    const views = this.layout(width);
    if (x === 0 && this.first > 0) return this.handle("previous");
    if (
      width > 0 &&
      x === width - 1 &&
      this.first + views.length < this.items.length
    )
      return this.handle("next");
    for (const cell of views)
      if (x >= cell.start && x < cell.start + cell.width && !cell.disabled) {
        this.focused = cell.id;
        if (
          (cell.text.endsWith("x]") || cell.text.endsWith("x ")) &&
          this.items.some((t) => t.id === cell.id && t.closable) &&
          x === cell.start + cells(cell.text) - 2
        )
          return event("close", cell.id);
        this.active = cell.id;
        return event("activate", cell.id);
      }
    return event();
  }
  draw(c: Canvas, r: Rect, focused = true): void {
    c.fill(r);
    const views = this.layout(r.width);
    if (this.first > 0) c.write(r.x, r.y, "<", "hint");
    if (this.first + views.length < this.items.length && r.width > 0)
      c.write(r.x + r.width - 1, r.y, ">", "hint");
    for (const cell of views) {
      c.write(
        r.x + cell.start,
        r.y,
        " ".repeat(cell.width),
        cell.disabled ? "disabled" : cell.active ? "selection" : "body",
        focused && cell.focused,
        cell.width,
      );
      c.write(
        r.x + cell.start,
        r.y,
        cell.text,
        cell.disabled ? "disabled" : cell.active ? "selection" : "body",
        focused && cell.focused,
        cell.width,
      );
    }
  }
}

export interface Item {
  id: string;
  label?: string;
  secondary?: string;
  shortcut?: string;
  icon?: string;
  ascii_icon?: string;
  disabled?: boolean;
  separator?: boolean;
  parent?: string;
}
export interface CollectionRow {
  id: string;
  text: string;
  role: string;
  focused?: boolean;
}
export class List {
  items: Item[] = [];
  focused = "";
  selected = "";
  query = "";
  empty = "(empty)";
  scroll = 0;
  private hits: CollectionRow[] = [];
  private width = 0;
  constructor(items: Item[]) {
    this.setItems(items);
  }
  setItems(items: Item[]): void {
    unique(items);
    const owned = clone(items);
    if (!owned.some((i) => i.id === this.selected)) this.selected = "";
    this.items = owned;
    this.eligible();
  }
  visible(): Item[] {
    const q = fold(this.query);
    return this.items.filter(
      (i) =>
        !q ||
        (!i.separator &&
          fold((i.label ?? "") + " " + (i.secondary ?? "")).includes(q)),
    );
  }
  private eligible(): Item[] {
    const items = this.visible().filter((i) => !i.disabled && !i.separator);
    if (!items.some((i) => i.id === this.focused))
      this.focused = items[0]?.id ?? "";
    return items;
  }
  focus(id: string): boolean {
    if (!this.visible().some((i) => i.id === id && !i.disabled && !i.separator))
      return false;
    this.focused = id;
    return true;
  }
  setQuery(query: string): Event {
    this.query = query.replace(/[\x00-\x1f\x7f-\x9f]/g, "");
    this.eligible();
    return event("query", "", this.query);
  }
  handle(action: string, height = 10, text = ""): Event {
    if (action === "query") return this.setQuery(text);
    const ids = this.eligible().map((i) => i.id);
    if (!ids.length) return event();
    let at = ids.indexOf(this.focused);
    if (action === "activate" || action === "select") {
      this.selected = this.focused;
      return event(action, this.focused);
    }
    action =
      (
        { up: "previous", down: "next", home: "first", end: "last" } as Dict<
          string,
          string
        >
      )[action] ?? action;
    if (action === "previous") at = Math.max(0, at - 1);
    else if (action === "next") at = Math.min(ids.length - 1, at + 1);
    else if (action === "first") at = 0;
    else if (action === "last") at = ids.length - 1;
    else if (action === "page_up")
      at = Math.max(0, at - Math.max(1, height - 1));
    else if (action === "page_down")
      at = Math.min(ids.length - 1, at + Math.max(1, height - 1));
    else return event();
    this.focused = ids[at];
    return event("focus", this.focused);
  }
  layout(width: number, height: number, ascii = false): CollectionRow[] {
    const rows: CollectionRow[] = [];
    let anchor = 0;
    for (const i of this.visible()) {
      const current = i.id === this.focused,
        role = i.disabled
          ? "disabled"
          : i.id === this.selected
            ? "selection"
            : "body";
      if (current) anchor = rows.length;
      if (i.separator) {
        rows.push({
          id: i.id,
          text: "--- " + (i.label ?? "") + " ---",
          role: "hint",
        });
        continue;
      }
      const icon = (ascii ? i.ascii_icon : i.icon) ?? "";
      rows.push({
        id: i.id,
        text:
          (current ? "> " : "  ") +
          (i.id === this.selected ? "* " : "") +
          (icon ? icon + " " : "") +
          (i.label ?? "") +
          (i.shortcut ? " [" + i.shortcut + "]" : ""),
        role,
        focused: current,
      });
      if (i.secondary)
        rows.push({
          id: i.id,
          text: "    " + i.secondary,
          role: i.disabled ? "disabled" : "hint",
        });
    }
    if (!rows.length) rows.push({ id: "", text: this.empty, role: "hint" });
    width = Math.max(0, width);
    height = Math.max(0, height);
    this.scroll = Math.min(
      Math.max(0, anchor - Math.max(0, height - 2)),
      Math.max(0, rows.length - height),
    );
    this.width = width;
    this.hits = rows
      .slice(this.scroll, this.scroll + height)
      .map((r) => ({ ...r, text: clip(r.text, width, true) }));
    return this.hits;
  }
  clickId(id: string): Event {
    return this.focus(id) ? this.handle("activate") : event();
  }
  click(x: number, y: number, height = 10): Event {
    return x >= 0 &&
      x < this.width &&
      y >= 0 &&
      y < Math.min(height, this.hits.length)
      ? this.clickId(this.hits[y].id)
      : event();
  }
  draw(c: Canvas, r: Rect, focused = true, ascii = false): void {
    c.fill(r);
    this.layout(r.width, r.height, ascii).forEach((row, y) => {
      c.fill(rect(r.x, r.y + y, r.width, 1), row.role);
      c.write(
        r.x,
        r.y + y,
        row.text,
        row.role,
        focused && !!row.focused,
        r.width,
        true,
      );
    });
  }
}
export class SearchPicker {
  readonly list: List;
  open = false;
  value = "";
  private width = 0;
  private height = 0;
  constructor(items: Item[]) {
    this.list = new List(items);
  }
  handle(action: string, text = "", height = 10): Event {
    if (action === "open") {
      this.open = true;
      this.list.setQuery("");
      this.list.focus(this.value);
      return event("open");
    }
    if (action === "cancel") {
      this.open = false;
      return event("cancel");
    }
    if (action === "insert" || action === "backspace") {
      if (!this.open) this.handle("open");
      const query =
        action === "insert"
          ? this.list.query + text
          : graphemes(this.list.query).slice(0, -1).join("");
      return this.list.setQuery(query);
    }
    if (action === "activate") {
      if (!this.open) return this.handle("open");
      const e = this.list.handle("activate", height);
      if (e.id) {
        this.value = e.id;
        this.open = false;
        return event("change", e.id);
      }
      return e;
    }
    return this.open ? this.list.handle(action, height) : event();
  }
  clickId(id: string): Event {
    return this.list.focus(id) ? this.handle("activate") : event();
  }
  click(x: number, y: number, height = 10): Event {
    if (x < 0 || x >= this.width || y < 0 || y >= Math.min(height, this.height))
      return event();
    if (!this.open) return this.handle("open");
    if (y === 0) return event();
    const e = this.list.click(x, y - 1, Math.max(0, height - 1));
    if (e.id) {
      this.value = e.id;
      this.open = false;
      return event("change", e.id);
    }
    return event();
  }
  layout(width: number, height: number, ascii = false): CollectionRow[] {
    this.width = Math.max(0, width);
    this.height = Math.max(0, height);
    if (height <= 0) return [];
    if (!this.open) {
      const label =
        this.list.items.find((i) => i.id === this.value)?.label ??
        this.list.empty;
      return [
        { id: this.value, text: clip("v " + label, width), role: "field" },
      ];
    }
    const shown = new Text(this.list.query, { multiline: false }).window(
      Math.max(0, width - 2),
    ).text;
    return [
      { id: "", text: clip("? " + shown, width), role: "field" },
      ...this.list.layout(width, Math.max(0, height - 1), ascii),
    ];
  }
  draw(c: Canvas, r: Rect, focused = true, ascii = false): void {
    c.fill(r);
    const rows = this.layout(r.width, r.height, ascii);
    if (!this.open) {
      if (rows.length) {
        c.fill(rect(r.x, r.y, r.width, 1), "field");
        c.write(r.x, r.y, rows[0].text, "field", false, r.width, true);
      }
      return;
    }
    if (r.height > 0) {
      c.fill(rect(r.x, r.y, r.width, 1), "field");
      c.write(r.x, r.y, "? ", "field", false, r.width, true);
      if (r.width > 2)
        new Text(this.list.query, { multiline: false }).draw(
          c,
          rect(r.x + 2, r.y, r.width - 2, 1),
          focused,
        );
    }
    if (r.height > 1)
      this.list.draw(
        c,
        rect(r.x, r.y + 1, r.width, r.height - 1),
        focused,
        ascii,
      );
  }
}
export class Text {
  cursor: number;
  anchor: number;
  value: string;
  readOnly: boolean;
  secret: boolean;
  multiline: boolean;
  disabled = false;
  scrollX = 0;
  scrollY = 0;
  private undoStack: [string, number, number][] = [];
  private redoStack: [string, number, number][] = [];
  constructor(
    value = "",
    options: { readOnly?: boolean; secret?: boolean; multiline?: boolean } = {},
  ) {
    this.value = value;
    this.cursor = this.anchor = graphemes(value).length;
    this.readOnly = options.readOnly ?? false;
    this.secret = options.secret ?? false;
    this.multiline = options.multiline ?? true;
  }
  display(): string {
    return this.secret ? "*".repeat(graphemes(this.value).length) : this.value;
  }
  [Symbol.for("nodejs.util.inspect.custom")](): unknown {
    return this.toJSON();
  }
  toJSON(): unknown {
    return {
      display: this.display(),
      cursor: this.cursor,
      anchor: this.anchor,
    };
  }
  select(anchor: number, cursor: number): void {
    const n = graphemes(this.value).length;
    this.anchor = Math.max(0, Math.min(n, anchor));
    this.cursor = Math.max(0, Math.min(n, cursor));
  }
  private replaceRange(lo: number, hi: number, text: string): Event {
    if (this.disabled || this.readOnly || (lo === hi && !text)) return event();
    this.undoStack.push([this.value, this.cursor, this.anchor]);
    this.undoStack = this.undoStack.slice(-128);
    this.redoStack = [];
    const g = graphemes(this.value),
      prefix = g.slice(0, lo).join("") + text;
    this.value = prefix + g.slice(hi).join("");
    let offset = 0,
      cursor = 0;
    for (const g of graphemes(this.value)) {
      if (offset >= prefix.length) break;
      offset += g.length;
      cursor++;
    }
    this.select(cursor, cursor);
    return event("change");
  }
  private byteIndex(byte: number): number {
    let offset = 0;
    const g = graphemes(this.value),
      encoder = {
        encode: (s: string) => ({
          length: [...s].reduce(
            (n, c) =>
              n +
              ((c.codePointAt(0) ?? 0) < 128
                ? 1
                : (c.codePointAt(0) ?? 0) < 2048
                  ? 2
                  : (c.codePointAt(0) ?? 0) < 65536
                    ? 3
                    : 4),
            0,
          ),
        }),
      };
    for (let i = 0; i < g.length; i++) {
      if (offset === byte) return i;
      offset += encoder.encode(g[i]).length;
    }
    if (offset === byte) return g.length;
    throw new Error("offset splits a grapheme or is outside text");
  }
  selectionBytes(): [number, number] {
    const g = graphemes(this.value),
      a = Math.min(this.anchor, this.cursor, g.length),
      b = Math.min(Math.max(this.anchor, this.cursor), g.length),
      encoder = {
        encode: (s: string) => ({
          length: [...s].reduce(
            (n, c) =>
              n +
              ((c.codePointAt(0) ?? 0) < 128
                ? 1
                : (c.codePointAt(0) ?? 0) < 2048
                  ? 2
                  : (c.codePointAt(0) ?? 0) < 65536
                    ? 3
                    : 4),
            0,
          ),
        }),
      };
    return [
      encoder.encode(g.slice(0, a).join("")).length,
      encoder.encode(g.slice(0, b).join("")).length,
    ];
  }
  selectBytes(anchor: number, cursor: number): void {
    const a = this.byteIndex(anchor),
      c = this.byteIndex(cursor);
    this.select(a, c);
  }
  replaceBytes(start: number, end: number, text: string): Event {
    if (start > end) throw new Error("reversed byte range");
    return this.replaceRange(this.byteIndex(start), this.byteIndex(end), text);
  }
  handle(action: string, text = ""): Event {
    if (this.disabled) return event();
    this.select(this.anchor, this.cursor);
    const g = graphemes(this.value),
      lo = Math.min(this.anchor, this.cursor),
      hi = Math.max(this.anchor, this.cursor),
      at = this.cursor;
    const br = (s: string) => ["\r", "\n", "\r\n"].includes(s);
    let start = at,
      end = at;
    while (start && !br(g[start - 1])) start--;
    while (end < g.length && !br(g[end])) end++;
    const extend = action.startsWith("select_"),
      move = extend ? action.slice(7) : action;
    let target: number | undefined;
    if (extend && move === "all") {
      this.select(0, g.length);
      return event("select");
    }
    if (move === "left")
      target = !extend && lo !== hi ? lo : Math.max(0, at - 1);
    if (move === "right")
      target = !extend && lo !== hi ? hi : Math.min(g.length, at + 1);
    if (move === "home") target = start;
    if (move === "end") target = end;
    if (move === "up") {
      let p = Math.max(0, start - 1);
      while (p && !br(g[p - 1])) p--;
      target = start ? Math.min(p + at - start, start - 1) : at;
    }
    if (move === "down") {
      let e = Math.min(g.length, end + 1);
      while (e < g.length && !br(g[e])) e++;
      target = end < g.length ? Math.min(end + 1 + at - start, e) : at;
    }
    if (target !== undefined) {
      this.select(extend ? this.anchor : target, target);
      return event("select");
    }
    if (action === "copy" || action === "cut") {
      if (this.secret || lo === hi || (action === "cut" && this.readOnly))
        return event();
      const copy = g.slice(lo, hi).join("");
      if (action === "cut") this.replaceRange(lo, hi, "");
      return event(action, "", copy);
    }
    if (this.readOnly) return event();
    if (action === "undo" || action === "redo") {
      const [src, dst] =
        action === "undo"
          ? [this.undoStack, this.redoStack]
          : [this.redoStack, this.undoStack];
      const previous = src.pop();
      if (!previous) return event();
      dst.push([this.value, this.cursor, this.anchor]);
      [this.value, this.cursor, this.anchor] = previous;
      return event("change");
    }
    let a = lo,
      b = hi;
    if (action === "backspace") {
      if (a === b) a = Math.max(0, a - 1);
      text = "";
    } else if (action === "delete") {
      if (a === b) b = Math.min(g.length, b + 1);
      text = "";
    } else if (["insert", "paste", "newline"].includes(action)) {
      if (action === "newline") text = "\n";
      text = text.replace(/\r\n|\r/g, "\n").replace(/\t/g, " ");
      text = [...text]
        .filter((c) =>
          c === "\n" ? this.multiline : !/[\x00-\x1f\x7f-\x9f]/.test(c),
        )
        .join("");
    } else return event();
    return this.replaceRange(a, b, text);
  }
  window(width: number): { text: string; x: number; glyphWidth: number } {
    const g = graphemes(this.display()),
      at = Math.min(g.length, Math.max(0, this.cursor)),
      n = at < g.length ? Math.max(1, cells(g[at])) : 1;
    let start = 0;
    while (start < at && cells(g.slice(start, at).join("")) + n > width)
      start++;
    if (n > width) return { text: "", x: 0, glyphWidth: 1 };
    return {
      text: clip(g.slice(start).join(""), width),
      x: cells(g.slice(start, at).join("")),
      glyphWidth: n,
    };
  }
  private visualRows(): { index: number; glyph: string }[][] {
    const rows: { index: number; glyph: string }[][] = [[]];
    graphemes(this.value).forEach((g, i) => {
      if (this.multiline && ["\r", "\n", "\r\n"].includes(g)) rows.push([]);
      else rows.at(-1)!.push({ index: i, glyph: this.secret ? "*" : g });
    });
    return rows;
  }
  draw(c: Canvas, r: Rect, focused = true): void {
    const role = this.disabled ? "disabled" : this.readOnly ? "body" : "field";
    c.fill(r, role);
    if (r.width <= 0 || r.height <= 0) return;
    const rows = this.visualRows(),
      raw = graphemes(this.value);
    let cy = this.multiline
      ? raw
          .slice(0, this.cursor)
          .filter((g) => ["\r", "\n", "\r\n"].includes(g)).length
      : 0;
    cy = Math.min(cy, rows.length - 1);
    const cx = rows[cy]
        .filter((g) => g.index < this.cursor)
        .reduce((n, g) => n + cells(g.glyph), 0),
      cw = Math.max(
        1,
        cells(rows[cy].find((g) => g.index === this.cursor)?.glyph ?? " "),
      );
    this.scrollY = Math.max(0, Math.min(this.scrollY, cy), cy - r.height + 1);
    this.scrollX = Math.max(
      0,
      Math.min(this.scrollX, cx),
      cx + Math.min(cw, r.width) - r.width,
    );
    const lo = Math.min(this.anchor, this.cursor),
      hi = Math.max(this.anchor, this.cursor);
    rows.slice(this.scrollY, this.scrollY + r.height).forEach((row, y) => {
      let x = 0;
      for (const g of row) {
        const n = cells(g.glyph),
          local = x - this.scrollX;
        if (local >= 0 && local + n <= r.width)
          c.write(
            r.x + local,
            r.y + y,
            g.glyph,
            lo <= g.index && g.index < hi ? "selection" : role,
            false,
            n,
            true,
          );
        x += n;
      }
    });
    if (focused && !this.disabled && !this.readOnly && cw <= r.width)
      c.setCursor(r.x + cx - this.scrollX, r.y + cy - this.scrollY, cw);
  }
  click(
    x: number,
    y: number,
    width: number,
    height: number,
    extend = false,
  ): Event {
    if (this.disabled || x < 0 || y < 0 || x >= width || y >= height)
      return event();
    const rows = this.visualRows(),
      rowIndex = Math.min(rows.length - 1, this.scrollY + y),
      row = rows[rowIndex];
    let cell = 0,
      target = row.length
        ? row.at(-1)!.index + 1
        : rows.slice(0, rowIndex).reduce((n, r) => n + r.length + 1, 0);
    for (const g of row) {
      const n = cells(g.glyph);
      if (x + this.scrollX < cell + n) {
        target = g.index;
        break;
      }
      cell += n;
    }
    this.select(extend ? this.anchor : target, target);
    return event("select");
  }
}
export interface FormOption {
  id: string;
  label?: string;
  disabled?: boolean;
}
export interface Field {
  id: string;
  kind?:
    | "text"
    | "textarea"
    | "password"
    | "button"
    | "checkbox"
    | "radio"
    | "select";
  label?: string;
  value?: string;
  required?: boolean;
  checked?: boolean;
  options?: FormOption[];
  state?: Partial<ControlState>;
  help?: string;
  error?: string;
  choice?: string;
  action?: string;
  open?: boolean;
  pending?: string;
  height?: number;
}
export interface FormRow {
  id: string;
  text: string;
  role: string;
  option?: string;
  input?: boolean;
  focused?: boolean;
  sourceRow?: number;
}
export class Form {
  readonly fields: Field[];
  readonly inputs = new Map<string, Text>();
  focused = "";
  scroll = 0;
  private hits: FormRow[] = [];
  private layoutWidth = 0;
  constructor(fields: Field[]) {
    unique(fields);
    this.fields = clone(fields);
    for (const f of this.fields) {
      f.kind ??= "text";
      f.state = new ControlState(f.state);
      f.options ??= [];
      unique(f.options);
      if (
        ![
          "text",
          "textarea",
          "password",
          "button",
          "checkbox",
          "radio",
          "select",
        ].includes(f.kind) ||
        f.open
      )
        throw new Error("invalid kind/open select");
      if (f.choice && !f.options.some((o) => o.id === f.choice))
        throw new Error("unknown choice");
      if (["text", "textarea", "password"].includes(f.kind)) {
        const t = new Text(f.value ?? "", {
          secret: f.kind === "password",
          multiline: f.kind === "textarea",
        });
        this.inputs.set(f.id, t);
        f.value = t.display();
      }
    }
    this.eligible();
  }
  private field(id: string): Field | undefined {
    return this.fields.find((f) => f.id === id);
  }
  private eligible(): Field[] {
    const items = this.fields.filter(
      (f) => new ControlState(f.state).focusable,
    );
    if (!items.some((f) => f.id === this.focused))
      this.focused = items[0]?.id ?? "";
    return items;
  }
  focus(id: string): boolean {
    const f = this.field(id);
    if (!f || !new ControlState(f.state).focusable) return false;
    for (const v of this.fields) v.open = false;
    this.focused = id;
    return true;
  }
  atTabBoundary(previous = false): boolean {
    const items = this.eligible();
    return (
      !items.length ||
      this.focused === items[previous ? 0 : items.length - 1].id
    );
  }
  setState(id: string, state: Partial<ControlState>): boolean {
    const f = this.field(id);
    if (!f) return false;
    f.state = new ControlState(state);
    if (!new ControlState(f.state).editable) f.open = false;
    this.eligible();
    return true;
  }
  setFeedback(id: string, help = "", error = ""): boolean {
    const f = this.field(id);
    if (!f) return false;
    f.help = help;
    f.error = error;
    f.state = new ControlState({ ...f.state, invalid: !!error });
    return true;
  }
  value(id: string): string {
    const f = this.field(id);
    if (!f) throw new Error("unknown field");
    return this.inputs.get(id)?.value ?? f.value ?? "";
  }
  selectText(id: string, a: number, c: number): boolean {
    const t = this.inputs.get(id);
    if (!t) return false;
    t.select(a, c);
    return true;
  }
  missing(): string[] {
    return this.fields
      .filter((f) => {
        const empty = this.inputs.has(f.id)
          ? /^\p{White_Space}*$/u.test(this.value(f.id))
          : f.kind === "checkbox"
            ? !f.checked
            : ["radio", "select"].includes(f.kind!)
              ? !f.choice
              : false;
        return (
          !f.state?.disabled &&
          (f.error || f.state?.invalid || (f.required && empty))
        );
      })
      .map((f) => f.id);
  }
  handle(action: string, text = ""): Event {
    const items = this.eligible();
    if (action === "next" || action === "previous") {
      if (items.length) {
        const i = items.findIndex((f) => f.id === this.focused);
        this.focus(
          items[
            (i + items.length + (action === "next" ? 1 : -1)) % items.length
          ].id,
        );
      }
      return event();
    }
    if (action === "submit") {
      const missing = this.missing();
      return event(missing.length ? "invalid" : "submit", "", "", missing);
    }
    const f = this.field(this.focused);
    if (!f) return event();
    const state = new ControlState(f.state);
    if (action === "cancel") {
      if (f.open) {
        f.open = false;
        return event();
      }
      return event("cancel", f.id);
    }
    if (action === "insert" && text === " " && !this.inputs.has(f.id))
      action = "toggle";
    const input = this.inputs.get(f.id);
    if (input) {
      input.disabled = state.disabled;
      input.readOnly = !state.editable;
      if (action === "activate" && f.kind !== "textarea")
        return state.activatable ? this.handle("submit") : event();
      const e = input.handle(action === "activate" ? "newline" : action, text);
      f.value = input.display();
      if (["change", "cut"].includes(e.kind))
        f.state = new ControlState({ ...f.state, edited: true });
      return { ...e, id: f.id };
    }
    if (
      f.kind === "button" &&
      ["left", "right"].includes(action) &&
      !state.disabled
    ) {
      this.handle(action === "left" ? "previous" : "next");
      return event();
    }
    if (!state.activatable) return event();
    if (f.kind === "button" && ["activate", "toggle"].includes(action))
      return f.action === "submit"
        ? this.handle("submit")
        : event(f.action === "cancel" ? "cancel" : "activate", f.id);
    if (!state.editable) return event();
    let changed = false;
    if (f.kind === "checkbox" && ["activate", "toggle"].includes(action)) {
      f.checked = !f.checked;
      changed = true;
    } else if (f.kind === "radio" || f.kind === "select") {
      if (f.kind === "select" && ["activate", "toggle"].includes(action)) {
        if (f.open) {
          f.choice = f.pending;
          f.open = false;
          changed = true;
        } else {
          f.open = true;
          f.pending = f.choice || f.options?.find((o) => !o.disabled)?.id || "";
          return event();
        }
      } else if (
        ["left", "right", "up", "down", "activate", "toggle"].includes(action)
      ) {
        if (f.kind === "select" && !f.open) return event();
        const ids = (f.options ?? [])
          .filter((o) => !o.disabled)
          .map((o) => o.id);
        if (!ids.length) return event();
        const at = ids.indexOf((f.open ? f.pending : f.choice) ?? "");
        const target = ["left", "up"].includes(action)
          ? (Math.max(0, at) + ids.length - 1) % ids.length
          : at < 0
            ? 0
            : (at + 1) % ids.length;
        if (f.kind === "select") f.pending = ids[target];
        else {
          f.choice = ids[target];
          changed = true;
        }
      }
    }
    if (changed) {
      f.state = new ControlState({ ...f.state, edited: true });
      return event("change", f.id);
    }
    return event();
  }
  clickField(id: string, option = ""): Event {
    const f = this.field(id);
    if (
      !f ||
      f.state?.disabled ||
      (f.options ?? []).some((o) => o.id === option && o.disabled)
    )
      return event();
    if (this.focused !== id) this.focus(id);
    const state = new ControlState(f.state);
    if (f.kind === "button") return this.handle("activate");
    if (!state.editable) return event();
    if (f.kind === "select" && !f.open) return this.handle("activate");
    if (option && ["radio", "select"].includes(f.kind!)) {
      if (!(f.options ?? []).some((o) => o.id === option && !o.disabled))
        return event();
      f.choice = option;
      f.open = false;
      f.state = new ControlState({ ...f.state, edited: true });
      return event("change", f.id);
    }
    return ["checkbox", "select"].includes(f.kind!)
      ? this.handle("activate")
      : event();
  }
  layout(width: number, height: number): FormRow[] {
    const rows: FormRow[] = [];
    let anchor = 0;
    for (const f of this.fields) {
      const current = f.id === this.focused,
        state = new ControlState(f.state),
        role = state.disabled
          ? "disabled"
          : f.error || state.invalid
            ? "error"
            : state.role;
      let markers = state.markers;
      if (state.disabled) markers = markers.replace(/^-/, "");
      if (current) anchor = rows.length;
      rows.push({
        id: f.id,
        text:
          (current ? "> " : "  ") +
          (f.label ?? "") +
          (f.required ? " *" : "") +
          (markers ? " " + markers : ""),
        role,
        focused: current,
      });
      if (this.inputs.has(f.id)) {
        const display = this.inputs.get(f.id)!.display(),
          lines =
            f.kind === "textarea" ? display.split(/\r\n|\r|\n/) : [display];
        lines
          .slice(0, f.kind === "textarea" ? Math.max(1, f.height ?? 3) : 1)
          .forEach((line, i) =>
            rows.push({
              id: f.id,
              text: "  " + line,
              role: state.disabled ? "disabled" : "field",
              input: true,
              sourceRow: i,
            }),
          );
      } else if (f.kind === "checkbox")
        rows.push({ id: f.id, text: f.checked ? "  [x]" : "  [ ]", role });
      else if (f.kind === "button")
        rows.push({
          id: f.id,
          text: "  [ " + (f.label ?? "") + (state.busy ? " ~" : "") + " ]",
          role: state.disabled ? "disabled" : state.busy ? "hint" : "button",
          focused: current,
        });
      else
        for (const o of f.options ?? []) {
          if (f.kind === "select" && !f.open && o.id !== f.choice) continue;
          rows.push({
            id: f.id,
            text:
              "  (" +
              (o.id === (f.open ? f.pending : f.choice) ? "*" : " ") +
              ") " +
              (o.label ?? ""),
            role: o.disabled || state.disabled ? "disabled" : role,
            option: o.id,
          });
        }
      if (f.error) rows.push({ id: f.id, text: "! " + f.error, role: "error" });
      else if (f.help)
        rows.push({ id: f.id, text: "  " + f.help, role: "hint" });
    }
    width = Math.max(0, width);
    height = Math.max(0, height);
    this.scroll = Math.min(
      Math.max(0, anchor - Math.max(0, height - 2)),
      Math.max(0, rows.length - height),
    );
    this.layoutWidth = width;
    this.hits = rows
      .slice(this.scroll, this.scroll + height)
      .map((r) => ({ ...r, text: clip(r.text, width) }));
    return this.hits;
  }
  click(x: number, y: number, height = 10): Event {
    if (x < 0) return event();
    if (!this.hits.length) return event();
    if (
      x >= this.layoutWidth ||
      y < 0 ||
      y >= Math.min(height, this.hits.length)
    )
      return event();
    const row = this.hits[y];
    if (row.input && x >= 2) {
      const f = this.field(row.id)!;
      if (f.state?.disabled) return event();
      if (this.focused !== f.id) this.focus(f.id);
      const indices = this.hits
        .map((r, i) => (r.id === row.id && r.input ? i : -1))
        .filter((i) => i >= 0);
      return this.inputs
        .get(row.id)!
        .click(
          x - 2,
          y - indices[0],
          Math.max(0, this.layoutWidth - 2),
          indices.length,
        );
    }
    return this.clickField(row.id, row.option);
  }
  draw(c: Canvas, r: Rect, focused = true): void {
    c.fill(r);
    const rows = this.layout(r.width, r.height);
    rows.forEach((row, y) =>
      c.write(
        r.x,
        r.y + y,
        row.text,
        row.role,
        focused && !!row.focused,
        r.width,
      ),
    );
    for (const f of this.fields) {
      const indices = rows
        .map((row, i) => (row.id === f.id && row.input ? i : -1))
        .filter((i) => i >= 0);
      if (!indices.length) continue;
      const t = this.inputs.get(f.id)!,
        state = new ControlState(f.state);
      t.disabled = state.disabled;
      t.readOnly = !state.editable;
      t.draw(
        c,
        rect(
          r.x + Math.min(2, r.width),
          r.y + indices[0],
          Math.max(0, r.width - 2),
          indices.length,
        ),
        focused && this.focused === f.id,
      );
    }
  }
}
export class Control extends Form {
  constructor(field: Field) {
    super([field]);
  }
}
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
  cells: { [id: string]: string | null };
  state?: Partial<ControlState>;
  cellStates?: { [id: string]: Partial<ControlState> };
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
}
export class Grid {
  columns: Column[];
  rows: Record[];
  row = 0;
  column = 0;
  top = 0;
  editEnabled = false;
  edit: GridEdit | null = null;
  prepare: ((row: Record, column: Column) => boolean) | null = null;
  private serial = 0;
  private revision = 0;
  constructor(columns: Column[], rows: Record[]) {
    unique(columns);
    unique(rows);
    if (
      columns.some(
        (c) =>
          (c.width ?? 12) < 1 || !["", "left", "right"].includes(c.pin ?? ""),
      )
    )
      throw new Error("invalid columns");
    this.columns = clone(columns);
    this.rows = clone(rows);
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
  private current(): [Record, Column] | null {
    const cols = this.visibleColumns();
    if (!cols.length || !this.rows.length) return null;
    this.row = Math.max(0, Math.min(this.row, this.rows.length - 1));
    this.column = Math.max(0, Math.min(this.column, cols.length - 1));
    return [this.rows[this.row], cols[this.column]];
  }
  setRows(rows: Record[]): void {
    unique(rows);
    const id = this.current()?.[0].id;
    this.rows = clone(rows);
    this.row = Math.max(
      0,
      rows.findIndex((r) => r.id === id),
    );
    this.edit = null;
    this.revision++;
  }
  beginEdit(first?: string): boolean {
    const current = this.current();
    if (!current || this.edit || !this.editEnabled) return false;
    const [r, c] = current,
      state = new ControlState(r.cellStates?.[c.id] ?? r.state);
    if (!c.editable || !state.editable || (this.prepare && !this.prepare(r, c)))
      return false;
    const value = r.cells[c.id] ?? null;
    this.edit = {
      id: ++this.serial,
      rowId: r.id,
      columnId: c.id,
      original: value,
      null: value === null,
      buffer: new Text(first ?? value ?? "", { multiline: false }),
      pending: false,
      error: "",
      revision: this.revision,
    };
    return true;
  }
  resolveEdit(id: number, error = "", rows?: Record[]): boolean {
    if (
      !this.edit ||
      !this.edit.pending ||
      this.edit.id !== id ||
      this.edit.revision !== this.revision
    )
      return false;
    if (error) {
      this.edit.pending = false;
      this.edit.error = error;
      return true;
    }
    this.edit = null;
    if (rows) this.setRows(rows);
    return true;
  }
  handle(action: string, height = 10, text = ""): Event {
    const e = this.edit;
    if (e) {
      if (action === "cancel") {
        this.edit = null;
        return event("edit_cancel", e.rowId);
      }
      if (e.pending) return event();
      if (action === "null") {
        e.null = !e.null;
        return event("edit_change", e.rowId);
      }
      if (action === "submit" || action === "activate") {
        const current = this.current();
        if (
          !current ||
          current[0].id !== e.rowId ||
          current[1].id !== e.columnId
        ) {
          this.edit = null;
          return event("edit_stale");
        }
        const [r, c] = current;
        if (
          !c.editable ||
          !new ControlState(r.cellStates?.[c.id] ?? r.state).editable ||
          (this.prepare && !this.prepare(r, c))
        )
          return event("edit_denied", r.id);
        e.pending = true;
        return event("edit_submit", e.rowId, "", {
          id: e.id,
          row_id: e.rowId,
          column_id: e.columnId,
          value: e.null ? null : e.buffer.value,
        });
      }
      if (["insert", "paste"].includes(action)) e.null = false;
      if (!e.null) e.buffer.handle(action, text);
      return event("edit_change", e.rowId);
    }
    const current = this.current();
    if (!current) return event();
    const [r, c] = current;
    if (action === "activate")
      return event(
        this.editEnabled
          ? this.beginEdit()
            ? "edit_begin"
            : "edit_denied"
          : "edit",
        r.id,
        "",
        { column_id: c.id },
      );
    if (action === "copy") return event("copy", r.id, r.cells[c.id] ?? "");
    if (action === "details")
      return event("details", r.id, "", {
        column_id: c.id,
        value: r.cells[c.id],
      });
    const moves: Dict<string, number> = {
      up: this.row - 1,
      down: this.row + 1,
      home: 0,
      end: this.rows.length - 1,
      page_up: this.row - Math.max(1, height - 1),
      page_down: this.row + Math.max(1, height - 1),
    };
    if (action in moves)
      this.row = Math.max(0, Math.min(this.rows.length - 1, moves[action]));
    if (action === "left" || action === "right")
      this.column = Math.max(
        0,
        Math.min(
          this.visibleColumns().length - 1,
          this.column + (action === "left" ? -1 : 1),
        ),
      );
    return event("select", this.rows[this.row].id, "", {
      column_id: this.visibleColumns()[this.column].id,
    });
  }
  find(query: string, previous = false, maxCells = 100000): boolean {
    const cols = this.visibleColumns(),
      total = cols.length * this.rows.length;
    if (!query || !total) return false;
    const start = this.row * cols.length + this.column;
    for (let step = 1; step <= Math.min(total, maxCells); step++) {
      const pos = (start + (previous ? -step : step) + total) % total,
        r = Math.floor(pos / cols.length),
        c = pos % cols.length;
      if (
        (this.rows[r].cells[cols[c].id] ?? "")
          .toLowerCase()
          .includes(query.toLowerCase())
      ) {
        this.row = r;
        this.column = c;
        return true;
      }
    }
    return false;
  }
  draw(canvas: Canvas, r: Rect, focused = true, ascii = false): void {
    canvas.fill(r);
    if (!this.current() || !r.width || !r.height) return;
    const h = Math.max(1, r.height - 1);
    this.top = Math.max(0, Math.min(this.top, this.row));
    if (this.row >= this.top + h) this.top = this.row - h + 1;
    let x = r.x;
    this.visibleColumns().forEach((column, ci) => {
      const w = Math.min(column.width ?? 12, r.x + r.width - x);
      if (w <= 0) return;
      canvas.write(
        x,
        r.y,
        clip(column.label ?? column.id, w, true),
        "header",
        false,
        w,
      );
      this.rows.slice(this.top, this.top + h).forEach((row, dy) => {
        const y = r.y + dy + 1,
          state = new ControlState(row.cellStates?.[column.id]),
          current = this.top + dy === this.row && ci === this.column,
          e = this.edit,
          editing = e && e.rowId === row.id && e.columnId === column.id;
        let role =
          row.state?.disabled || state.disabled
            ? "disabled"
            : state.invalid
              ? "error"
              : state.edited
                ? "edited"
                : current
                  ? "selection"
                  : "body";
        let text = row.cells[column.id] ?? "NULL";
        if (editing) {
          role = e.pending ? "hint" : e.error ? "error" : "field";
          const p = e.buffer.window(w - Number(state.edited));
          text = e.null ? "NULL" : p.text;
          if (focused && !e.null && !e.pending && w > Number(state.edited))
            canvas.setCursor(x + Number(state.edited) + p.x, y, p.glyphWidth);
        }
        text = clip((state.edited ? "*" : "") + text, w);
        canvas.write(
          x,
          y,
          text + " ".repeat(Math.max(0, w - cells(text))),
          role,
          focused && current,
          w,
          true,
        );
      });
      x += column.width ?? 12;
      if (x < r.x + r.width)
        for (let y = r.y; y < r.y + r.height; y++)
          canvas.write(x, y, ascii ? "|" : "│", "hint");
      x++;
    });
  }
}
export interface FocusTarget {
  id: string;
  state?: Partial<ControlState>;
  hidden?: boolean;
}
export interface InputRoute {
  scopeId: string;
  blocked: boolean;
}
export interface PopupCloseRequest {
  id: string;
  reason: "escape";
}
export class Focus {
  private scopes: {
    id: string;
    targets: FocusTarget[];
    focused: string;
    restore: string;
    dismissible: boolean;
  }[];
  constructor(id: string, targets: FocusTarget[]) {
    if (!id) throw new Error("empty root scope");
    unique(targets);
    const root = {
      id,
      targets: clone(targets),
      focused: "",
      restore: "",
      dismissible: false,
    };
    this.reconcile(root);
    this.scopes = [root];
  }
  private ids(scope: { targets: FocusTarget[] }): string[] {
    return scope.targets
      .filter((t) => !t.hidden && !t.state?.disabled)
      .map((t) => t.id);
  }
  private reconcile(scope: { targets: FocusTarget[]; focused: string }): void {
    const ids = this.ids(scope);
    if (!ids.includes(scope.focused)) scope.focused = ids[0] ?? "";
  }
  get focused(): string {
    return this.scopes.at(-1)!.focused;
  }
  get scopeId(): string {
    return this.scopes.at(-1)!.id;
  }
  get depth(): number {
    return this.scopes.length - 1;
  }
  open(
    id: string,
    targets: FocusTarget[],
    initial = "",
    dismissible = true,
  ): void {
    if (!id || this.scopes.length >= 65 || this.scopes.some((s) => s.id === id))
      throw new Error("invalid scope or depth");
    unique(targets);
    const scope = {
      id,
      targets: clone(targets),
      focused: "",
      restore: this.focused,
      dismissible,
    };
    this.reconcile(scope);
    if (initial) {
      if (!this.ids(scope).includes(initial))
        throw new Error("initial target not focusable");
      scope.focused = initial;
    }
    this.scopes.push(scope);
  }
  update(id: string, targets: FocusTarget[]): void {
    unique(targets);
    const scope = this.scopes.find((s) => s.id === id);
    if (!scope) throw new Error("unknown scope");
    const owned = clone(targets);
    scope.targets = owned;
    this.reconcile(scope);
  }
  close(id: string): Event {
    if (!this.depth || this.scopeId !== id)
      throw new Error("only top popup can close");
    const restore = this.scopes.pop()!.restore,
      top = this.scopes.at(-1)!;
    if (this.ids(top).includes(restore)) top.focused = restore;
    else this.reconcile(top);
    return event("focus", this.focused);
  }
  focus(id: string): boolean {
    const top = this.scopes.at(-1)!;
    if (!this.ids(top).includes(id)) return false;
    top.focused = id;
    return true;
  }
  move(previous = false): string {
    const top = this.scopes.at(-1)!,
      ids = this.ids(top);
    if (!ids.length) top.focused = "";
    else {
      const at = ids.indexOf(top.focused),
        next = previous
          ? (Math.max(0, at) + ids.length - 1) % ids.length
          : at < 0
            ? 0
            : (at + 1) % ids.length;
      top.focused = ids[next];
    }
    return this.focused;
  }
  requestClose(): PopupCloseRequest | undefined {
    return this.depth && this.scopes.at(-1)!.dismissible
      ? { id: this.scopeId, reason: "escape" }
      : undefined;
  }
  route(target = ""): InputRoute {
    return {
      scopeId: this.scopeId,
      blocked: !!target && target !== this.scopeId,
    };
  }
  blocked(scope: string): boolean {
    return this.route(scope).blocked;
  }
}
export interface MenuItem extends Item {
  mnemonic?: string;
}
export interface MenuEvent {
  kind: string;
  id: string;
  returnId: string;
  data: { return_id: string };
  text: string;
}
export interface MenuSpan {
  start: number;
  width: number;
  text: string;
  role: string;
}
export interface MenuRow {
  id: string;
  text: string;
  role: string;
  spans: MenuSpan[];
  focused: boolean;
}
export interface MenuBarCell {
  id: string;
  text: string;
  role: string;
  start: number;
  width: number;
  focused: boolean;
}
export interface MenuBarLayout {
  cells: MenuBarCell[];
  previous: boolean;
  next: boolean;
}
export class Menu {
  private items_: MenuItem[] = [];
  private index = new Map<string, MenuItem>();
  private children = new Map<string, string[]>();
  private path_: string[] = [];
  private focusMap = new Map<string, string>();
  private tops = new Map<string, number>();
  opened = false;
  private context = false;
  returnId = "";
  private bar = "";
  private barFirst = 0;
  backLabel = "Back";
  emptyLabel = "(empty)";
  private hits: MenuRow[] = [];
  private width = 0;
  constructor(items: MenuItem[]) {
    this.setItems(items);
  }
  get items(): readonly MenuItem[] {
    return clone(this.items_);
  }
  get path(): string[] {
    return [...this.path_];
  }
  get focused(): string {
    return this.focusMap.get(this.parent()) ?? "";
  }
  get barFocused(): string {
    return this.bar;
  }
  private static validate(items: MenuItem[]): {
    index: Map<string, MenuItem>;
    children: Map<string, string[]>;
  } {
    unique(items);
    if (items.length > 10000) throw new Error("too many menu items");
    const index = new Map(items.map((i) => [i.id, i])),
      children = new Map<string, string[]>(),
      keys = new Map<string, Set<string>>();
    for (const i of items) {
      if (i.id.startsWith("@")) throw new Error("reserved menu ID");
      const parent = i.parent ?? "",
        mnemonic = i.mnemonic ?? "";
      if (mnemonic) {
        const key = mnemonic.toLowerCase(),
          seen = keys.get(parent) ?? new Set<string>();
        if (!/^[a-z0-9]$/.test(key) || i.separator || seen.has(key))
          throw new Error("invalid/duplicate mnemonic");
        seen.add(key);
        keys.set(parent, seen);
      }
      children.set(parent, [...(children.get(parent) ?? []), i.id]);
    }
    for (const i of items) {
      if (i.separator && (children.get(i.id)?.length ?? 0) > 0)
        throw new Error("separator children");
      let parent = i.parent ?? "";
      const seen = new Set([i.id]);
      let depth = 1;
      while (parent) {
        const p = index.get(parent);
        if (!p || seen.has(parent) || p.separator)
          throw new Error("invalid parent/cycle");
        if (++depth > 32) throw new Error("menu depth exceeds32");
        seen.add(parent);
        parent = p.parent ?? "";
      }
    }
    return { index, children };
  }
  setItems(items: MenuItem[]): MenuEvent {
    const owned = clone(items),
      data = Menu.validate(owned);
    this.items_ = owned;
    this.index = data.index;
    this.children = data.children;
    this.focusMap = new Map(
      [...this.focusMap].filter(([p]) => !p || this.index.has(p)),
    );
    this.tops = new Map(
      [...this.tops].filter(([p]) => !p || this.index.has(p)),
    );
    this.hits = [];
    if (!this.usable(this.bar, "")) this.bar = this.first("");
    for (let n = 0; n < this.path_.length; n++) {
      const id = this.path_[n];
      if (
        !this.usable(id, n ? this.path_[n - 1] : "") ||
        !this.childIds(id).length
      )
        return this.close();
    }
    if (this.opened) this.reconcile();
    return this.none();
  }
  private none(): MenuEvent {
    return {
      kind: "",
      id: "",
      returnId: "",
      data: { return_id: "" },
      text: "",
    };
  }
  private event(kind: string, id = ""): MenuEvent {
    return {
      kind,
      id,
      returnId: this.returnId,
      data: { return_id: this.returnId },
      text: "",
    };
  }
  private childIds(parent: string): string[] {
    return this.children.get(parent) ?? [];
  }
  private parent(): string {
    return this.path_.at(-1) ?? "";
  }
  private usable(id: string, parent: string): boolean {
    const i = this.index.get(id);
    return !!i && (i.parent ?? "") === parent && !i.disabled && !i.separator;
  }
  private first(parent: string): string {
    return this.childIds(parent).find((id) => this.usable(id, parent)) ?? "";
  }
  private backAllowed(): boolean {
    return this.path_.length > 1 || (this.context && this.path_.length > 0);
  }
  private reconcile(): void {
    const p = this.parent(),
      id = this.focusMap.get(p) ?? "";
    if (id === "@back" && this.backAllowed()) return;
    if (!this.usable(id, p))
      this.focusMap.set(
        p,
        this.first(p) || (this.backAllowed() ? "@back" : ""),
      );
  }
  title(): string {
    return this.path_
      .map((id) => clean(this.index.get(id)!.label ?? ""))
      .join(" / ");
  }
  open(id = "", returnId = ""): MenuEvent {
    const path: string[] = [];
    let at = id;
    while (at) {
      const i = this.index.get(at);
      if (!i || i.disabled || i.separator) return this.none();
      path.unshift(at);
      at = i.parent ?? "";
    }
    this.returnId = returnId;
    this.path_ = path;
    this.hits = [];
    path.forEach((child, n) => this.focusMap.set(n ? path[n - 1] : "", child));
    this.context = !id;
    this.opened = true;
    if (path.length) this.bar = path[0];
    if (id && !this.childIds(id).length) return this.finish("activate", id);
    this.reconcile();
    return this.event("open", id);
  }
  private finish(kind: string, id = ""): MenuEvent {
    this.opened = false;
    this.path_ = [];
    this.hits = [];
    return this.event(kind, id);
  }
  close(): MenuEvent {
    return this.opened ? this.finish("close") : this.none();
  }
  back(): MenuEvent {
    if (!this.opened) return this.none();
    if (!this.backAllowed()) return this.close();
    this.path_.pop();
    this.reconcile();
    return this.event("back", this.parent());
  }
  focus(id: string): boolean {
    if (!this.opened) return false;
    if (
      (id === "@back" && this.backAllowed()) ||
      this.usable(id, this.parent())
    ) {
      this.focusMap.set(this.parent(), id);
      return true;
    }
    return false;
  }
  private enter(id: string): MenuEvent {
    this.path_.push(id);
    this.reconcile();
    return this.event("open", id);
  }
  private switchRoot(next: boolean): MenuEvent {
    const ids = this.childIds("").filter((id) => this.usable(id, ""));
    if (!ids.length) return this.none();
    let at = Math.max(0, ids.indexOf(this.bar));
    const step = next ? 1 : ids.length - 1;
    for (let n = 0; n < ids.length; n++) {
      at = (at + step) % ids.length;
      if (ids[at] !== this.bar && this.childIds(ids[at]).length)
        return this.open(ids[at], this.returnId);
    }
    return this.none();
  }
  handle(action: string, value = "", height = 10): MenuEvent {
    if (!this.opened) return this.none();
    this.reconcile();
    const p = this.parent(),
      id = this.focused;
    if (action === "cancel" || action === "back") return this.back();
    if (action === "close") return this.close();
    if (action === "left")
      return this.backAllowed()
        ? this.back()
        : this.context
          ? this.none()
          : this.switchRoot(false);
    if (action === "right") {
      if (this.usable(id, p) && this.childIds(id).length) return this.enter(id);
      return !this.backAllowed() && !this.context
        ? this.switchRoot(true)
        : this.none();
    }
    if (action === "activate") {
      if (id === "@back") return this.back();
      if (!this.usable(id, p)) return this.none();
      return this.childIds(id).length
        ? this.enter(id)
        : this.finish("activate", id);
    }
    if (action === "mnemonic") {
      if (!/^[a-z0-9]$/i.test(value)) return this.none();
      for (const candidate of this.childIds(p)) {
        const i = this.index.get(candidate)!;
        if (
          this.usable(candidate, p) &&
          i.mnemonic &&
          i.mnemonic.toLowerCase() === value.toLowerCase()
        ) {
          this.focusMap.set(p, candidate);
          return this.handle("activate", "", height);
        }
      }
      return this.none();
    }
    const ids = [
      ...(this.backAllowed() ? ["@back"] : []),
      ...this.childIds(p).filter((id) => this.usable(id, p)),
    ];
    if (!ids.length) return this.none();
    let at = Math.max(0, ids.indexOf(id));
    if (action === "previous" || action === "up")
      at = (at + ids.length - 1) % ids.length;
    else if (action === "next" || action === "down") at = (at + 1) % ids.length;
    else if (action === "first" || action === "home") at = 0;
    else if (action === "last" || action === "end") at = ids.length - 1;
    else if (action === "page_up")
      at = Math.max(0, at - Math.max(1, height - 1));
    else if (action === "page_down")
      at = Math.min(ids.length - 1, at + Math.max(1, height - 1));
    else return this.none();
    this.focusMap.set(p, ids[at]);
    return this.event("focus", ids[at]);
  }
  handleBar(action: string, value = ""): MenuEvent {
    const ids = this.childIds("").filter((id) => this.usable(id, ""));
    if (!ids.length) return this.none();
    let at = Math.max(0, ids.indexOf(this.bar));
    const event = (kind: string, id: string): MenuEvent => ({
      kind,
      id,
      returnId: "",
      data: { return_id: "" },
      text: "",
    });
    if (action === "previous" || action === "left")
      at = (at + ids.length - 1) % ids.length;
    else if (action === "next" || action === "right")
      at = (at + 1) % ids.length;
    else if (action === "first" || action === "home") at = 0;
    else if (action === "last" || action === "end") at = ids.length - 1;
    else if (action === "activate" || action === "down")
      return event("open_request", ids[at]);
    else if (action === "mnemonic") {
      if (!/^[a-z0-9]$/i.test(value)) return this.none();
      for (const id of ids) {
        const i = this.index.get(id)!;
        if (i.mnemonic && i.mnemonic.toLowerCase() === value.toLowerCase()) {
          this.bar = id;
          return event("open_request", id);
        }
      }
      return this.none();
    } else return this.none();
    this.bar = ids[at];
    return event("focus", this.bar);
  }
  clickId(id: string): MenuEvent {
    return this.focus(id) ? this.handle("activate") : this.none();
  }
  click(x: number, y: number, height = 10): MenuEvent {
    if (
      !this.opened ||
      x < 0 ||
      x >= this.width ||
      y < 0 ||
      y >= Math.min(height, this.hits.length)
    )
      return this.none();
    return this.clickId(this.hits[y].id);
  }
  private static label(i: MenuItem): string {
    return (
      (i.label ?? "") +
      (i.mnemonic ? " (" + i.mnemonic.toUpperCase() + ")" : "")
    );
  }
  private rows(): MenuItem[] {
    return [
      ...(this.backAllowed()
        ? [
            { id: "@back", label: this.backLabel },
            { id: "", separator: true },
          ]
        : []),
      ...this.childIds(this.parent()).map((id) => this.index.get(id)!),
    ];
  }
  contentSize(): [number, number] {
    const rows = this.rows();
    let width = 12;
    for (const i of rows)
      width = Math.max(
        width,
        cells(Menu.label(i)) +
          cells(i.secondary ?? "") +
          cells(i.shortcut ?? "") +
          cells(i.icon ?? "") +
          8,
      );
    return [Math.min(width, 4096), Math.max(1, rows.length)];
  }
  layout(width: number, height: number, ascii = false): MenuRow[] {
    this.hits = [];
    this.width = width = Math.max(0, Math.min(65535, width));
    height = Math.max(0, Math.min(4096, height));
    if (!this.opened || !width || !height) return [];
    this.reconcile();
    const rows = this.rows();
    if (!rows.length) {
      this.hits = [
        {
          id: "",
          text: clip(this.emptyLabel, width, true),
          role: "hint",
          spans: [],
          focused: false,
        },
      ];
      return this.hits;
    }
    const at = Math.max(
        0,
        rows.findIndex((i) => i.id === this.focused),
      ),
      p = this.parent();
    let top = Math.min(this.tops.get(p) ?? 0, at);
    if (at >= top + height) top = at - height + 1;
    top = Math.min(top, Math.max(0, rows.length - height));
    this.tops.set(p, top);
    for (const i of rows.slice(top, top + height)) {
      if (i.separator) {
        this.hits.push({
          id: "",
          text: (ascii ? "-" : "─").repeat(width),
          role: "hint",
          spans: [],
          focused: false,
        });
        continue;
      }
      const current = i.id === this.focused,
        role = i.disabled ? "disabled" : current ? "selection" : "surface",
        icon = (ascii ? i.ascii_icon || (i.icon ? "*" : "") : i.icon) ?? "",
        prefix = (current ? "> " : "  ") + (icon ? icon + " " : ""),
        text =
          prefix +
          (i.id === "@back" ? "< " + (i.label ?? "") : Menu.label(i)) +
          (i.secondary ? "  " + i.secondary : ""),
        suffix = this.childIds(i.id).length ? (ascii ? " >" : " ›") : "",
        shortcut = clean(i.shortcut ?? ""),
        reserve = Math.min(Math.floor(width / 3), cells(shortcut)),
        tail = reserve ? " " + clip(shortcut, reserve) + suffix : suffix,
        tw = Math.min(width, cells(tail)),
        left = clip(text, width - tw, true),
        spans: MenuSpan[] = [{ start: 0, width, text: left, role }];
      if (tw)
        spans.push({
          start: width - tw,
          width: tw,
          text: clip(tail, tw),
          role: role === "surface" ? "hint" : role,
        });
      this.hits.push({
        id: i.id,
        text:
          left +
          " ".repeat(Math.max(0, width - tw - cells(left))) +
          clip(tail, tw),
        role,
        spans,
        focused: current,
      });
    }
    return this.hits;
  }
  draw(c: Canvas, r: Rect, ascii = false): void {
    if (!this.opened) return;
    c.fill(r, "surface");
    this.layout(r.width, r.height, ascii).forEach((row, y) => {
      c.fill(rect(r.x, r.y + y, r.width, 1), row.role);
      if (!row.spans.length)
        c.write(r.x, r.y + y, row.text, row.role, false, r.width, true);
      for (const span of row.spans)
        c.write(
          r.x + span.start,
          r.y + y,
          span.text,
          span.role,
          false,
          span.width,
          true,
        );
    });
  }
  /** Paint a host-positioned popup and return its content hit-test rectangle. */
  drawPopup(c: Canvas, r: Rect, title = "", padding = 1, ascii = false): Rect {
    if (!this.opened) return rect(r.x, r.y, 0, 0);
    const inner = c.panel(r, title, false, ascii);
    padding = Math.max(
      0,
      Math.min(4096, Number.isFinite(padding) ? Math.trunc(padding) : 0),
    );
    const px = Math.min(padding, Math.floor(inner.width / 2)),
      py = Math.min(padding, Math.floor(inner.height / 2));
    const content = rect(
      inner.x + px,
      inner.y + py,
      Math.max(0, inner.width - 2 * px),
      Math.max(0, inner.height - 2 * py),
    );
    this.draw(c, content, ascii);
    return content;
  }
  barLayout(width: number): MenuBarLayout {
    const out: MenuBarLayout = { cells: [], previous: false, next: false };
    width = Math.max(0, Math.min(65535, width));
    if (width < 3) return out;
    const ids = this.childIds("").filter(
      (id) => !this.index.get(id)!.separator,
    );
    if (!ids.length) return out;
    const target = Math.max(0, ids.indexOf(this.bar));
    this.barFirst = Math.min(this.barFirst, target);
    const size = (n: number) =>
        Math.min(24, cells(Menu.label(this.index.get(ids[n])!)) + 2),
      sum = (a: number, b: number) =>
        ids.slice(a, b + 1).reduce((n, _, offset) => n + size(a + offset), 0);
    while (this.barFirst < target && sum(this.barFirst, target) > width - 2)
      this.barFirst++;
    while (this.barFirst > 0 && sum(this.barFirst - 1, target) <= width - 2)
      this.barFirst--;
    let x = 1,
      last = this.barFirst;
    for (let n = this.barFirst; n < ids.length; n++) {
      if (x >= width - 1) break;
      const i = this.index.get(ids[n])!,
        w = Math.min(size(n), width - 1 - x),
        current = i.id === this.bar,
        role = i.disabled ? "disabled" : current ? "selection" : "header";
      out.cells.push({
        id: i.id,
        text: clip(" " + Menu.label(i) + " ", w, true),
        role,
        start: x,
        width: w,
        focused: current,
      });
      x += w;
      last = n + 1;
    }
    out.previous = this.barFirst > 0;
    out.next = last < ids.length;
    return out;
  }
  barClick(x: number, width: number): MenuEvent {
    if (x < 0 || x >= width) return this.none();
    const l = this.barLayout(width);
    if (x === 0 && l.previous) return this.handleBar("previous");
    if (x + 1 === width && l.next) return this.handleBar("next");
    for (const c of l.cells)
      if (x >= c.start && x < c.start + c.width && this.usable(c.id, "")) {
        this.bar = c.id;
        return {
          kind: "open_request",
          id: c.id,
          returnId: "",
          data: { return_id: "" },
          text: "",
        };
      }
    return this.none();
  }
  drawBar(c: Canvas, r: Rect): void {
    if (r.height <= 0) return;
    c.fill(rect(r.x, r.y, r.width, 1), "surface");
    const l = this.barLayout(r.width);
    for (const cell of l.cells) {
      c.fill(rect(r.x + cell.start, r.y, cell.width, 1), cell.role);
      c.write(
        r.x + cell.start,
        r.y,
        cell.text,
        cell.role,
        false,
        cell.width,
        true,
      );
    }
    if (l.previous) c.write(r.x, r.y, "<", "hint", false, 1);
    if (l.next) c.write(r.x + r.width - 1, r.y, ">", "hint", false, 1);
  }
}
export function menuPlacement(
  anchor: Rect,
  viewport: Rect,
  width: number,
  height: number,
): Rect {
  const w = Math.min(Math.max(0, width), Math.max(0, viewport.width)),
    h = Math.min(Math.max(0, height), Math.max(0, viewport.height)),
    x = Math.max(
      viewport.x,
      Math.min(viewport.x + Math.max(0, viewport.width) - w, anchor.x),
    );
  let y = anchor.y + Math.max(0, anchor.height);
  if (y + h > viewport.y + viewport.height) y = anchor.y - h;
  y = Math.max(
    viewport.y,
    Math.min(viewport.y + Math.max(0, viewport.height) - h, y),
  );
  return rect(x, y, w, h);
}

export interface SplitLayout {
  first: number;
  divider: number;
  second: number;
  compact: boolean;
}
export class Split {
  preferred: number;
  firstMin: number;
  secondMin: number;
  constructor(firstMin = 1, secondMin = 1, preferred = 0) {
    this.firstMin = Math.max(1, firstMin);
    this.secondMin = Math.max(1, secondMin);
    this.preferred = Math.max(0, preferred);
  }
  layout(total: number): SplitLayout {
    if (total < 0) throw new Error("negative split size");
    if (total < this.firstMin + this.secondMin + 1)
      return { first: 0, divider: 0, second: total, compact: true };
    const first = Math.max(
      this.firstMin,
      Math.min(
        total - 1 - this.secondMin,
        this.preferred || Math.floor((total - 1) / 2),
      ),
    );
    return { first, divider: 1, second: total - first - 1, compact: false };
  }
  resize(total: number, position: number): boolean {
    const old = this.layout(total);
    if (old.compact) return false;
    this.preferred = Math.max(
      this.firstMin,
      Math.min(total - 1 - this.secondMin, position),
    );
    return old.first !== this.preferred;
  }
}
export function split(
  r: Rect,
  preferred: number,
  firstMin = 0,
  secondMin = 0,
  vertical = false,
): [Rect, Rect, Rect] {
  if (Math.min(r.width, r.height, preferred, firstMin, secondMin) < 0)
    throw new Error("negative geometry");
  const layout = new Split(firstMin, secondMin, preferred).layout(
    vertical ? r.height : r.width,
  );
  if (layout.compact) return [rect(r.x, r.y), rect(r.x, r.y), r];
  return vertical
    ? [
        rect(r.x, r.y, r.width, layout.first),
        rect(r.x, r.y + layout.first, r.width, 1),
        rect(r.x, r.y + layout.first + 1, r.width, layout.second),
      ]
    : [
        rect(r.x, r.y, layout.first, r.height),
        rect(r.x + layout.first, r.y, 1, r.height),
        rect(r.x + layout.first + 1, r.y, layout.second, r.height),
      ];
}

export function container(
  r: Rect,
  ids: string[],
  vertical = false,
  gap = 0,
): Map<string, Rect> {
  if (ids.some((id) => !id) || new Set(ids).size !== ids.length || gap < 0)
    throw new Error("invalid container");
  const out = new Map<string, Rect>(),
    size = vertical ? r.height : r.width,
    usable = Math.max(0, size - gap * (ids.length - 1));
  let offset = 0;
  ids.forEach((id, i) => {
    const extent = Math.min(
      Math.floor(usable / ids.length) + Number(i < usable % ids.length),
      Math.max(0, size - offset),
    );
    out.set(
      id,
      vertical
        ? rect(r.x, r.y + offset, r.width, extent)
        : rect(r.x + offset, r.y, extent, r.height),
    );
    offset = Math.min(size, offset + extent + gap);
  });
  return out;
}
export interface LineRun {
  text: string;
  role: string;
  id: string;
  start: number;
  width: number;
}
export class LineLayout {
  readonly runs: LineRun[] = [];
  omitted = 0;
  get text(): string {
    return this.runs.map((r) => r.text).join("");
  }
  add(text: string, role: string, id = ""): void {
    text = clean(text);
    this.runs.push({
      text,
      role,
      id,
      start: cells(this.text),
      width: cells(text),
    });
  }
  hit(x: number): string {
    return (
      this.runs.find((r) => x >= r.start && x < r.start + r.width)?.id ?? ""
    );
  }
  draw(c: Canvas, r: Rect): void {
    c.fill(r);
    for (const run of this.runs)
      c.write(
        r.x + run.start,
        r.y,
        run.text,
        run.role,
        false,
        Math.max(0, r.width - run.start),
      );
  }
}
function tailCells(text: string, width: number): string {
  text = clean(text);
  if (cells(text) <= width) return text;
  if (width <= 0) return "";
  const parts = graphemes(text);
  let start = parts.length,
    used = 0;
  while (start > 0 && used + cells(parts[start - 1]) <= width - 1)
    used += cells(parts[--start]);
  return "~" + parts.slice(start).join("");
}
export function pathRuns(
  items: { id: string; label: string }[],
  width: number,
): LineLayout {
  const out = new LineLayout();
  if (!items.length || width <= 0) return out;
  const full =
    items.reduce((n, p) => n + cells(p.label), 0) + 3 * (items.length - 1);
  if (full <= width) {
    items.forEach((p, i) => {
      if (i) out.add(" / ", "hint");
      out.add(p.label, i + 1 === items.length ? "body" : "hint", p.id);
    });
    return out;
  }
  const last = items.at(-1)!;
  let prefix = "";
  if (
    items.length > 2 &&
    cells(items[0].label) + 9 + cells(last.label) <= width
  ) {
    out.add(items[0].label, "hint", items[0].id);
    prefix = " / ... / ";
  } else if (items.length > 1 && width >= 7) prefix = "... / ";
  out.add(prefix, "hint");
  out.add(tailCells(last.label, width - cells(out.text)), "body", last.id);
  return out;
}
export function breadcrumbs(
  items: { id: string; label: string }[],
  width: number,
  ascii = false,
): string {
  void ascii;
  return pathRuns(items, width).text;
}
export interface StatusItem {
  id: string;
  text: string;
  role?: string;
  priority?: number;
}
export function status(items: StatusItem[], width: number): StatusItem[] {
  let remaining = Math.max(0, width);
  const selected = new Set<number>();
  items
    .map((item, i) => ({ item, i }))
    .sort(
      (a, b) => (b.item.priority ?? 0) - (a.item.priority ?? 0) || a.i - b.i,
    )
    .forEach(({ item, i }) => {
      const need = cells(item.text) + (selected.size ? 3 : 0);
      if (need <= remaining) {
        selected.add(i);
        remaining -= need;
      }
    });
  return items.filter((_, i) => selected.has(i));
}
export function statusLine(source: StatusItem[], width: number): LineLayout {
  const items = [...source].sort(
      (a, b) => (b.priority ?? 0) - (a.priority ?? 0),
    ),
    out = new LineLayout();
  out.omitted = items.length;
  if (width <= 0) return out;
  let included = 0;
  for (let i = 0; i < items.length; i++) {
    const item = items[i],
      reserve = i + 1 < items.length ? ` +${items.length - i - 1}`.length : 0,
      prefix =
        (
          {
            warning: "! ",
            error: "! ",
            edited: "* ",
            success: "+ ",
            info: "i ",
          } as Dict<string, string>
        )[item.role ?? ""] ?? "";
    let sep = included ? " | " : "",
      text = prefix + clean(item.text);
    const needed = cells(sep) + cells(text);
    if (needed + reserve > width - cells(out.text)) {
      if (included) break;
      const available = width - reserve > 0 ? width - reserve : width;
      text =
        available === 1 && prefix
          ? prefix.slice(0, 1)
          : clip(text, available, true);
      sep = "";
    }
    if (sep) out.add(sep, "hint");
    out.add(text, item.role || "body", item.id);
    included++;
    if (needed + reserve > width) break;
  }
  out.omitted = items.length - included;
  const marker = ` +${out.omitted}`;
  if (out.omitted && cells(out.text) + marker.length <= width)
    out.add(marker, "hint");
  return out;
}
export interface NoticeAction {
  id: string;
  label?: string;
  disabled?: boolean;
}
export interface Notice {
  id: string;
  text?: string;
  detail?: string;
  severity?: string;
  priority?: number;
  expiresAt?: number;
  persistent?: boolean;
  actions?: NoticeAction[];
}
export interface NoticeEvent {
  kind: string;
  id: string;
  action: string;
}
export interface FeedbackSpan {
  start: number;
  width: number;
  text: string;
  role: string;
  action: string;
  disabled: boolean;
}
export interface FeedbackRow {
  id: string;
  text: string;
  role: string;
  focused: boolean;
  spans: FeedbackSpan[];
}
const noticeSeverity: Dict<string, number> = {
  info: 0,
  success: 1,
  warning: 2,
  error: 3,
};
function feedbackNumber(n: number): number {
  if (!Number.isSafeInteger(n) || n < 0)
    throw new Error("expected a nonnegative safe integer");
  return n;
}
function feedbackEvent(kind = "", id = "", action = ""): NoticeEvent {
  return { kind, id, action };
}
function feedbackRow(
  id = "",
  text = "",
  role = "body",
  focused = false,
  spans: FeedbackSpan[] = [],
): FeedbackRow {
  return { id, text, role, focused, spans };
}
function feedbackDraw(c: Canvas, r: Rect, rows: FeedbackRow[]): void {
  c.fill(r);
  rows.slice(0, Math.max(0, r.height)).forEach((row, y) => {
    c.write(r.x, r.y + y, row.text, row.role, false, r.width, true);
    for (const s of row.spans)
      c.write(r.x + s.start, r.y + y, s.text, s.role, false, s.width, true);
  });
}
/** Copied notices, host clocks, explicit dismissal and action requests. */
export class NoticeQueue {
  private source: Notice[] = [];
  private hits: FeedbackRow[] = [];
  private width = 0;
  focused = "";
  private readonly fixedCapacity: number;
  get capacity(): number {
    return this.fixedCapacity;
  }
  constructor(capacity = 10) {
    if (!Number.isInteger(capacity) || capacity < 1 || capacity > 65536)
      throw new Error("notice capacity must be 1..65536");
    this.fixedCapacity = capacity;
  }
  get items(): Notice[] {
    return clone(this.source);
  }
  private static pinned(n: Notice): boolean {
    return Boolean(n.persistent || n.severity === "error" || n.actions?.length);
  }
  private static expired(n: Notice, now: number): boolean {
    return (
      !NoticeQueue.pinned(n) &&
      (n.expiresAt ?? 0) > 0 &&
      (n.expiresAt ?? 0) <= now
    );
  }
  push(source: Notice): void {
    const n: Notice = {
        ...source,
        actions: source.actions?.map((a) => ({ ...a })),
      },
      severity = n.severity ?? "info";
    if (!n.id || !Object.hasOwn(noticeSeverity, severity))
      throw new Error("invalid notice ID or severity");
    n.severity = severity;
    n.priority ??= 0;
    n.expiresAt ??= 0;
    n.actions ??= [];
    n.text ??= "";
    n.detail ??= "";
    if (
      !Number.isInteger(n.priority) ||
      n.priority < -(2 ** 31) ||
      n.priority >= 2 ** 31
    )
      throw new Error("priority must be a signed 32-bit integer");
    feedbackNumber(n.expiresAt);
    const ids = n.actions.map((a) => a.id);
    if (
      ids.length > 1024 ||
      ids.some((id) => !id) ||
      new Set(ids).size !== ids.length
    )
      throw new Error("invalid notice actions");
    const index = this.source.findIndex((old) => old.id === n.id);
    if (index >= 0) {
      this.source[index] = n;
      this.hits = [];
      return;
    }
    if (this.source.length >= this.capacity) {
      const candidates = this.source
        .map((item, index) => ({ item, index }))
        .filter((v) => !NoticeQueue.pinned(v.item));
      candidates.sort(
        (a, b) =>
          noticeSeverity[a.item.severity ?? "info"] -
            noticeSeverity[b.item.severity ?? "info"] ||
          (a.item.priority ?? 0) - (b.item.priority ?? 0),
      );
      const candidate = candidates[0];
      if (!candidate)
        throw new Error("notice queue full; important notices retained");
      const old = candidate.item;
      if (
        noticeSeverity[old.severity ?? "info"] > noticeSeverity[severity] ||
        (noticeSeverity[old.severity ?? "info"] === noticeSeverity[severity] &&
          (old.priority ?? 0) > n.priority)
      )
        throw new Error("notice queue full");
      if (this.focused === old.id) this.focused = "";
      this.source.splice(candidate.index, 1);
    }
    if (!this.focused || severity === "error") this.focused = n.id;
    this.source.push(n);
    this.hits = [];
  }
  visible(now = 0): Notice[] {
    feedbackNumber(now);
    return clone(this.source.filter((n) => !NoticeQueue.expired(n, now))).sort(
      (a, b) =>
        noticeSeverity[b.severity ?? "info"] -
          noticeSeverity[a.severity ?? "info"] ||
        (b.priority ?? 0) - (a.priority ?? 0),
    );
  }
  dismiss(id: string): boolean {
    const index = this.source.findIndex((n) => n.id === id);
    if (index < 0) return false;
    this.source.splice(index, 1);
    if (this.focused === id) this.focused = "";
    this.hits = [];
    return true;
  }
  expire(now: number): NoticeEvent[] {
    feedbackNumber(now);
    const events = this.source
      .filter((n) => NoticeQueue.expired(n, now))
      .map((n) => feedbackEvent("expired", n.id));
    for (const e of events) this.dismiss(e.id);
    return events;
  }
  private static limit(count: number, height: number): number {
    height = Math.max(0, Math.min(4096, height));
    return count > height && height > 0 ? Math.max(1, height - 1) : height;
  }
  requestAction(id: string, action: string, now = 0): NoticeEvent {
    for (const n of this.visible(now))
      if (n.id === id && n.actions?.some((a) => a.id === action && !a.disabled))
        return feedbackEvent("action", id, action);
    return feedbackEvent();
  }
  handle(action: string, now = 0, height = 10): NoticeEvent {
    action =
      ({ down: "next", up: "previous" } as Dict<string, string>)[action] ??
      action;
    const source = this.visible(now),
      items = source.slice(0, NoticeQueue.limit(source.length, height));
    if (
      !items.length ||
      !["next", "previous", "activate", "dismiss"].includes(action)
    )
      return feedbackEvent();
    let at = Math.max(
      0,
      items.findIndex((n) => n.id === this.focused),
    );
    if (action === "next") at = Math.min(at + 1, items.length - 1);
    else if (action === "previous") at = Math.max(0, at - 1);
    const n = items[at];
    this.focused = n.id;
    if (action === "dismiss") return feedbackEvent("dismiss", n.id);
    if (action === "activate") {
      const a = n.actions?.find((a) => !a.disabled);
      if (a) return feedbackEvent("action", n.id, a.id);
    }
    return feedbackEvent();
  }
  layout(width: number, height: number, now = 0): FeedbackRow[] {
    this.width = width = Math.max(0, Math.min(65535, width));
    height = Math.max(0, Math.min(4096, height));
    const items = this.visible(now),
      limit = NoticeQueue.limit(items.length, height),
      rows: FeedbackRow[] = [];
    for (const n of items.slice(0, limit)) {
      const role = n.severity ?? "info",
        mark = (
          {
            error: "[!]",
            warning: "[?]",
            success: "[+]",
            info: "[i]",
          } as Dict<string, string>
        )[role];
      let value =
        (this.focused === n.id ? "> " : "  ") +
        mark +
        " " +
        clean(n.text ?? "");
      if (n.detail) value += " / " + clean(n.detail);
      const parts: { start: number; part: string; action: NoticeAction }[] = [];
      for (const a of n.actions ?? []) {
        const part = " [" + clean(a.label ?? "") + "]";
        parts.push({ start: cells(value), part, action: a });
        value += part;
      }
      const end = cells(value) > width ? Math.max(0, width - 1) : width,
        spans: FeedbackSpan[] = [];
      for (const { start, part, action: a } of parts) {
        const text = clip(part, Math.max(0, end - start)),
          size = cells(text);
        if (size)
          spans.push({
            start,
            width: size,
            text,
            role: a.disabled ? "disabled" : role,
            action: a.id,
            disabled: Boolean(a.disabled),
          });
      }
      rows.push(
        feedbackRow(
          n.id,
          clip(value, width, true),
          role,
          n.id === this.focused,
          spans,
        ),
      );
    }
    if (items.length > limit && height > rows.length)
      rows.push(
        feedbackRow(
          "",
          clip("+" + (items.length - limit), width, true),
          "hint",
        ),
      );
    this.hits = rows;
    return clone(rows);
  }
  click(x: number, y: number, now = 0): NoticeEvent {
    feedbackNumber(now);
    if (
      !Number.isInteger(x) ||
      x < 0 ||
      x >= this.width ||
      y < 0 ||
      y >= this.hits.length ||
      !Number.isInteger(y)
    )
      return feedbackEvent();
    const row = this.hits[y];
    if (!row.id || !this.visible(now).some((n) => n.id === row.id))
      return feedbackEvent();
    for (const s of row.spans)
      if (x >= s.start && x < s.start + s.width) {
        if (s.disabled) return feedbackEvent();
        this.focused = row.id;
        return this.requestAction(row.id, s.action, now);
      }
    this.focused = row.id;
    return feedbackEvent("focus", row.id);
  }
  draw(c: Canvas, r: Rect, now = 0): void {
    feedbackDraw(c, r, this.layout(r.width, r.height, now));
  }
}
export interface ProgressOptions {
  id?: string;
  label?: string;
  status?: string;
  message?: string;
  cancelLabel?: string;
  current?: number;
  total?: number;
  cancellable?: boolean;
}
export class Progress {
  id = "";
  label = "";
  status = "loading";
  message = "";
  cancelLabel = "";
  current = 0;
  total = 0;
  cancellable = false;
  constructor(options: ProgressOptions = {}) {
    Object.assign(this, options);
  }
  requestCancel(): NoticeEvent {
    return this.id && this.cancellable && ["", "loading"].includes(this.status)
      ? feedbackEvent("cancel", this.id)
      : feedbackEvent();
  }
  layout(width: number, frame = 0): FeedbackRow[] {
    feedbackNumber(this.current);
    feedbackNumber(this.total);
    feedbackNumber(frame);
    width = Math.max(0, Math.min(65535, width));
    const status = this.status || "loading",
      role =
        (
          {
            error: "error",
            success: "success",
            empty: "hint",
            cancelled: "hint",
            ready: "body",
            loading: "info",
          } as Dict<string, string>
        )[status] ?? "error";
    let value = status;
    if (status === "loading") {
      if (this.total === 0) value = "|/-\\"[frame % 4];
      else {
        const ratio = Math.min(this.current, this.total) / this.total,
          size = Math.min(30, Math.max(0, width - 10)),
          done = Math.floor(ratio * size);
        value =
          "[" +
          "#".repeat(done) +
          "-".repeat(size - done) +
          "] " +
          Math.floor(ratio * 100) +
          "%";
      }
    }
    if (this.message) value += " " + this.message;
    const rows = [
      feedbackRow(this.id, clip(this.label, width, true), role),
      feedbackRow(this.id, clip(value, width, true), role),
    ];
    if (this.requestCancel().kind && this.cancelLabel)
      rows.push(
        feedbackRow(this.id, clip(this.cancelLabel, width, true), "hint"),
      );
    return rows;
  }
  draw(c: Canvas, r: Rect, frame = 0): void {
    feedbackDraw(c, r, this.layout(r.width, frame));
  }
}
export class DataState {
  constructor(
    public kind = "empty",
    public text = "",
    public detail = "",
  ) {}
  layout(width: number): FeedbackRow[] {
    width = Math.max(0, Math.min(65535, width));
    return [
      feedbackRow(
        "",
        clip(this.text, width, true),
        (
          { ready: "body", loading: "info", empty: "hint" } as Dict<
            string,
            string
          >
        )[this.kind] ?? "error",
      ),
      feedbackRow("", clip(this.detail, width, true), "hint"),
    ];
  }
  draw(c: Canvas, r: Rect): void {
    feedbackDraw(c, r, this.layout(r.width));
  }
}

export function popupPlacement(
  anchor: Rect,
  viewport: Rect,
  width: number,
  height: number,
  shadow = false,
): { card: Rect; bounds: Rect } {
  if (Math.min(width, height, viewport.width, viewport.height) < 0)
    throw new Error("negative popup size");
  const w = Math.min(viewport.width, width + Number(shadow)),
    h = Math.min(viewport.height, height + Number(shadow)),
    x = Math.max(
      viewport.x,
      Math.min(viewport.x + viewport.width - w, anchor.x),
    );
  let y = anchor.y + anchor.height;
  if (y + h > viewport.y + viewport.height) y = anchor.y - h;
  y = Math.max(viewport.y, Math.min(viewport.y + viewport.height - h, y));
  return {
    card: rect(
      x,
      y,
      Math.max(0, w - Number(shadow && w > 0)),
      Math.max(0, h - Number(shadow && h > 0)),
    ),
    bounds: rect(x, y, w, h),
  };
}
export class Drag {
  source = "";
  target = "";
  active = false;
  private x = 0;
  private y = 0;
  constructor(public enabled = false) {}
  begin(id: string, x: number, y: number): boolean {
    if (!this.enabled || !id) return false;
    this.source = id;
    this.target = "";
    this.x = x;
    this.y = y;
    this.active = false;
    return true;
  }
  move(target: string, x: number, y: number, allowed = true): void {
    if (!this.source) return;
    this.active ||= Math.abs(x - this.x) + Math.abs(y - this.y) >= 2;
    this.target = allowed && target !== this.source ? target : "";
  }
  cancel(): Event {
    this.source = this.target = "";
    this.active = false;
    return event("drag_cancel");
  }
  drop(): Event {
    const e =
      this.active && this.target
        ? event("drop", this.source, "", { target: this.target })
        : event();
    this.cancel();
    return e;
  }
}

export function fold(text: string): string {
  const mapping = foldData.mappings as Dict<string, string>;
  return [...text].map((c) => mapping[String(c.codePointAt(0))] ?? c).join("");
}
