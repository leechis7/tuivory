import { colorContrast } from "./colors.js";
/** Independent request-only movement. Hosts approve immutable replacements. */
import { Tree, Tabs, Canvas, rect, cells, graphemes, clip } from "./index.js";
import type { Node as TreeNode, Tab, TabCell, Rect, Style } from "./index.js";
export class DropError extends Error {
  constructor(readonly reason: string) {
    super(reason);
  }
}
export interface DropRequest {
  readonly sourceId: string;
  readonly targetId: string;
  readonly position: string;
  readonly revision: string;
}
export class DragOptions {
  threshold = 0;
  autoScroll = false;
  hoverExpand = false;
  locked: string[] = [];
  constructor(options: Partial<DragOptions> = {}) {
    Object.assign(this, options);
    this.locked = [...(options.locked ?? [])];
  }
}
export interface DragPointer {
  action: string;
  x: number;
  y: number;
  width: number;
  height: number;
}
export interface DragLayout {
  readonly first: number;
  readonly scroll: number;
  readonly expanded: readonly string[];
  readonly tabs: readonly TabCell[];
  readonly rows: readonly TreeNode[];
}
function options(value?: DragOptions): DragOptions {
  const o = new DragOptions(value);
  if (
    !Number.isInteger(o.threshold) ||
    o.threshold < 0 ||
    o.threshold > 1000000 ||
    o.locked.length > 65536 ||
    o.locked.some((id) => typeof id !== "string" || !id)
  )
    throw new DropError("options");
  return o;
}
function utf8(text: string, visit: (byte: number) => void): void {
  for (const c of text) {
    const p = c.codePointAt(0)!;
    if (p >= 0xd800 && p <= 0xdfff) throw new DropError("text");
    if (p < 128) visit(p);
    else if (p < 2048) {
      visit(0xc0 | (p >> 6));
      visit(0x80 | (p & 63));
    } else if (p < 65536) {
      visit(0xe0 | (p >> 12));
      visit(0x80 | ((p >> 6) & 63));
      visit(0x80 | (p & 63));
    } else {
      visit(0xf0 | (p >> 18));
      visit(0x80 | ((p >> 12) & 63));
      visit(0x80 | ((p >> 6) & 63));
      visit(0x80 | (p & 63));
    }
  }
}
function revision(parts: string[]): string {
  let hash = 14695981039346656037n;
  const update = (b: number) => {
    hash = BigInt.asUintN(64, (hash ^ BigInt(b)) * 1099511628211n);
  };
  for (const s of parts) {
    let size = 0;
    utf8(s, () => size++);
    utf8(String(size) + ":", update);
    utf8(s, update);
  }
  return hash.toString(16).padStart(16, "0");
}
const nodes = (model: Tree): TreeNode[] =>
  model.nodes.map((n) => ({ ...n, branch: model.branches.has(n.id) }));
