import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const f = JSON.parse(
  readFileSync(new URL("../../design/layout-cases.json", import.meta.url)),
);
for (const s of f.spacing) {
  const t = ui.SpacingTokens.forWidth(s.density, s.columns);
  assert.deepEqual(
    [t.gap, t.padding, t.controlGap],
    [s.gap, s.padding, s.control_gap],
  );
}
for (const s of f.stacks) {
  const r = ui.stackLayout(s.items ?? f.items, s.total, s.gap);
  assert.deepEqual(
    r.slots.map((i) => [i.id, i.start, i.size]),
    s.slots,
  );
  assert.equal(r.gap, s.actual_gap);
  assert.deepEqual(r.hidden, s.hidden);
}
for (let width = 0; width < 241; width++) {
  const r = ui.stackLayout(f.items, width, 2);
  let end = 0;
  for (const s of r.slots) {
    assert.ok(end <= s.start && s.start + s.size <= width);
    if (s.size) end = s.start + s.size;
  }
  for (const vertical of [false, true])
    for (const item of ui.stackRects(
      ui.rect(2, 3, width, 20),
      f.items,
      new ui.SpacingTokens(2, 1, 2),
      vertical,
    ).rects) {
      const r = item.rect;
      assert.ok(
        r.x >= 2 &&
          r.x + r.width <= 2 + width &&
          r.y >= 3 &&
          r.y + r.height <= 23,
      );
    }
}
assert.equal(f.items[0].preferred, 40);
assert.equal(ui.drawerLayout(ui.rect(0, 0, 30, 10), 24, 40).overlay, true);
assert.equal(ui.drawerLayout(ui.rect(0, 0, 100, 10), 24, 40).overlay, false);
for (const bad of [
  [{ id: "a" }, { id: "a" }],
  [{ id: "a", min: 0 }],
  [{ id: "a", min: 1, weight: -1 }],
])
  assert.throws(() => ui.stackLayout(bad, 20, 1));
for (const s of f.badges) {
  const { text, role, ...options } = s,
    row = new ui.Badge(options).line(40);
  assert.deepEqual([row.text, row.role], [text, role]);
}
for (const s of f.chips) {
  const { request, ...options } = s,
    c = new ui.Chip(options);
  assert.equal(c.requestRemove().kind, request);
  assert.equal(c.removable, s.removable);
  for (let w = 0; w < 40; w++) {
    const r = c.line(w);
    assert.ok(ui.cells(r.text) <= w);
    for (const span of r.spans)
      assert.ok(span.start >= 0 && span.start + span.width <= w);
  }
}
const items = structuredClone(f.shortcuts),
  help = new ui.Help(items);
items[1].text = "changed";
assert.equal(help.layout(40, 1)[0].text, "[F1] Help");
assert.equal(help.layout(40, 2)[1].role, "disabled");
for (const keys of f.duplicate_keys)
  assert.throws(() => new ui.Help(keys.map((key) => ({ key }))));
assert.throws(() => new ui.Help([{ key: " 　" }]));
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"])
    for (let w = 0; w < 20; w++) {
      const c = new ui.Canvas(w, 6, new ui.Palette(theme, colors));
      new ui.Badge({
        label: "Selected",
        count: 123,
        state: { selected: true },
      }).draw(c, ui.rect(0, 0, w, 1));
      new ui.Chip({
        id: "tag",
        label: "한글",
        state: { disabled: true },
        removable: true,
      }).draw(c, ui.rect(0, 1, w, 1));
      help.draw(c, ui.rect(0, 2, w, 4));
      assert.equal(c.cursor, null);
      if (w)
        assert.deepEqual(
          c.data[0][0].style.background,
          c.palette.style("selection").background,
        );
    }
console.log(
  "Layout spacing/weighted stacks, bounds, badge/chip requests and literal priority hints passed",
);
const { LayoutDemo } = await import("../examples/layout-host.mjs");
{
  const h = new LayoutDemo(true),
    c = new ui.Canvas(72, 18);
  h.draw(c, ui.rect(1, 1, 70, 15), false);
  for (const id of ["off", "fixed"]) {
    const hit = h.hits.find((hit) => hit.chip.id === id);
    h.pointer(hit.rect.x, hit.rect.y, 0);
    assert.equal(h.active, true);
    assert.equal(h.status, "");
  }
  const hit = h.hits.find((hit) => hit.chip.id === "filter");
  h.pointer(hit.rect.x, hit.rect.y, 0);
  assert.equal(h.active, false);
  assert.equal(h.filter.removable, true);
  assert.equal(h.hits.length, 0);
  h.handle("insert", "d");
  assert.equal(h.density, "comfortable");
  h.draw(c, ui.rect(1, 1, 70, 15), false);
  assert.equal(c.cursor, null);
}
