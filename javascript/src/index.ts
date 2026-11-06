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
export class List {
  items: Item[];
  focused = "";
  selected = "";
  query = "";
  scroll = 0;
  constructor(items: Item[]) {
    unique(items);
    this.items = clone(items);
    this.eligible();
  }
  visible(): Item[] {
    return this.items.filter(
      (i) =>
        !this.query ||
        `${i.label ?? ""} ${i.secondary ?? ""}`
          .toLocaleLowerCase()
          .includes(this.query.toLocaleLowerCase()),
    );
  }
  private eligible(): Item[] {
    const items = this.visible().filter((i) => !i.disabled && !i.separator);
    if (!items.some((i) => i.id === this.focused))
      this.focused = items[0]?.id ?? "";
    return items;
  }
  handle(action: string, height = 10, text = ""): Event {
    if (action === "query") {
      this.query = text;
      this.eligible();
      return event("query", "", text);
    }
    const items = this.eligible();
    if (!items.length) return event();
    const i = items.findIndex((t) => t.id === this.focused);
    if (action === "activate") {
      this.selected = this.focused;
      return event("activate", this.focused);
    }
    const moves: Dict<string, number> = {
      up: i - 1,
      down: i + 1,
      home: 0,
      end: items.length - 1,
      page_up: i - Math.max(1, height),
      page_down: i + Math.max(1, height),
    };
    const target = Math.max(0, Math.min(items.length - 1, moves[action] ?? i));
    if (target !== i) {
      this.focused = items[target].id;
      return event("focus", this.focused);
    }
    return event();
  }
  click(x: number, y: number, height = 10): Event {
    const item = this.visible()[this.scroll + y];
    if (y < 0 || y >= height || !item || item.disabled || item.separator)
      return event();
    this.focused = this.selected = item.id;
    return event("activate", item.id);
  }
  draw(c: Canvas, r: Rect, focused = true, ascii = false): void {
    c.fill(r);
    this.eligible();
    const rows = this.visible(),
      i = Math.max(
        0,
        rows.findIndex((t) => t.id === this.focused),
      ),
      h = Math.max(1, r.height);
    this.scroll = Math.max(0, Math.min(this.scroll, rows.length - h));
    if (i < this.scroll) this.scroll = i;
    if (i >= this.scroll + h) this.scroll = i - h + 1;
    rows.slice(this.scroll, this.scroll + r.height).forEach((item, y) => {
      const current = item.id === this.focused,
        icon = ascii ? item.ascii_icon : item.icon;
      const text = item.separator
        ? (ascii ? "-" : "─").repeat(r.width)
        : (current ? "> " : "  ") +
          (icon ? icon + " " : "") +
          (item.label ?? "") +
          (item.secondary ? "  " + item.secondary : "") +
          (item.shortcut ? "  " + item.shortcut : "");
      c.write(
        r.x,
        r.y + y,
        clip(text, r.width, true),
        item.disabled ? "disabled" : current ? "selection" : "body",
        focused && current,
        r.width,
      );
    });
  }
}
export class Text {
  value: string;
  cursor: number;
  anchor: number;
  readOnly: boolean;
  secret: boolean;
  multiline: boolean;
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
  select(anchor: number, cursor: number): void {
    const n = graphemes(this.value).length;
    this.anchor = Math.max(0, Math.min(n, anchor));
    this.cursor = Math.max(0, Math.min(n, cursor));
  }
  private replace(text: string): void {
    if (this.readOnly) return;
    this.undoStack.push([this.value, this.cursor, this.anchor]);
    this.undoStack = this.undoStack.slice(-100);
    this.redoStack = [];
    const parts = graphemes(this.value),
      a = Math.min(this.cursor, this.anchor),
      b = Math.max(this.cursor, this.anchor);
    if (!this.multiline) text = text.replace(/\r\n|\r|\n/g, " ");
    this.value = parts.slice(0, a).join("") + text + parts.slice(b).join("");
    this.cursor = this.anchor = a + graphemes(text).length;
  }
  handle(action: string, text = ""): Event {
    const parts = graphemes(this.value);
    if (action === "select_all") this.select(0, parts.length);
    else if (action === "copy" || action === "cut") {
      const a = Math.min(this.cursor, this.anchor),
        b = Math.max(this.cursor, this.anchor),
        e = event("copy", "", this.secret ? "" : parts.slice(a, b).join(""));
      if (action === "cut" && !this.secret) this.replace("");
      return e;
    } else if (["undo", "redo"].includes(action) && !this.readOnly) {
      const [src, dst] =
        action === "undo"
          ? [this.undoStack, this.redoStack]
          : [this.redoStack, this.undoStack];
      const previous = src.pop();
      if (previous) {
        dst.push([this.value, this.cursor, this.anchor]);
        [this.value, this.cursor, this.anchor] = previous;
      }
    } else if (["left", "right", "home", "end"].includes(action)) {
      const target = (
        {
          left: this.cursor - 1,
          right: this.cursor + 1,
          home: 0,
          end: parts.length,
        } as Dict<string, number>
      )[action];
      this.select(target, target);
    } else if (action === "backspace" || action === "delete") {
      if (this.anchor === this.cursor)
        this.select(
          action === "backspace" ? this.cursor - 1 : this.cursor,
          action === "backspace" ? this.cursor : this.cursor + 1,
        );
      this.replace("");
    } else if (action === "insert" || action === "paste") this.replace(text);
    else if (action === "newline" && this.multiline) this.replace("\n");
    return event("change", "", this.secret ? "" : this.value);
  }
  window(width: number): { text: string; x: number; glyphWidth: number } {
    let parts = graphemes(this.value);
    if (this.secret) parts = parts.map(() => "*");
    const cursor = Math.min(parts.length, Math.max(0, this.cursor)),
      glyphWidth =
        cursor < parts.length ? Math.max(1, cells(parts[cursor])) : 1;
    let start = 0;
    while (
      start < cursor &&
      cells(parts.slice(start, cursor).join("")) + glyphWidth > width
    )
      start++;
    if (glyphWidth > width) return { text: "", x: 0, glyphWidth: 1 };
    return {
      text: clip(parts.slice(start).join(""), width),
      x: cells(parts.slice(start, cursor).join("")),
      glyphWidth,
    };
  }
  draw(c: Canvas, r: Rect, focused = true): void {
    c.fill(r, this.readOnly ? "surface" : "field");
    if (r.width <= 0 || r.height <= 0) return;
    if (!this.multiline) {
      const p = this.window(r.width);
      c.write(r.x, r.y, p.text, "field", false, r.width, true);
      if (focused && !this.readOnly) c.setCursor(r.x + p.x, r.y, p.glyphWidth);
      return;
    }
    const before = graphemes(this.value).slice(0, this.cursor).join(""),
      cy = before.split("\n").length - 1,
      cx = cells(before.split("\n").at(-1) ?? ""),
      sy = Math.max(0, cy - r.height + 1),
      sx = Math.max(0, cx - r.width + 1);
    this.value
      .split("\n")
      .slice(sy, sy + r.height)
      .forEach((text, y) =>
        c.write(
          r.x - sx,
          r.y + y,
          this.secret ? "*".repeat(graphemes(text).length) : text,
          this.readOnly ? "body" : "field",
          false,
          r.width + sx,
          true,
        ),
      );
    if (focused && !this.readOnly) c.setCursor(r.x + cx - sx, r.y + cy - sy);
  }
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
  options?: { id: string; label: string; disabled?: boolean }[];
  state?: Partial<ControlState>;
  error?: string;
}
export class Form {
  readonly fields: Field[];
  readonly inputs = new Map<string, Text>();
  focused = "";
  scroll = 0;
  constructor(fields: Field[]) {
    unique(fields);
    this.fields = clone(fields);
    for (const f of this.fields) {
      f.kind ??= "text";
      f.state = new ControlState(f.state);
      if (["text", "textarea", "password"].includes(f.kind))
        this.inputs.set(
          f.id,
          new Text(f.value ?? "", {
            secret: f.kind === "password",
            multiline: f.kind === "textarea",
          }),
        );
    }
    this.eligible();
  }
  private eligible(): Field[] {
    const items = this.fields.filter((f) => !f.state?.disabled);
    if (!items.some((f) => f.id === this.focused))
      this.focused = items[0]?.id ?? "";
    return items;
  }
  value(id: string): string {
    const f = this.fields.find((f) => f.id === id);
    if (!f) throw new Error("unknown field");
    return this.inputs.get(id)?.value ?? f.value ?? "";
  }
  handle(action: string, text = ""): Event {
    const items = this.eligible();
    if (action === "cancel") return event("cancel");
    if (action === "submit") {
      const missing = this.fields
        .filter((f) => !f.state?.disabled && f.required && !this.value(f.id))
        .map((f) => f.id);
      return event(missing.length ? "invalid" : "submit", "", "", missing);
    }
    if (!items.length) return event();
    const i = items.findIndex((f) => f.id === this.focused),
      f = items[i],
      state = new ControlState(f.state);
    if (action === "next" || action === "previous") {
      this.focused =
        items[
          (i + (action === "next" ? 1 : -1) + items.length) % items.length
        ].id;
      return event("focus", this.focused);
    }
    if (!state.activatable) return event();
    if (action === "activate" && f.kind === "button")
      return event("activate", f.id);
    if (!state.editable) return event();
    const input = this.inputs.get(f.id);
    if (input) return { ...input.handle(action, text), id: f.id };
    if (
      ["checkbox", "radio"].includes(f.kind!) &&
      ["activate", "toggle"].includes(action)
    ) {
      f.checked = f.kind === "radio" || !f.checked;
      return event("change", f.id, "", f.checked);
    }
    if (
      f.kind === "select" &&
      ["activate", "left", "right", "up", "down"].includes(action)
    ) {
      const options = (f.options ?? []).filter((o) => !o.disabled);
      if (!options.length) return event();
      const at = Math.max(
        0,
        options.findIndex((o) => o.id === f.value),
      );
      f.value =
        options[
          (at + (["left", "up"].includes(action) ? -1 : 1) + options.length) %
            options.length
        ].id;
      return event("change", f.id, f.value);
    }
    return event();
  }
  click(x: number, y: number, height = 10): Event {
    const f = this.fields[this.scroll + y];
    if (y < 0 || y >= height || !f || f.state?.disabled) return event();
    this.focused = f.id;
    return ["button", "checkbox", "radio", "select"].includes(f.kind!)
      ? this.handle("activate")
      : event("focus", f.id);
  }
  draw(c: Canvas, r: Rect, focused = true): void {
    c.fill(r);
    this.eligible();
    const index = Math.max(
      0,
      this.fields.findIndex((f) => f.id === this.focused),
    );
    this.scroll = Math.max(0, Math.min(this.scroll, index));
    if (index >= this.scroll + Math.max(1, r.height))
      this.scroll = index - Math.max(1, r.height) + 1;
    this.fields.slice(this.scroll, this.scroll + r.height).forEach((f, y) => {
      const current = focused && f.id === this.focused,
        prefix = f.label ? f.label + ": " : "",
        start = Math.min(cells(prefix), r.width),
        width = r.width - start,
        role = f.state?.disabled ? "disabled" : f.error ? "error" : "body";
      c.write(r.x, r.y + y, clip(prefix, r.width), role, current, r.width);
      const input = this.inputs.get(f.id);
      if (input) {
        const p = input.window(width);
        c.write(
          r.x + start,
          r.y + y,
          p.text + " ".repeat(Math.max(0, width - cells(p.text))),
          f.state?.disabled ? "disabled" : "field",
          false,
          width,
          true,
        );
        if (current && new ControlState(f.state).editable && width)
          c.setCursor(r.x + start + p.x, r.y + y, p.glyphWidth);
      } else {
        const value = ["checkbox", "radio"].includes(f.kind!)
          ? (f.checked ? "[x] " : "[ ] ") + (f.label ?? "")
          : f.kind === "button"
            ? `[ ${f.label ?? ""} ]`
            : ((f.options ?? []).find((o) => o.id === f.value)?.label ??
              f.value ??
              "");
        c.write(
          r.x + start,
          r.y + y,
          clip(value, width, true),
          role,
          current,
          width,
        );
      }
    });
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
export class Focus {
  private scopes: {
    id: string;
    targets: FocusTarget[];
    focused: string;
    modal: boolean;
  }[] = [];
  constructor(id: string, targets: FocusTarget[]) {
    this.open(id, targets);
  }
  get focused(): string {
    return this.scopes.at(-1)!.focused;
  }
  private eligible(): string[] {
    const s = this.scopes.at(-1)!,
      ids = s.targets
        .filter((t) => !t.hidden && !t.state?.disabled)
        .map((t) => t.id);
    if (!ids.includes(s.focused)) s.focused = ids[0] ?? "";
    return ids;
  }
  open(id: string, targets: FocusTarget[], focused = "", modal = true): void {
    unique(targets);
    if (!id || this.scopes.some((s) => s.id === id))
      throw new Error("duplicate/empty scope");
    this.scopes.push({ id, targets: clone(targets), focused, modal });
    this.eligible();
  }
  close(id: string): Event {
    if (this.scopes.length <= 1 || this.scopes.at(-1)!.id !== id)
      throw new Error("only top popup can close");
    this.scopes.pop();
    this.eligible();
    return event("focus", this.focused);
  }
  focus(id: string): boolean {
    if (!this.eligible().includes(id)) return false;
    this.scopes.at(-1)!.focused = id;
    return true;
  }
  move(previous = false): string {
    const ids = this.eligible();
    if (ids.length)
      this.scopes.at(-1)!.focused =
        ids[
          (ids.indexOf(this.focused) + (previous ? -1 : 1) + ids.length) %
            ids.length
        ];
    return this.focused;
  }
  blocked(scope: string): boolean {
    const i = this.scopes.findIndex((s) => s.id === scope);
    return i < 0 || this.scopes.slice(i + 1).some((s) => s.modal);
  }
}
export class Menu {
  readonly items: Item[];
  path: string[] = [];
  opened = false;
  returnId = "";
  level = new List([]);
  constructor(items: Item[]) {
    unique(items);
    this.items = clone(items);
    const byId = new Map(items.map((i) => [i.id, i]));
    for (const item of items) {
      const seen = new Set([item.id]);
      let parent = item.parent;
      while (parent) {
        if (!byId.has(parent) || seen.has(parent))
          throw new Error("invalid menu hierarchy");
        seen.add(parent);
        parent = byId.get(parent)!.parent;
      }
    }
  }
  private update(): void {
    const old = this.level.focused;
    this.level = new List(
      this.items.filter((i) => (i.parent ?? "") === (this.path.at(-1) ?? "")),
    );
    if (
      this.level.items.some((i) => i.id === old && !i.disabled && !i.separator)
    )
      this.level.focused = old;
  }
  open(id = "", returnId = ""): Event {
    const item = this.items.find((i) => i.id === id);
    if (id && (!item || item.disabled || item.separator)) return event();
    this.path = id ? [id] : [];
    this.returnId = returnId;
    this.opened = true;
    this.update();
    return event("open", id);
  }
  handle(action: string, height = 10, text = ""): Event {
    if (!this.opened) return event();
    if (action === "cancel" || action === "close") {
      this.opened = false;
      return event("close", this.returnId);
    }
    if (action === "left" || action === "back") {
      if (this.path.length) {
        this.path.pop();
        this.update();
        return event("back", this.path.at(-1) ?? "");
      }
      return this.handle("close");
    }
    if (action === "activate" || action === "right") {
      const item = this.level.items.find((i) => i.id === this.level.focused);
      if (!item || item.disabled || item.separator) return event();
      if (this.items.some((i) => i.parent === item.id)) {
        this.path.push(item.id);
        this.update();
        return event("open", item.id);
      }
      if (action === "activate") {
        this.opened = false;
        return event("activate", item.id, "", { return_id: this.returnId });
      }
      return event();
    }
    return this.level.handle(action, height, text);
  }
  click(x: number, y: number, height = 10): Event {
    if (!this.opened) return event();
    const e = this.level.click(x, y, height);
    return e.kind ? this.handle("activate", height) : event();
  }
  draw(c: Canvas, r: Rect, focused = true, ascii = false): void {
    if (this.opened) this.level.draw(c, r, false, ascii);
  }
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
export interface Notice {
  id: string;
  text: string;
  severity?: "info" | "success" | "warning" | "error";
  priority?: number;
  expiresAt?: number;
  persistent?: boolean;
}
export class Notices {
  items: Notice[] = [];
  constructor(readonly capacity = 10) {
    if (capacity < 1) throw new Error("positive capacity required");
  }
  push(n: Notice): void {
    if (
      !n.id ||
      !["info", "success", "warning", "error"].includes(n.severity ?? "info")
    )
      throw new Error("invalid notice");
    this.items = [...this.items.filter((i) => i.id !== n.id), clone(n)]
      .sort(
        (a, b) =>
          (b.priority ?? 0) - (a.priority ?? 0) ||
          Number(b.severity === "error") - Number(a.severity === "error"),
      )
      .slice(0, this.capacity);
  }
  visible(now: number): Notice[] {
    return this.items.filter(
      (i) =>
        i.persistent ||
        i.severity === "error" ||
        !i.expiresAt ||
        i.expiresAt > now,
    );
  }
  dismiss(id: string): Event {
    this.items = this.items.filter((i) => i.id !== id);
    return event("dismiss", id);
  }
  draw(c: Canvas, r: Rect, now = 0): void {
    c.fill(r);
    this.visible(now)
      .slice(0, r.height)
      .forEach((n, y) =>
        c.write(
          r.x,
          r.y + y,
          clip(n.text, r.width, true),
          n.severity ?? "info",
          false,
          r.width,
        ),
      );
  }
}
export class Progress {
  constructor(
    public value = 0,
    public total = 0,
    public label = "",
    public cancellable = false,
  ) {}
  cancel(): Event {
    return this.cancellable ? event("cancel") : event();
  }
  draw(c: Canvas, r: Rect, frame = 0): void {
    const fraction =
        this.total > 0 ? Math.max(0, Math.min(1, this.value / this.total)) : 0,
      text =
        this.total > 0
          ? `${this.label} ${Math.floor(fraction * 100)}%`
          : `${this.label} ${"|/-"[frame % 3]}`;
    c.write(r.x, r.y, clip(text, r.width, true), "info", false, r.width);
  }
}
export class DataState {
  constructor(
    public status = "empty",
    public message = "",
  ) {}
  draw(c: Canvas, r: Rect): void {
    c.write(
      r.x,
      r.y,
      clip(this.message || this.status, r.width, true),
      this.status === "error" ? "error" : "hint",
      false,
      r.width,
    );
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