export function dragRevision(model: Tree | Tabs): string {
  const parts: string[] = [];
  if (model instanceof Tabs)
    for (const t of model.items)
      parts.push(
        t.id,
        t.title ?? "",
        String(!!t.edited),
        String(!!t.closable),
        String(!!t.disabled),
      );
  else if (model instanceof Tree)
    for (const n of nodes(model))
      parts.push(
        n.id,
        n.parent ?? "",
        n.name ?? "",
        n.secondary ?? "",
        n.icon ?? "",
        n.ascii_icon ?? "",
        n.count === undefined ? "" : String(n.count),
        String(!!n.branch),
      );
  else throw new DropError("model");
  return revision(parts);
}
function stateRevision(model: Tree | Tabs): string {
  return model instanceof Tabs
    ? revision([model.active, model.focused, String(model.first)])
    : revision([
        model.selected,
        String(model.scroll),
        String(model.horizontal),
        ...[...model.expanded].sort(),
      ]);
}
function copyState(model: Tabs, next: Tabs): Tabs;
function copyState(model: Tree, next: Tree): Tree;
function copyState(model: Tabs | Tree, next: Tabs | Tree): Tabs | Tree {
  if (model instanceof Tabs && next instanceof Tabs) {
    next.active = model.active;
    next.focused = model.focused;
    next.first = model.first;
    next.handle("");
    return next;
  }
  if (model instanceof Tree && next instanceof Tree) {
    next.selected = model.selected;
    next.scroll = model.scroll;
    next.horizontal = model.horizontal;
    next.expanded = new Set(
      [...model.expanded].filter((id) => next.byId.has(id)),
    );
    return next;
  }
  throw new DropError("model");
}
export function applyDrop(model: Tabs, request: DropRequest): Tabs;
export function applyDrop(model: Tree, request: DropRequest): Tree;
export function applyDrop(
  model: Tabs | Tree,
  request: DropRequest,
): Tabs | Tree {
  if (request.revision !== dragRevision(model)) throw new DropError("stale");
  const source = request.sourceId,
    target = request.targetId,
    position = request.position;
  if (model instanceof Tabs) {
    if (source === target) throw new DropError("self");
    if (!["before", "after"].includes(position))
      throw new DropError("position");
    const items = model.items.map((t) => ({ ...t })),
      si = items.findIndex((t) => t.id === source);
    let ti = items.findIndex((t) => t.id === target);
    if (si < 0 || ti < 0) throw new DropError("missing");
    if (items[si].disabled || items[ti].disabled)
      throw new DropError("disabled");
    const [item] = items.splice(si, 1);
    if (si < ti) ti--;
    if (position === "after") ti++;
    if (si === ti) throw new DropError("unchanged");
    items.splice(ti, 0, item);
    return copyState(model, new Tabs(items));
  }
  const all = nodes(model),
    index = new Map(all.map((n, i) => [n.id, i])),
    si = index.get(source),
    ti = index.get(target);
  if (si === undefined || ti === undefined) throw new DropError("missing");
  if (source === target) throw new DropError("self");
  if (!["before", "after", "inside"].includes(position))
    throw new DropError("position");
  let parent = target;
  while (parent) {
    if (parent === source) throw new DropError("cycle");
    parent = all[index.get(parent)!].parent ?? "";
  }
  if (position === "inside" && !all[ti].branch) throw new DropError("leaf");
  let end = si + 1;
  while (
    end < all.length &&
    model.depth.get(all[end].id)! > model.depth.get(source)!
  )
    end++;
  const newDepth = model.depth.get(target)! + Number(position === "inside"),
    extra = all
      .slice(si, end)
      .reduce(
        (depth, node) =>
          Math.max(depth, model.depth.get(node.id)! - model.depth.get(source)!),
        0,
      );
  if (newDepth + extra > 128) throw new DropError("depth");
  const block = all.slice(si, end),
    remaining = [...all.slice(0, si), ...all.slice(end)];
  let at = remaining.findIndex((n) => n.id === target);
  parent = position === "inside" ? target : (remaining[at].parent ?? "");
  if (position !== "before") {
    at++;
    while (
      at < remaining.length &&
      model.depth.get(remaining[at].id)! > model.depth.get(target)!
    )
      at++;
  }
  block[0] = { ...block[0], parent };
  const reordered = [
    ...remaining.slice(0, at),
    ...block,
    ...remaining.slice(at),
  ];
  if (
    reordered.every(
      (n, i) =>
        n.id === all[i].id && (n.parent ?? "") === (all[i].parent ?? ""),
    )
  )
    throw new DropError("unchanged");
  return copyState(model, new Tree(reordered));
}
export type DropPolicy = (request: DropRequest) => boolean;
export function requestDrop(
  model: Tree | Tabs,
  sourceId: string,
  targetId: string,
  position: string,
  value?: DragOptions,
  allow?: DropPolicy,
): DropRequest {
  const o = options(value);
  if (o.locked.includes(sourceId) || o.locked.includes(targetId))
    throw new DropError("locked");
  const request = Object.freeze({
    sourceId,
    targetId,
    position,
    revision: dragRevision(model),
  });
  if (model instanceof Tabs) applyDrop(model, request);
  else applyDrop(model, request);
  if (allow) {
    let allowed = false;
    try {
      allowed = !!allow(request);
    } catch {
      throw new DropError("policy");
    }
    if (!allowed) throw new DropError("policy");
    if (request.revision !== dragRevision(model)) throw new DropError("stale");
  }
  return request;
}
export function keyboardDrop(
  model: Tree | Tabs,
  direction: string,
  value?: DragOptions,
  allow?: DropPolicy,
): DropRequest {
  if (model instanceof Tabs) {
    const i = model.items.findIndex((t) => t.id === model.focused);
    if (i < 0) throw new DropError("missing");
    if (!["previous", "next"].includes(direction))
      throw new DropError("position");
    const j = i + (direction === "previous" ? -1 : 1);
    if (j < 0 || j >= model.items.length) throw new DropError("missing");
    return requestDrop(
      model,
      model.focused,
      model.items[j].id,
      direction === "previous" ? "before" : "after",
      value,
      allow,
    );
  }
  const node = model.byId.get(model.selected);
  if (!node) throw new DropError("missing");
  if (direction === "outside" && node.parent)
    return requestDrop(model, node.id, node.parent, "after", value, allow);
  const siblings = model.nodes.filter(
      (n) => (n.parent ?? "") === (node.parent ?? ""),
    ),
    i = siblings.findIndex((n) => n.id === node.id);
  if (!["previous", "next", "inside"].includes(direction))
    throw new DropError("position");
  const j = i + (direction === "next" ? 1 : -1);
  if (j < 0 || j >= siblings.length) throw new DropError("missing");
  return requestDrop(
    model,
    node.id,
    siblings[j].id,
    direction === "inside"
      ? "inside"
      : direction === "next"
        ? "after"
        : "before",
    value,
    allow,
  );
}

