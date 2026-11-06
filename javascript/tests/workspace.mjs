import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const f = JSON.parse(
  readFileSync(
    new URL("../../design/components-cases.json", import.meta.url),
    "utf8",
  ),
);
test("shared workspace layouts", () => {
  for (const c of f.tabs.layouts) {
    const t = new ui.Tabs(f.tabs.items);
    t.focused = "c";
    const views = t.layout(c.width);
    assert.equal(t.first, c.first);
    assert.deepEqual(
      views.map((v) => v.id),
      c.ids,
    );
    for (const v of views) {
      assert.ok(v.start + v.width <= c.width);
      assert.ok(ui.cells(v.text) <= v.width);
    }
  }
  for (const c of f.paths) {
    const line = ui.pathRuns(
      [
        { id: "r", label: "root" },
        { id: "f", label: "folder" },
        { id: "c", label: "현재.sql" },
      ],
      c.width,
    );
    assert.equal(line.text, c.text);
    for (const r of line.runs) assert.ok(r.start + r.width <= c.width);
  }
  const items = [
    { id: "help", text: "F1 Help", role: "hint", priority: 1 },
    { id: "err", text: "Failure", role: "error", priority: 100 },
    { id: "draft", text: "Draft", role: "edited", priority: 30 },
  ];
  for (const c of f.status) {
    const line = ui.statusLine(items, c.width);
    assert.equal(line.text, c.text);
    assert.equal(line.omitted, c.omitted);
  }
});
test("tab hit testing and compact split", () => {
  const t = new ui.Tabs([
    { id: "a", title: "ax" },
    { id: "d", title: "Disabled", disabled: true },
    { id: "b", title: "Draft", closable: true },
  ]);
  let views = t.layout(80);
  assert.equal(
    t.click(views[0].start + ui.cells(views[0].text) - 2, 80).kind,
    "activate",
  );
  views = t.layout(80);
  assert.equal(t.click(views[1].start, 80).kind, "");
  const last = t.layout(80)[2];
  assert.equal(t.click(last.start + ui.cells(last.text) - 2, 80).kind, "close");
  const split = new ui.Split(3, 4, 7);
  for (let total = 0; total < 30; total++) {
    const l = split.layout(total);
    assert.equal(l.first + l.divider + l.second, total);
    if (total < 8) {
      assert.ok(l.compact);
      assert.equal(l.first, 0);
    }
  }
  assert.ok(split.resize(30, 10));
});
