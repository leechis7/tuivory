import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const fixture = (n) =>
  JSON.parse(
    readFileSync(new URL(`../../design/${n}.json`, import.meta.url), "utf8"),
  );
test("shared tree navigation", () => {
  const f = fixture("tree-navigation"),
    tree = new ui.Tree(f.nodes);
  for (const s of f.steps) {
    const e =
      s.action === "click"
        ? tree.click(s.column, s.row, f.height)
        : tree.handle(s.action, f.height);
    assert.equal(tree.selected, s.selected);
    assert.deepEqual([...tree.expanded].sort(), s.expanded);
    assert.equal(tree.scroll, s.scroll);
    assert.equal(tree.horizontal, s.horizontal);
    assert.deepEqual(
      tree.visible().map((n) => n.id),
      s.visible,
    );
    assert.deepEqual([e.kind, e.id], [s.event ?? "", s.id ?? ""]);
  }
});
test("shared tabs and control states", () => {
  const f = fixture("components-cases").tabs,
    tabs = new ui.Tabs(f.items);
  for (const s of f.steps) {
    const e = tabs.handle(s.action);
    assert.deepEqual(
      [tabs.active, tabs.focused, e.kind, e.id],
      [s.active, s.focused, s.event ?? "", s.id ?? ""],
    );
  }
  for (const s of fixture("interaction-cases").states) {
    const state = new ui.ControlState(s.state);
    for (const key of [
      "role",
      "markers",
      "focusable",
      "activatable",
      "editable",
    ])
      assert.equal(state[key], s[key]);
  }
});
test("all palettes, wide edges and terminal cursor commands", () => {
  for (const theme of ["dark", "light", "blackwhite"])
    for (const colors of ["8", "16", "256", "truecolor"]) {
      const c = new ui.Canvas(12, 3, new ui.Palette(theme, colors));
      c.write(0, 0, "한글💻abc");
      const style = c.data[0][0].style;
      c.write(1, 0, " X", "selection", false, 2);
      assert.equal(c.data[0][0].text, " ");
      assert.deepEqual(c.data[0][0].style, style);
      assert.equal(c.data[0][3].text, " ");
      assert.equal(c.data[0][3].owner, -1);
      assert.deepEqual(c.data[0][3].style, style);
      for (let x = 0; x < c.width; x++)
        if (c.data[0][x].owner >= 0)
          assert.ok(ui.cells(c.data[0][c.data[0][x].owner].text) > 1);
      c.setCursor(2, 1, 2);
      const ansi = c.ansi();
      assert.ok(ansi.endsWith("\x1b[2;3H\x1b[?25h"));
      assert.ok(!ansi.includes(" q"));
      assert.ok(!ansi.includes("\x1b[?12"));
    }
});
test("narrow view and literal controls", () => {
  for (let w = 0; w < 20; w++) {
    const c = new ui.Canvas(w, 4),
      t = new ui.Tree([
        { id: "a", name: "\x1b[31m한글" },
        { id: "b", name: "👩‍💻e\u0301" },
      ]);
    t.draw(c, ui.rect(0, 0, w, 4));
    assert.ok(c.lines().every((l) => ui.cells(l) <= w));
    assert.ok(!c.lines().join("").includes("\x1b"));
  }
  assert.equal(ui.cells("한글 👩‍💻"), 7);
});

test("shared Unicode widths including modifiers and selectors", () => {
  for (const c of fixture("language-unicode-cases").cases)
    assert.equal(ui.cells(c.text), c.cells, JSON.stringify(c));
});
