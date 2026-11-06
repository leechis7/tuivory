import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const f = JSON.parse(
  readFileSync(new URL("../../design/controls-cases.json", import.meta.url)),
).layout;
const remap = (o) =>
  Object.fromEntries(
    Object.entries(o).map(([k, v]) => [
      k.replace(/_([a-z])/g, (_, c) => c.toUpperCase()),
      v,
    ]),
  );
for (const c of f) {
  const items = c.items.map(remap),
    o = remap(c.options),
    bounds = { ...ui.rect(), ...c.bounds };
  assert.deepEqual(
    ui
      .computeContainer(bounds, items, o)
      .map((n) => [n.id, ...Object.values(n.rect)]),
    c.expected,
  );
  for (let w = 0; w < 25; w++)
    for (let h = 0; h < 10; h++)
      for (const n of ui.computeContainer(ui.rect(2, 3, w, h), items, o)) {
        const r = n.rect;
        assert.ok(
          2 <= r.x &&
            r.x + r.width <= 2 + w &&
            3 <= r.y &&
            r.y + r.height <= 3 + h,
        );
      }
}
let items = [{ id: "a" }, { id: "b" }];
const s = new ui.ContainerState();
s.reconcile(items);
assert.equal(s.moveFocus(items), "b");
items.push({ id: "popup", modal: true });
s.reconcile(items);
assert.equal(s.focused, "popup");
items.push({ id: "nested", modal: true });
s.reconcile(items);
s.captured = "nested";
items = items.slice(0, 2);
s.reconcile(items);
assert.equal(s.focused, "b");
assert.equal(s.captured, "");
const c = new ui.Container(
  [
    { id: "top", track: { fixed: 1 } },
    { id: "editor", track: { fixed: 1 } },
  ],
  { kind: "column", virtualWidth: 8, virtualHeight: 3 },
);
c.state.focused = "editor";
c.scrollX = 2;
c.scrollY = 1;
const paint = (id, child, focused) => {
  child.write(-1, 0, "界a界b한c", "selection");
  child.write(0, 99, "overflow");
  child.setCursor(3, 0, 2);
};
const canvas = new ui.Canvas(9, 4);
canvas.write(0, 0, "Outside");
c.draw(canvas, ui.rect(1, 1, 5, 1), paint);
assert.deepEqual(canvas.cursor, [2, 1]);
assert.equal(c.pointer(2, 1, true), "editor");
assert.equal(c.pointer(50, 50, false, true), "editor");
assert.equal(c.state.captured, "");
assert.equal(canvas.lines()[0], "Outside  ");
assert.equal(canvas.lines()[2], " ".repeat(9));
const before = canvas.ansi();
assert.throws(() =>
  c.draw(canvas, ui.rect(1, 1, 5, 1), () => {
    throw new Error("host");
  }),
);
assert.equal(canvas.ansi(), before);
c.setItems([{ id: "editor", disabled: true }], {});
c.draw(canvas, ui.rect(1, 1, 5, 1), paint);
assert.equal(canvas.cursor, null);
assert.throws(() => c.setItems([{ id: "same" }, { id: "same" }]));
assert.equal(c.items[0].id, "editor");
console.log(
  "Configured row/column/grid/layers, modal restoration, captured routing and clipped virtual rendering passed",
);
