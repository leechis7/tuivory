import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const f = JSON.parse(
  readFileSync(
    new URL("../../design/drag-cases.json", import.meta.url),
    "utf8",
  ),
);
const tabs = () => new ui.Tabs(f.tabs),
  tree = () => {
    const t = new ui.Tree(f.tree);
    t.expanded = new Set(["root", "a"]);
    return t;
  };
const snapshot = (m) =>
  JSON.stringify(
    m instanceof ui.Tabs
      ? [m.items, m.active, m.focused, m.first]
      : [m.nodes, m.selected, m.scroll, m.horizontal, [...m.expanded].sort()],
  );
const p = (action, x, y, width = 60, height = 2) => ({
  action,
  x,
  y,
  width,
  height,
});
for (const c of f.cases) {
  const m = c.kind === "tabs" ? tabs() : tree(),
    before = snapshot(m);
  assert.equal(
    ui.dragRevision(m),
    f[c.kind === "tabs" ? "tab_revision_hex" : "tree_revision_hex"],
  );
  const options = new ui.DragOptions({ locked: c.locked ?? [] });
  if (c.error)
    assert.throws(
      () =>
        m.requestDrop(
          c.source,
          c.target,
          c.position,
          options,
          c.deny ? () => false : undefined,
        ),
      (e) => e instanceof ui.DropError && e.reason === c.error,
    );
  else {
    const request = m.requestDrop(c.source, c.target, c.position, options),
      next = m.applyDrop(request);
    assert.notEqual(next, m);
    assert.deepEqual(
      (next instanceof ui.Tabs ? next.items : next.nodes).map((n) => n.id),
      c.order,
    );
    if (next instanceof ui.Tree)
      assert.equal(next.byId.get(c.source).parent, c.parent);
  }
  assert.equal(snapshot(m), before);
}
{
  const m = tabs(),
    d = new ui.DragState();
  d.pointer(m, p("down", 3, 0));
  assert.equal(d.captured, false);
  d.enabled = true;
  const before = snapshot(m);
  d.pointer(m, p("down", 3, 0));
  assert.equal(d.captured, true);
  d.pointer(m, p("move", 4, 1));
  assert.equal(d.phase, "armed");
  d.pointer(m, p("up", 4, 1));
  assert.equal(d.result, "");
  assert.equal(d.captured, false);
  const target = m.layout(60).find((c) => c.id === "c"),
    x = target.start + target.width - 1;
  d.pointer(m, p("down", 3, 0));
  d.pointer(m, p("move", x, 0));
  assert.equal(d.allowed, true);
  const request = d.pointer(m, p("up", x, 0));
  assert.equal(request.targetId, "c");
  assert.equal(d.result, "drop");
  assert.equal(snapshot(m), before);
  d.pointer(m, p("down", 3, 0));
  d.pointer(m, p("move", 70, 0));
  assert.equal(d.pointer(m, p("up", 70, 0)), null);
  assert.equal(d.result, "reject");
  d.pointer(m, p("down", 3, 0));
  d.cancel();
  assert.equal(d.result, "cancel");
  assert.equal(snapshot(m), before);
}
{
  const m = tree(),
    before = snapshot(m),
    d = new ui.DragState(true),
    o = new ui.DragOptions({ hoverExpand: true });
  d.pointer(m, p("down", 6, 3, 24, 6), o);
  d.pointer(m, p("move", 10, 4, 24, 6), o);
  assert.equal(d.allowed, true);
  assert.equal(m.expanded.has("c"), false);
  const preview = d.previewLayout(m, 24, 6);
  assert.ok(preview.expanded.includes("c"));
  assert.ok(preview.rows.some((n) => n.id === "c1"));
  assert.throws(() => preview.rows.pop());
  const request = d.pointer(m, p("up", 10, 4, 24, 6), o);
  assert.deepEqual(
    [request.sourceId, request.targetId, request.position],
    ["b", "c", "inside"],
  );
  assert.equal(snapshot(m), before);
  let allowed = true;
  const policy = () => allowed;
  d.pointer(m, p("down", 6, 3, 24, 6), o, policy);
  d.pointer(m, p("move", 10, 4, 24, 6), o, policy);
  allowed = false;
  assert.equal(d.pointer(m, p("up", 10, 4, 24, 6), o, policy), null);
  assert.equal(d.result, "reject");
  assert.equal(snapshot(m), before);
}
for (const change of ["state", "data", "size", "palette"]) {
  const m = tabs(),
    d = new ui.DragState(true);
  let c = new ui.Canvas(60, 2);
  d.draw(m, c, ui.rect(0, 0, 60, 2));
  d.pointer(m, p("down", 3, 0));
  if (change === "state") m.focused = "b";
  else if (change === "data") m.items[0].title = "new title";
  else if (change === "size") c = new ui.Canvas(59, 2);
  else c = new ui.Canvas(60, 2, new ui.Palette("light", "8"));
  d.draw(m, c, ui.rect(0, 0, c.width, 2));
  assert.equal(d.captured, false);
  assert.equal(d.result, "stale", change);
}
{
  const m = tabs(),
    r = m.requestDrop("a", "c", "after");
  m.items[0].edited = false;
  assert.throws(
    () => m.applyDrop(r),
    (e) => e.reason === "stale",
  );
  const t = tabs();
  t.focused = "c";
  const request = t.keyboardDrop("previous");
  assert.deepEqual(
    [request.sourceId, request.targetId, request.position],
    ["c", "b", "before"],
  );
  const updated = t.applyDrop(request);
  assert.equal(updated.focused, "c");
  assert.equal(updated.items[0].edited, true);
  const tr = tree();
  tr.selected = "b";
  const move = tr.keyboardDrop("inside");
  assert.deepEqual([move.targetId, move.position], ["a", "inside"]);
  const next = tr.applyDrop(move);
  assert.equal(next.selected, "b");
  assert.equal(next.byId.get("b").parent, "a");
  const outside = next.keyboardDrop("outside");
  assert.deepEqual([outside.targetId, outside.position], ["a", "after"]);
}
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"])
    for (const ascii of [false, true]) {
      const m = tree(),
        before = snapshot(m),
        d = new ui.DragState(true),
        c = new ui.Canvas(28, 8, new ui.Palette(theme, colors), "button.focus"),
        area = ui.rect(1, 1, 24, 6);
      d.draw(m, c, area, true, ascii);
      d.pointer(m, p("down", 6, 3, 24, 6));
      d.pointer(m, p("move", 10, 4, 24, 6));
      d.draw(m, c, area, true, ascii);
      const marker = c.data[5][1];
      assert.equal(marker.text, ascii ? "+" : "↳");
      assert.ok(marker.style.bold && marker.style.underline);
      assert.equal(
        marker.style.background,
        c.palette.style("button.focus").background,
      );
      assert.equal(c.cursor, null);
      for (const row of c.data)
        for (const cell of row)
          if (cell.owner >= 0) assert.ok(ui.cells(row[cell.owner].text) > 1);
      assert.equal(snapshot(m), before);
      d.cancel();
    }
{
  const m = tabs(),
    d = new ui.DragState(true);
  d.pointer(m, p("down", 3, 0, 60, 1));
  const before = [d.phase, d.sourceId];
  assert.throws(
    () => d.pointer(m, p("move", 10, 0, -1, 1)),
    (e) => e.reason === "pointer",
  );
  assert.deepEqual([d.phase, d.sourceId], before);
  const target = m.layout(60).find((c) => c.id === "c"),
    x = target.start + target.width - 1;
  d.pointer(m, p("move", x, 0, 60, 1), undefined, () => d.cancel());
  assert.equal(d.allowed, false);
  assert.equal(d.reason, "policy");
}
{
  const ns = [{ id: "n0" }];
  for (let i = 1; i < 129; i++)
    ns.push({ id: "n" + i, parent: "n" + (i - 1), branch: i === 128 });
  ns.push({ id: "move" });
  const m = new ui.Tree(ns);
  assert.throws(
    () => m.requestDrop("move", "n128", "inside"),
    (e) => e.reason === "depth",
  );
  const model = tabs(),
    d = new ui.DragState(true),
    c = new ui.Canvas(60, 2);
  d.draw(model, c, ui.rect(0, 0, 60, 2));
  d.pointer(model, p("down", 3, 0));
  const before = [d.phase, d.sourceId];
  assert.throws(
    () => d.draw(model, c, ui.rect(0, 0, 65536, 2)),
    (e) => e.reason === "bounds",
  );
  assert.deepEqual([d.phase, d.sourceId], before);
  d.draw(model, c, ui.rect(0, 0, 60, 2), false);
  assert.equal(d.result, "cancel");
  assert.equal(d.captured, false);
}
console.log(
  "Drag shared immutable requests/FNV64, gesture threshold/capture, preview-only expansion, policy recheck, stale context and actual-surface feedback passed",
);

for (const kind of ["preview", "render"]) {
  const m = tabs(),
    d = new ui.DragState(true);
  d.pointer(m, p("down", 3, 0, 60, 1));
  const target = m.layout(60).find((c) => c.id === "c");
  d.pointer(
    m,
    p("move", target.start + target.width - 1, 0, 60, 1),
    undefined,
    () => {
      if (kind === "preview") d.previewLayout(m, 60, 1);
      else d.renderKey("changed inside policy");
      return true;
    },
  );
  assert.equal(d.allowed, false);
  assert.equal(d.reason, "policy");
  assert.equal(d.captured, true);
}
// A valid broad subtree must not hit JavaScript's function argument limit.
{
  const children = Array.from({ length: 130000 }, (_, i) => ({
    id: "leaf" + i,
    parent: "source",
  }));
  const model = new ui.Tree([
    { id: "source", branch: true },
    ...children,
    { id: "target", branch: true },
  ]);
  const request = model.requestDrop("source", "target", "inside");
  const next = model.applyDrop(request);
  assert.equal(next.byId.get("source").parent, "target");
  assert.equal(next.nodes.length, model.nodes.length);
  assert.equal(model.byId.get("source").parent ?? "", "");
}
