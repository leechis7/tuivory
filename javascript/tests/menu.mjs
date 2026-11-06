import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const f = JSON.parse(
  readFileSync(new URL("../../design/menu-cases.json", import.meta.url)),
);
for (const c of f.scenarios) {
  const m = new ui.Menu(f.items);
  assert.equal(m.open(c.root, c.caller).kind, "open");
  for (const s of c.steps) {
    const e = m.handle(s.action, s.value ?? "", 5);
    assert.deepEqual([e.kind, e.id, e.returnId], [s.event, s.id, c.caller]);
    assert.equal(m.opened, !s.closed);
    if (m.opened) {
      assert.equal(m.focused, s.focus ?? "");
      assert.deepEqual(m.path, s.path ?? []);
    }
  }
}
const m = new ui.Menu(f.items);
m.open("file", "origin");
m.handle("next");
m.handle("activate");
m.handle("next");
const before = m.path;
assert.throws(() => m.setItems([...f.items, f.items[0]]));
assert.deepEqual(m.path, before);
m.setItems(f.items);
assert.equal(m.focused, "deep");
const changed = structuredClone(f.items);
changed[4].disabled = true;
assert.equal(m.setItems(changed).kind, "close");
assert.equal(m.opened, false);
for (const items of [
  [{ id: "@back" }],
  [
    { id: "a", parent: "b" },
    { id: "b", parent: "a" },
  ],
  [{ id: "a", parent: "missing" }],
  [
    { id: "a", mnemonic: "f" },
    { id: "b", mnemonic: "F" },
  ],
  [
    { id: "a", separator: true },
    { id: "b", parent: "a" },
  ],
])
  assert.throws(() => new ui.Menu(items));
m.setItems(f.items);
m.open("file", "editor");
for (const ascii of [false, true])
  for (let width = 0; width < 90; width++)
    for (let height = 0; height < 12; height++) {
      const rows = m.layout(width, height, ascii);
      assert.ok(rows.length <= height);
      for (const r of rows) {
        assert.ok(ui.cells(r.text) <= width);
        for (const s of r.spans) {
          assert.ok(s.start + s.width <= width);
          assert.ok(ui.cells(s.text) <= s.width);
        }
      }
      for (const c of m.barLayout(width).cells) {
        assert.ok(c.start + c.width <= width);
        assert.ok(ui.cells(c.text) <= c.width);
      }
    }
for (let width = 0; width < 40; width++)
  for (let height = 0; height < 20; height++) {
    const v = ui.rect(3, 2, width, height),
      r = ui.menuPlacement(ui.rect(70, 18, 1, 1), v, 40, 20);
    assert.ok(r.x >= v.x && r.x + r.width <= v.x + v.width);
    assert.ok(r.y >= v.y && r.y + r.height <= v.y + v.height);
  }
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"]) {
    const c = new ui.Canvas(40, 12, new ui.Palette(theme, colors));
    m.draw(c, ui.rect(1, 1, 38, 10), false);
    assert.equal(c.cursor, null);
    assert.ok(
      c.data.every((row) => row.every((cell) => !cell.style.underline)),
    );
    assert.equal(m.clickId("off").kind, "");
  }
console.log(
  "Menu shared hierarchy, return requests, atomic validation, clipping/placement and selection-only rendering passed",
);
const { MenuDemo } = await import("../examples/menu-host.mjs");
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"])
    for (const ascii of [false, true]) {
      const host = new MenuDemo(true, true),
        c = new ui.Canvas(72, 18, new ui.Palette(theme, colors));
      host.draw(c, ui.rect(1, 1, 70, 15), ascii);
      assert.equal(c.cursor, null);
      assert.equal(host.focus.depth, 1);
      const initial = host.editor.value;
      host.pointer(2, 1, 0);
      host.handle("insert", "z");
      assert.equal(host.editor.value, initial);
      host.pointer(65, 13, 2);
      host.draw(c, ui.rect(1, 1, 70, 15), ascii);
      assert.ok(
        host.content.x >= 1 && host.content.x + host.content.width <= 71,
      );
      host.handle("cancel");
      assert.equal(host.focus.depth, 0);
      assert.equal(host.focus.focused, "editor");
      host.handle("insert", "z");
      assert.notEqual(host.editor.value, initial);
      host.draw(c, ui.rect(1, 1, 70, 15), ascii);
      assert.ok(c.cursor);
    }
for (let w = 0; w < 12; w++)
  for (let h = 0; h < 8; h++) {
    const menu = new ui.Menu([{ id: "a", label: "A" }]);
    menu.open("");
    const r = menu.drawPopup(
      new ui.Canvas(12, 8),
      ui.rect(0, 0, w, h),
      "Popup",
      99999,
    );
    assert.ok(r.width >= 0 && r.width <= w && r.height >= 0 && r.height <= h);
  }
console.log(
  "Menu example background blocking, right-click placement, scope return and restored real cursor passed",
);

{
  const row = new ui.List([{ id: "long", label: "abcdefghijklmnop" }]).layout(
    8,
    1,
  )[0];
  assert.equal(ui.cells(row.text), 8);
  assert.ok(row.text.endsWith("~"));
}
