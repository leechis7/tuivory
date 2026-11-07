import assert from "node:assert/strict";
import fs from "node:fs";
import * as ui from "../dist/index.js";
const cases = JSON.parse(
  fs.readFileSync(new URL("../../design/document-cases.json", import.meta.url)),
);
for (const f of cases.layout) {
  const d = new ui.TextDocument(f.source, { readOnly: f.read_only });
  d.buffer.secret = f.secret ?? false;
  d.buffer.select(f.cursor, f.cursor);
  d.wrap = f.wrap;
  d.lineNumbers = f.line_numbers;
  d.scrollX = f.scroll_x ?? 0;
  const c = new ui.Canvas(f.width, f.height);
  d.draw(c, ui.rect(0, 0, f.width, f.height));
  assert.deepEqual(
    c.lines().slice(0, f.rows.length),
    f.rows.map((row) => row + " ".repeat(f.width - ui.cells(row))),
    f.name,
  );
  assert.deepEqual(c.cursor, f.screen_cursor ?? null, f.name);
}
for (const f of cases.markup)
  assert.deepEqual(ui.parseMarkup(f.source), {
    source: f.plain,
    spans: f.spans,
  });
const d = ui.TextDocument.editor("unchanged");
d.buffer.select(2, 2);
for (const bad of cases.invalid_markup) {
  assert.throws(() => d.setMarkup(bad));
  assert.equal(d.buffer.value, "unchanged");
  assert.equal(d.buffer.cursor, 2);
}
const f = cases.byte_spans;
d.setText(f.source);
d.setByteSyntax([f.valid]);
assert.deepEqual(d.syntax, [f.expected]);
for (const start of f.invalid_starts) {
  assert.throws(() => d.setByteSyntax([{ start, end: 6, role: "error" }]));
  assert.deepEqual(d.syntax, [f.expected]);
}
d.setText("abc");
d.lineNumbers = false;
d.buffer.select(0, 0);
const spans = [{ start: 0, end: 3, role: "info" }];
d.setSyntax(spans);
spans[0].role = "error";
d.setSearchMatches([{ start: 1, end: 3 }]);
d.buffer.select(0, 2);
assert.deepEqual(
  d
    .layout(8, 2)[0]
    .glyphs.filter((g) => g.index < 3)
    .map((g) => g.role),
  ["selection", "selection", "edited"],
);
d.buffer.disabled = true;
assert(d.layout(8, 2)[0].glyphs.every((g) => g.role === "disabled"));
assert.equal(d.click(0, 0, 8, 2).kind, "");
assert.equal(d.handle("insert", "Z").kind, "");
d.buffer.disabled = false;
d.handle("insert", "X");
d.layout(8, 2);
assert.deepEqual(d.syntax, []);
assert.deepEqual(d.searchMatches, []);
d.buffer.secret = true;
assert(!JSON.stringify(d).includes("X"));
assert.equal(d.handle("copy").kind, "");
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"]) {
    const c = new ui.Canvas(
      10,
      3,
      new ui.Palette(theme, colors),
      "button.focus",
    );
    const d = ui.TextDocument.viewer("한글");
    d.draw(c, ui.rect(0, 0, 10, 3));
    assert.equal(
      c.data[0][0].style.background,
      c.palette.style("button.focus").background,
    );
    assert.equal(c.cursor, null);
  }
const pointer = ui.TextDocument.editor("한글abcd");
pointer.lineNumbers = false;
pointer.wrap = true;
pointer.buffer.select(0, 0);
pointer.layout(4, 6);
pointer.click(1, 0, 4, 6);
assert.equal(pointer.buffer.cursor, 0);
pointer.click(0, 1, 4, 6);
assert.equal(pointer.buffer.cursor, 2);
const c = new ui.Canvas(4, 3);
pointer.draw(c, ui.rect(0, 0, 4, 3));
assert.deepEqual(c.cursor, [0, 1]);
assert.throws(() => pointer.setText("\ud800"));
assert.equal(pointer.buffer.value, "한글abcd");
console.log(
  "Document shared layout/markup/UTF-8, priority/stale, surface/cursor/pointer cases passed",
);

const invalid = ui.TextDocument.editor("safe"),
  dest = new ui.Canvas(8, 2);
dest.write(0, 0, "before");
const before = dest.lines();
assert.throws(() => invalid.draw(dest, ui.rect(-1, 0, 8, 2)));
assert.deepEqual(dest.lines(), before);
for (const value of [-1, 1000001, NaN, 0.5]) {
  invalid.scrollX = value;
  assert.throws(() => invalid.layout(8, 2));
  assert.equal(invalid.buffer.value, "safe");
}
invalid.scrollX = 0;
invalid.scrollY = 1000000;
invalid.handle("page_down");
assert.equal(invalid.scrollY, 1000000);

const limited=ui.TextDocument.editor('safe');assert.throws(()=>limited.handle('insert','a'.repeat(999997)));assert.equal(limited.buffer.value,'safe');assert.equal(limited.buffer.cursor,4);assert.equal(limited.handle('undo').kind,'');limited.handle('insert','\r\n\t');assert.equal(limited.buffer.value,'safe\n ');
