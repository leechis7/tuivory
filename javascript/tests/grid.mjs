import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const fixture = (name) =>
  JSON.parse(
    readFileSync(new URL(`../../design/${name}.json`, import.meta.url), "utf8"),
  );
const model = (
  rows = [
    { id: "r1", cells: { a: "한글", b: null } },
    { id: "r2", cells: { a: "Straße", b: "two" } },
  ],
) => {
  const g = new ui.Grid(
    [
      { id: "a", label: "Name", width: 6, editable: true },
      { id: "b", label: "Value", width: 8, editable: true },
    ],
    rows,
  );
  g.editEnabled = true;
  return g;
};
for (const c of fixture("grid-work-cases").cases) {
  if (c.accepted) {
    const rows = ui.parseGridTSV(c.text);
    assert.deepEqual(rows.flat(), c.values, c.id);
    assert.deepEqual(ui.parseGridTSV(ui.formatGridTSV(rows)), rows);
  } else assert.throws(() => ui.parseGridTSV(c.text), undefined, c.id);
}
assert.throws(() => ui.parseGridTSV("a\tb", 1));
for (const c of fixture("grid-cursor-cases").cases) {
  const g = new ui.Grid(
    [{ id: "a", label: "A", width: c.width, editable: true }],
    [{ id: "r", cells: { a: c.text } }],
  );
  g.editEnabled = true;
  assert.equal(g.beginEdit(), true);
  g.edit.buffer.select(c.cursor, c.cursor);
  let canvas = new ui.Canvas(c.width, 2);
  g.draw(canvas, ui.rect(0, 0, c.width, 2));
  assert.equal(
    canvas.lines()[1],
    c.visible_text + " ".repeat(c.width - ui.cells(c.visible_text)),
    c.id,
  );
  assert.deepEqual(canvas.cursor, [c.x, 1]);
  assert.ok(canvas.ansi().includes("\x1b[?25h"));
  const e = g.handle("submit");
  canvas = new ui.Canvas(c.width, 2);
  g.draw(canvas, ui.rect(0, 0, c.width, 2));
  assert.equal(canvas.cursor, null);
  assert.equal(g.resolveEdit(e.data.id, "retry"), true);
}
{
  const rows = [{ id: "r", cells: { a: "old" } }],
    g = model(rows);
  rows[0].cells.a = "outside";
  assert.equal(g.rows[0].cells.a, "old");
  const snapshot = g.rows;
  snapshot[0].cells.a = "snapshot";
  assert.equal(g.rows[0].cells.a, "old");
  g.beginEdit();
  g.handle("insert", 10, "!");
  const first = g.handle("submit");
  assert.equal(g.rows[0].cells.a, "old");
  assert.equal(g.resolveEdit(first.data.id, "denied"), true);
  const second = g.handle("submit");
  assert.notEqual(first.data.id, second.data.id);
  assert.equal(g.resolveEdit(first.data.id), false);
  g.columns[0].editable = false;
  assert.equal(g.resolveEdit(second.data.id), false);
  assert.equal(g.edit, null);
  g.columns[0].editable = true;
  g.beginEdit();
  const third = g.handle("submit");
  g.setRows([{ id: "r", cells: { a: "replacement" } }]);
  assert.equal(g.resolveEdit(third.data.id), false);
}
for (const flag of ["disabled", "busy", "read_only"]) {
  const g = model([
    {
      id: "r",
      cells: { a: "x" },
      state: { [flag]: true },
      cellStates: { a: {} },
    },
  ]);
  assert.equal(g.beginEdit(), false, flag);
  assert.equal(g.paste("new").kind, "paste_rejected", flag);
}
{
  const g = model();
  g.prepare = () => false;
  assert.equal(g.beginEdit(), false);
  assert.equal(g.paste("new").kind, "paste_rejected");
  g.prepare = null;
  g.beginEdit();
  g.prepare = () => false;
  assert.equal(g.handle("insert", 10, "x").kind, "edit_stale");
  assert.equal(g.edit, null);
}
{
  const g = model(),
    e = g.paste("one\ttwo\nthree\tfour");
  assert.equal(e.kind, "paste_request");
  e.data.changes[0].rowId = "tamper";
  assert.equal(g.pendingPaste.changes[0].rowId, "r1");
  g.columns[1].editable = false;
  assert.equal(g.resolvePaste(e.data.id), false);
  assert.equal(g.pendingPaste, null);
  assert.equal(g.rows[0].cells.a, "한글");
  g.columns[1].editable = true;
  const next = g.paste("one\ttwo");
  assert.equal(g.resolvePaste(next.data.id), true);
  assert.equal(g.resolvePaste(next.data.id), false);
  assert.equal(g.rows[0].cells.a, "한글");
  const nulls = g.paste('NULL\t""', 10000, "NULL");
  assert.deepEqual(
    nulls.data.changes.map((v) => v.value),
    [null, ""],
  );
}
{
  const source = {
    length: 10000000,
    calls: 0,
    row(i) {
      this.calls++;
      return { id: String(i), cells: { a: "한글", b: String(i) } };
    },
    indexOf(id) {
      return /^\d+$/.test(id) && Number(id) < this.length
        ? Number(id)
        : undefined;
    },
  };
  const g = new ui.Grid(
    [
      { id: "a", width: 5 },
      { id: "b", width: 5 },
    ],
    source,
  );
  g.focus("9999999", "a");
  g.draw(new ui.Canvas(20, 6), ui.rect(0, 0, 20, 6));
  assert.ok(source.calls < 100);
  assert.equal(g.rowId, "9999999");
  assert.throws(() =>
    g.setSource({
      ...source,
      indexOf() {
        return 0;
      },
    }),
  );
  assert.equal(g.rowId, "9999999");
}
{
  const g = model();
  g.setSelection({
    anchorRow: "r1",
    anchorColumn: "a",
    endRow: "r2",
    endColumn: "b",
  });
  assert.deepEqual(ui.parseGridTSV(g.copySelection().text), [
    ["한글", "NULL"],
    ["Straße", "two"],
  ]);
  const o = g.options;
  o.maxCopyCells = 3;
  g.setOptions(o);
  assert.equal(g.copySelection().kind, "copy_rejected");
  assert.equal(g.find("STRASSE"), true);
  assert.deepEqual([g.rowId, g.columnId], ["r2", "a"]);
  g.caseSensitive = true;
  assert.equal(g.find("STRASSE"), false);
  const info = new ui.GridCellInfo({
    display: "shown",
    hasDisplay: true,
    numeric: true,
  });
  g.cellInfo = () => info;
  g.useDisplay = true;
  assert.equal(g.find("shown"), true);
  assert.deepEqual(info.state, {});
  g.caseSensitive = false;
  g.useDisplay = false;
  assert.equal(g.find("shown"), false);
}
{
  const g = model(),
    one = g.request("search", "old"),
    two = g.request("search", "new");
  assert.equal(
    g.applySource(
      one.data.revision,
      new ui.MemoryRows([{ id: "old", cells: {} }]),
    ),
    false,
  );
  assert.equal(
    g.applySource(
      two.data.revision,
      new ui.MemoryRows([{ id: "new", cells: { a: "fresh" } }]),
    ),
    true,
  );
  assert.equal(g.applySource(two.data.revision, new ui.MemoryRows([])), false);
  assert.equal(g.rowId, "new");
  g.beginEdit();
  const e = g.handle("next");
  assert.equal(g.columnId, "a");
  assert.equal(g.resolveEdit(e.data.id), true);
  assert.equal(g.columnId, "b");
  assert.equal(g.edit.columnId, "b");
}
{
  const g = model();
  g.setSelection({
    anchorRow: "r1",
    anchorColumn: "a",
    endRow: "r2",
    endColumn: "b",
  });
  const view = g.saveView();
  g.focus("r2", "b");
  g.restoreView(view);
  assert.deepEqual([g.rowId, g.columnId], ["r1", "a"]);
  const before = g.saveView(),
    bad = g.saveView();
  bad.columns[0].width = 0;
  g.beginEdit();
  assert.throws(() => g.restoreView(bad));
  assert.deepEqual(g.saveView(), before);
  assert.ok(g.edit);
  g.prepare = () => g.setRows([]);
  assert.throws(() => g.handle("submit"));
  assert.equal(g.rows.length, 2);
}
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"])
    for (const ascii of [false, true]) {
      const g = model(),
        o = ui.gridPreset("data").withDensity("comfortable");
      o.ascii = ascii;
      g.setOptions(o);
      g.cellInfo = (r) =>
        new ui.GridCellInfo({ state: { disabled: r.id === "r2" } });
      for (const width of [0, 1, 4, 12, 30]) {
        const c = new ui.Canvas(width, 6, new ui.Palette(theme, colors));
        g.draw(c, ui.rect(0, 0, width, 6), true, ascii);
        for (const row of c.data)
          for (const cell of row)
            if (cell.owner >= 0) assert.ok(ui.cells(row[cell.owner].text) > 1);
        assert.equal(c.cursor, null);
      }
      const c = new ui.Canvas(30, 6, new ui.Palette(theme, colors));
      g.draw(c, ui.rect(0, 0, 30, 6));
      assert.ok(c.data[3].some((cell) => cell.style.dim));
      assert.equal(g.click(4, 3, 30, 6).kind, "");
      assert.equal(g.click(4, 1, 29, 6).kind, "");
    }
{
  const g = new ui.Grid(
    [
      { id: "a", width: 3, pin: "left" },
      { id: "b", width: 5 },
      { id: "c", width: 3, pin: "right" },
    ],
    [{ id: "r", cells: { a: "A", b: "a한bc", c: "C" } }],
  );
  g.setColumnOptions("b", new ui.GridColumnOptions({ overflow: "scroll" }));
  g.panCell("b", 2);
  const c = new ui.Canvas(11, 3);
  g.draw(c, ui.rect(0, 0, 11, 3));
  assert.equal(c.lines()[1], "A   bc  C  ");
  assert.deepEqual(
    g.geometry(11, 3).columns.map((s) => [s.id, s.x]),
    [
      ["a", 0],
      ["b", 3],
      ["c", 8],
    ],
  );
  g.setSelection({
    anchorRow: "r",
    anchorColumn: "a",
    endRow: "r",
    endColumn: "c",
  });
  g.setRows([{ id: "r", cells: { a: "new" } }]);
  assert.ok(g.selected);
}
{
  const g = model();
  g.setEditOptions({
    enabled: true,
    startTyping: true,
    allowNull: true,
    prepare: () => ({ text: "prepared", null: false }),
  });
  assert.equal(g.handle("insert", 10, "typed").kind, "edit_begin");
  assert.equal(g.edit.buffer.value, "typed");
  g.handle("cancel");
  assert.equal(g.beginEdit(), true);
  assert.equal(g.edit.buffer.value, "prepared");
  g.handle("null");
  assert.equal(g.handle("submit").data.value, null);
  g.setEditOptions({ enabled: true, prepare: () => null });
  assert.equal(g.beginEdit(), false);
  g.setEditOptions({ enabled: true });
  g.beginEdit();
  assert.equal(g.handle("null").kind, "");
  assert.equal(g.edit.null, false);
  g.setCellInfo(() => new ui.GridCellInfo({ state: { disabled: true } }));
  assert.equal(g.edit, null);
  assert.equal(g.details(), null);
  const bad = new ui.GridOptions({ padding: NaN });
  assert.throws(() => g.setOptions(bad));
  assert.throws(() =>
    g.setColumnOptions("a", new ui.GridColumnOptions({ minWidth: Infinity })),
  );
}
console.log(
  "Grid shared TSV/cursor, independent virtual source, edit/paste approval, stable views, range copy, Unicode find and all-palette narrow rendering passed",
);
{
  const source = {
    items: [
      { id: "r1", cells: { a: "first" } },
      { id: "r2", cells: { a: "second" } },
    ],
    reenter: false,
    grid: null,
    get length() {
      return this.items.length;
    },
    row(i) {
      if (this.reenter) this.grid.focus("r2", "a");
      return this.items[i];
    },
    indexOf(id) {
      const i = this.items.findIndex((r) => r.id === id);
      return i < 0 ? undefined : i;
    },
  };
  const g = new ui.Grid([{ id: "a", width: 8, editable: true }], source);
  source.grid = g;
  const c = new ui.Canvas(10, 4);
  g.draw(c, ui.rect(0, 0, 10, 4));
  source.items.reverse();
  assert.equal(g.click(1, 1, 10, 4).kind, "");
  g.draw(c, ui.rect(0, 0, 10, 4));
  assert.equal(g.click(1, 1, 10, 4).id, "r2");
  g.columns[0].width = 4;
  assert.equal(g.click(1, 0, 10, 4).kind, "");
  source.reenter = true;
  const before = c.lines();
  assert.throws(() => g.draw(c, ui.rect(0, 0, 10, 4)));
  assert.deepEqual(c.lines(), before);
  source.reenter = false;
  assert.equal(g.rowId, "r2");
  g.setEditOptions({ enabled: true, prepare: () => g.focus("r1", "a") });
  assert.throws(() => g.beginEdit());
  assert.equal(g.rowId, "r2");
}
{
  const g = new ui.Grid(
    [{ id: "a", label: "A", width: 2, editable: true }],
    [{ id: "r", cells: { a: null } }],
  );
  g.setLabels(new ui.GridLabels({ nullText: "한글" }));
  g.setColumnOptions(
    "a",
    new ui.GridColumnOptions({ autoFit: true, maxWidth: 8 }),
  );
  assert.equal(g.geometry(20, 4).columns[0].width, 4);
  assert.equal(g.columns[0].width, 2);
  g.setEditOptions({ enabled: true, allowNull: true });
  assert.equal(g.beginEdit(), true);
  const c = new ui.Canvas(20, 4);
  g.draw(c, ui.rect(0, 0, 20, 4));
  assert.ok(c.lines()[1].includes("한글"));
  assert.equal(c.cursor, null);
  assert.ok(g.edit);
  const e = g.handle("submit");
  g.geometry(20, 4);
  assert.equal(g.edit.pending, true);
  assert.equal(g.resolveEdit(e.data.id), true);
  const labels = g.labels;
  labels.nullText = "outside";
  assert.equal(g.labels.nullText, "한글");
  g.setLabels(new ui.GridLabels({ nullText: "[x]" }));
  g.draw(c, ui.rect(0, 0, 20, 4));
  assert.ok(c.lines()[1].includes("[x]"));
}