export class DragState {
  phase = "idle";
  result = "";
  sourceId = "";
  targetId = "";
  position = "";
  allowed = false;
  reason = "";
  private renderKeyValue = "";
  private busy = false;
  private request: DropRequest | null = null;
  private revisionValue = "";
  private stateRevisionValue = "";
  private x = 0;
  private y = 0;
  private width = 0;
  private height = 0;
  private first = 0;
  private scroll = 0;
  private expanded = new Set<string>();
  private lastPointer: DragPointer = {
    action: "cancel",
    x: 0,
    y: 0,
    width: 0,
    height: 0,
  };
  constructor(public enabled = false) {}
  get captured(): boolean {
    return this.phase === "armed" || this.phase === "dragging";
  }
  private reset(result: string): void {
    this.phase = "idle";
    this.result = result;
    this.sourceId = this.targetId = this.position = this.reason = "";
    this.allowed = false;
    this.request = null;
    this.revisionValue = this.stateRevisionValue = "";
    this.x = this.y = this.width = this.height = this.first = this.scroll = 0;
    this.expanded = new Set();
    this.lastPointer = { action: "cancel", x: 0, y: 0, width: 0, height: 0 };
  }
  cancel(): void {
    if (this.busy) throw new DropError("reentrant");
    this.reset("cancel");
  }
  renderKey(key: string): void {
    if (this.busy) throw new DropError("reentrant");
    if (typeof key !== "string") throw new DropError("render_key");
    if (this.captured && this.renderKeyValue && key !== this.renderKeyValue)
      this.reset("stale");
    this.renderKeyValue = key;
  }
  private valid(model: Tree | Tabs, width: number, height: number): boolean {
    if (!this.captured) return false;
    if (!this.enabled) {
      this.reset("cancel");
      return false;
    }
    if (
      this.revisionValue !== dragRevision(model) ||
      this.stateRevisionValue !== stateRevision(model) ||
      this.width !== width ||
      this.height !== height
    ) {
      this.reset("stale");
      return false;
    }
    return true;
  }
  private tabCells(model: Tabs, width: number, first: number): TabCell[] {
    const result: TabCell[] = [];
    let x = 1;
    if (width <= 2) return result;
    for (const item of model.items.slice(first)) {
      if (x >= width - 1) break;
      const w = Math.min(
        Math.max(6, Math.min(24, cells(item.title ?? "") + 5)),
        width - 1 - x,
      );
      if (w < 4 && result.length) break;
      const active = item.id === model.active,
        focused = item.id === model.focused,
        suffix = (item.edited ? " *" : "") + (item.closable ? " x" : ""),
        label = clip(
          item.title ?? "",
          Math.max(0, w - 3 - suffix.length),
          true,
        ),
        text = clip(
          (focused ? ">" : " ") +
            (active ? "[" : " ") +
            label +
            suffix +
            (active ? "]" : " "),
          w,
          true,
        );
      result.push({
        id: item.id,
        text,
        start: x,
        width: w,
        active,
        focused,
        disabled: !!item.disabled,
      });
      x += w;
    }
    return result;
  }
  private treeRows(model: Tree, height: number): TreeNode[] {
    const preview = new Tree(nodes(model));
    copyState(model, preview);
    preview.expanded = new Set(this.expanded);
    const rows = preview.visible();
    this.scroll = Math.max(
      0,
      Math.min(this.scroll, Math.max(0, rows.length - Math.max(1, height))),
    );
    return rows;
  }
  previewLayout(model: Tree | Tabs, width: number, height: number): DragLayout {
    if (this.busy) throw new DropError("reentrant");
    if (
      !Number.isInteger(width) ||
      !Number.isInteger(height) ||
      width < 0 ||
      width > 65535 ||
      height < 0 ||
      height > 4096
    )
      throw new DropError("bounds");
    if (!this.valid(model, width, height)) {
      if (model instanceof Tabs) {
        const preview = copyState(model, new Tabs(model.items)),
          tabs = preview.layout(width);
        return Object.freeze({
          first: preview.first,
          scroll: 0,
          expanded: Object.freeze([]),
          tabs: Object.freeze(tabs.map((c) => Object.freeze({ ...c }))),
          rows: Object.freeze([]),
        });
      }
      const preview = copyState(model, new Tree(nodes(model)));
      preview.handle("", height);
      return Object.freeze({
        first: 0,
        scroll: preview.scroll,
        expanded: Object.freeze([...preview.expanded].sort()),
        tabs: Object.freeze([]),
        rows: Object.freeze(preview.visible()),
      });
    }
    if (model instanceof Tabs)
      return Object.freeze({
        first: this.first,
        scroll: 0,
        expanded: Object.freeze([]),
        tabs: Object.freeze(
          this.tabCells(model, width, this.first).map((c) => Object.freeze(c)),
        ),
        rows: Object.freeze([]),
      });
    const rows = this.treeRows(model, height);
    return Object.freeze({
      first: 0,
      scroll: this.scroll,
      expanded: Object.freeze([...this.expanded].sort()),
      tabs: Object.freeze([]),
      rows: Object.freeze(rows),
    });
  }
  pointer(
    model: Tree | Tabs,
    pointer: DragPointer,
    value?: DragOptions,
    allow?: DropPolicy,
  ): DropRequest | null {
    if (this.busy) throw new DropError("reentrant");
    const p = { ...pointer },
      o = options(value);
    if (
      !["down", "move", "up", "cancel"].includes(p.action) ||
      ![p.x, p.y].every(
        (v) => Number.isInteger(v) && Math.abs(v) <= 1000000000,
      ) ||
      !Number.isInteger(p.width) ||
      !Number.isInteger(p.height) ||
      p.width < 0 ||
      p.width > 65535 ||
      p.height < 0 ||
      p.height > 4096
    )
      throw new DropError("pointer");
    if (p.action === "cancel") {
      this.cancel();
      return null;
    }
    if (!this.enabled) {
      if (this.captured) this.reset("cancel");
      return null;
    }
    if (p.action === "down") {
      this.reset("");
      if (p.x < 0 || p.x >= p.width || p.y < 0 || p.y >= p.height) return null;
      let id = "",
        first = 0,
        scroll = 0,
        expanded = new Set<string>();
      if (model instanceof Tabs) {
        if (p.y) return null;
        const preview = copyState(model, new Tabs(model.items)),
          target = preview
            .layout(p.width)
            .find(
              (c) => c.start <= p.x && p.x < c.start + c.width && !c.disabled,
            );
        id = target?.id ?? "";
        first = preview.first;
      } else {
        const preview = copyState(model, new Tree(nodes(model)));
        preview.handle("", p.height);
        const rows = preview.visible(),
          i = preview.scroll + p.y;
        id = rows[i]?.id ?? "";
        scroll = preview.scroll;
        expanded = new Set(preview.expanded);
      }
      if (!id || o.locked.includes(id)) return null;
      this.phase = "armed";
      this.sourceId = id;
      this.revisionValue = dragRevision(model);
      this.stateRevisionValue = stateRevision(model);
      this.x = p.x;
      this.y = p.y;
      this.width = p.width;
      this.height = p.height;
      this.first = first;
      this.scroll = scroll;
      this.expanded = expanded;
      this.lastPointer = p;
      return null;
    }
    if (!this.valid(model, p.width, p.height)) return null;
    this.lastPointer = p;
    if (
      Math.max(Math.abs(p.x - this.x), Math.abs(p.y - this.y)) >=
      (o.threshold || 2)
    )
      this.phase = "dragging";
    if (this.phase === "dragging") {
      let raw: DropRequest | null = null,
        error = "outside";
      if (model instanceof Tabs) {
        if (o.autoScroll && p.action === "move") {
          if (p.x <= 0) this.first = Math.max(0, this.first - 1);
          else if (p.x >= p.width - 1)
            this.first = Math.min(
              Math.max(0, model.items.length - 1),
              this.first + 1,
            );
        }
        const target = this.tabCells(model, p.width, this.first).find(
          (c) =>
            p.x >= 0 &&
            p.x < p.width &&
            p.y === 0 &&
            c.start <= p.x &&
            p.x < c.start + c.width,
        );
        if (target)
          raw = Object.freeze({
            sourceId: this.sourceId,
            targetId: target.id,
            position:
              p.x - target.start >= Math.floor(target.width / 2)
                ? "after"
                : "before",
            revision: this.revisionValue,
          });
      } else {
        const rows = this.treeRows(model, p.height);
        if (o.autoScroll && p.action === "move") {
          if (p.y <= 0) this.scroll = Math.max(0, this.scroll - 1);
          else if (p.y >= p.height - 1)
            this.scroll = Math.min(
              Math.max(0, rows.length - Math.max(1, p.height)),
              this.scroll + 1,
            );
        }
        const i = this.scroll + p.y;
        if (
          p.x >= 0 &&
          p.x < p.width &&
          p.y >= 0 &&
          p.y < p.height &&
          i >= 0 &&
          i < rows.length
        ) {
          const target = rows[i],
            position =
              p.x <= 2 + model.depth.get(target.id)! * 2
                ? "before"
                : model.branches.has(target.id) && p.x < p.width - 2
                  ? "inside"
                  : "after";
          raw = Object.freeze({
            sourceId: this.sourceId,
            targetId: target.id,
            position,
            revision: this.revisionValue,
          });
        }
      }
      if (raw) {
        this.busy = true;
        try {
          requestDrop(
            model,
            raw.sourceId,
            raw.targetId,
            raw.position,
            o,
            allow,
          );
          error = "";
        } catch (e) {
          if (!(e instanceof DropError)) throw e;
          error = e.reason;
        } finally {
          this.busy = false;
        }
        if (!this.valid(model, p.width, p.height)) return null;
      }
      this.request = raw;
      this.targetId = raw?.targetId ?? "";
      this.position = raw?.position ?? "";
      this.allowed = !error;
      this.reason = error;
      if (
        raw &&
        !error &&
        o.hoverExpand &&
        model instanceof Tree &&
        raw.position === "inside"
      )
        this.expanded.add(raw.targetId);
    }
    if (p.action !== "up") return null;
    const request =
        this.phase === "dragging" && this.allowed ? this.request : null,
      result = request ? "drop" : this.phase === "dragging" ? "reject" : "";
    this.reset(result);
    return request;
  }
  draw(
    model: Tree | Tabs,
    canvas: Canvas,
    r: Rect,
    focused = true,
    ascii = false,
  ): void {
    if (this.busy) throw new DropError("reentrant");
    if (
      ![r.x, r.y, r.width, r.height].every(
        (v) => Number.isInteger(v) && v >= 0 && v <= 1000000000,
      ) ||
      r.width > 65535 ||
      r.height > 4096
    )
      throw new DropError("bounds");
    if (!focused && this.captured) this.reset("cancel");
    this.renderKey(
      [
        r.x,
        r.y,
        r.width,
        r.height,
        canvas.palette.theme,
        canvas.palette.colors,
        canvas.surfaceRole,
        focused,
        ascii,
      ].join("|"),
    );
    if (!this.valid(model, r.width, r.height)) {
      model.draw(canvas, r, focused, ascii);
      return;
    }
    const child = new Canvas(
      r.width,
      r.height,
      canvas.palette,
      canvas.surfaceRole,
    );
    let markerX = 0,
      markerY = 0,
      marker = "!";
    if (model instanceof Tabs) {
      const views = this.tabCells(model, r.width, this.first);
      model.drawRail(
        child,
        rect(0, 0, r.width, r.height),
        views,
        this.first,
        focused,
        ascii,
      );
      const target = views.find((c) => c.id === this.targetId);
      markerX = target
        ? target.start + (this.position === "after" ? target.width - 1 : 0)
        : Math.max(0, Math.min(r.width - 1, this.lastPointer.x));
      markerY = Number(r.height >= 3);
      marker = ascii ? "|" : "│";
    } else {
      const rows = this.treeRows(model, r.height);
      for (const [y, n] of rows
        .slice(this.scroll, this.scroll + r.height)
        .entries()) {
        const selected = model.selected === n.id,
          arrow = model.branches.has(n.id)
            ? this.expanded.has(n.id)
              ? ascii
                ? "v"
                : "▾"
              : ascii
                ? ">"
                : "▸"
            : " ",
          icon = ascii ? n.ascii_icon : n.icon;
        let text =
          "  ".repeat(model.depth.get(n.id)!) +
          arrow +
          " " +
          (icon ? icon + " " : "") +
          (n.name ?? "");
        if (n.secondary) text += "  " + n.secondary;
        if (n.count !== undefined) text += " (" + n.count + ")";
        const gs = graphemes(text);
        let skipped = 0;
        while (gs.length && skipped < model.horizontal)
          skipped += cells(gs.shift()!);
        child.write(
          0,
          y,
          (selected ? "> " : "  ") +
            clip(gs.join(""), Math.max(0, r.width - 2), true),
          selected ? "selection" : "body",
          focused && selected,
          r.width,
        );
      }
      const i = rows.findIndex((n) => n.id === this.targetId);
      markerX = 0;
      markerY =
        i < 0
          ? Math.max(0, Math.min(r.height - 1, this.lastPointer.y))
          : i - this.scroll;
      marker =
        (
          {
            before: ascii ? "^" : "↑",
            after: ascii ? "v" : "↓",
            inside: ascii ? "+" : "↳",
          } as { [key: string]: string }
        )[this.position] ?? "!";
    }
    if (
      this.phase === "dragging" &&
      markerX >= 0 &&
      markerX < r.width &&
      markerY >= 0 &&
      markerY < r.height
    ) {
      const old = child.data[markerY][markerX].style,
        semantic = child.palette.style(this.allowed ? "info" : "error");
      let foreground = semantic.foreground;
      if (
        colorContrast(foreground, old.background) < 4.5 &&
        colorContrast(old.foreground, old.background) >
          colorContrast(foreground, old.background)
      )
        foreground = old.foreground;
      child.writeStyle(
        markerX,
        markerY,
        this.allowed ? marker : "!",
        {
          foreground,
          background: old.background,
          bold: true,
          dim: false,
          underline: true,
        },
        1,
      );
    }
    canvas.blit(child, rect(0, 0, r.width, r.height), r.x, r.y);
  }
}
