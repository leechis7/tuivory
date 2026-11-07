import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import * as ui from "../dist/index.js";
const F = JSON.parse(
  readFileSync(
    new URL("../../design/grid-pointer-cases.json", import.meta.url),
  ),
);
const rows = () =>
  F.rows.map((r) => ({
    id: r.id,
    cells: { a: r.a, b: "b", c: "c" },
    state: { disabled: !!r.disabled, readOnly: !!r.read_only },
  }));
function model(source) {
  const g = new ui.Grid(
    F.columns.map((c) => ({
      id: c.id,
      label: c.id.toUpperCase(),
      width: c.width,
      editable: true,
    })),
    source ?? rows(),
  );
  g.setOptions(ui.gridPreset("data"));
  g.setColumnOptions(
    "a",
    new ui.GridColumnOptions({ minWidth: 4, maxWidth: 14 }),
  );
  g.setEditOptions({ enabled: true, startTyping: false, allowNull: false });
  return g;
}
function draw(g, width = 64, height = 10, theme = "dark", focused = true) {
  const c = new ui.Canvas(width, height, new ui.Palette(theme, "8"));
  g.draw(c, ui.rect(0, 0, width, height), focused);
  return c;
}
function point(g, at, width, height, origin) {
  const [kind, a, b, c] = at;
  if (kind === "outside") return [-3, height + 3];
  if (kind === "delta") return [origin[0] + a, origin[1] + b];
  const geo = g.geometry(width, height);
  if (kind === "header" || kind === "divider") {
    const s = geo.columns.find((s) => s.id === a);
    return [s.x + (kind === "divider" ? s.width : 0), 0];
  }
  const index = F.rows.findIndex((r) => r.id === a),
    y = geo.headerRows + (index - geo.top) * geo.stride;
  if (kind === "gutter") return [0, y];
  const s = geo.columns.find((s) => s.id === b);
  return [s.x + (kind === "editor" ? g.options.padding + c : 0), y];
}
for (const c of F.cases) {
  const g = model();
  let width = F.width,
    height = F.height,
    origin = [0, 0];
  draw(g, width, height);
  for (const step of c.steps) {
    const [w, h] = step.viewport ?? [width, height];
    let e;
    if (step.key) e = g.handle(step.key, h);
    else {
      const [x, y] = point(g, step.at, w, h, origin);
      if (step.action === "down") origin = [x, y];
      e = g.pointer(step.action, x, y, w, h, step.extend ?? false);
    }
    assert.equal(e.kind, step.event, c.name);
    const values = {
      row: g.rowId,
      column: g.columnId,
      captured: g.pointerCaptured,
      range: g.selected
        ? [
            g.selected.anchorRow,
            g.selected.anchorColumn,
            g.selected.endRow,
            g.selected.endColumn,
          ]
        : null,
      order: g.columns.map((x) => x.id),
      caret: g.edit ? [g.edit.buffer.anchor, g.edit.buffer.cursor] : null,
    };
    for (const [k, v] of Object.entries(values))
      if (k in step) assert.deepEqual(v, step[k], c.name + " " + k);
    if (step.width)
      assert.equal(
        g.columns.find((c) => c.id === step.width[0]).width,
        step.width[1],
      );
    draw(g, w, h);
    width = w;
    height = h;
  }
}
{
  const data = rows(),
    src = {
      get length() {
        return data.length;
      },
      row(i) {
        return data[i];
      },
      indexOf(id) {
        const i = data.findIndex((r) => r.id === id);
        return i < 0 ? undefined : i;
      },
    };
  const g = model(src);
  draw(g);
  const [x, y] = point(g, ["cell", "r1", "a"], 64, 10, [0, 0]);
  g.pointer("down", x, y, 64, 10);
  assert.equal(g.pointerCaptured, true);
  [data[2], data[3]] = [data[3], data[2]];
  const [tx, ty] = point(g, ["cell", "r3", "b"], 64, 10, [0, 0]);
  assert.equal(g.pointer("move", tx, ty, 64, 10).kind, "");
  assert.equal(g.pointerCaptured, false);
  assert.equal(g.rowId, "r1");
  assert.equal(g.selected, null);
  draw(g);
  g.pointer("down", x, y, 64, 10);
  draw(g, 64, 10, "light");
  assert.equal(g.pointerCaptured, false);
  g.pointer("down", x, y, 64, 10);
  draw(g, 64, 10, "light", false);
  assert.equal(g.pointerCaptured, false);
}
{
  const g = model();
  draw(g);
  const [x, y] = point(g, ["editor", "r1", "a", 0], 64, 10, [0, 0]);
  g.pointer("double", x, y, 64, 10);
  draw(g);
  g.pointer("down", x + 1, y, 64, 10);
  g.pointer("move", x + 3, y, 64, 10);
  const c = draw(g);
  assert.equal(c.data[y][x].text, "한");
  assert.equal(c.data[y][x + 1].owner, x);
  assert.equal(
    c.data[y][x].style.background,
    c.palette.style("selection").background,
  );
  assert.deepEqual(c.cursor.slice(0, 2), [x + 2, y]);
}
console.log(
  "Grid shared capture, stale hit guards, keyboard ranges, header resize/reorder and selected wide editor glyphs passed",
);
