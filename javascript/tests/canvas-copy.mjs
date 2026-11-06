import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const f = JSON.parse(
  readFileSync(new URL("../../design/canvas-copy-cases.json", import.meta.url)),
);
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"]) {
    const palette = new ui.Palette(theme, colors);
    for (const c of f.cases) {
      const source = new ui.Canvas(8, 1, palette);
      source.write(0, 0, f.text, "selection");
      source.setCursor(4, 0, 2);
      const dest = new ui.Canvas(c.width, 1, palette);
      dest.blit(source, ui.rect(...c.region), ...c.at);
      assert.deepEqual(dest.lines(), [c.expected]);
      assert.deepEqual(dest.cursor, c.cursor);
      for (const cell of dest.data[0])
        if (cell.text !== " " && cell.text !== "")
          assert.deepEqual(cell.style, palette.style("selection"));
      assert.equal(dest.ansi().includes("\x1b[?25h"), !!c.cursor);
    }
  }
const c = new ui.Canvas(8, 1);
c.write(0, 0, "a界b한c");
c.setCursor(4, 0, 2);
c.blit(c, ui.rect(0, 0, 6, 1), 2, 0);
assert.deepEqual(c.lines(), ["a a界b한"]);
assert.deepEqual(c.cursor, [6, 0]);
c.fill(ui.rect(7, 0, 1, 1));
assert.equal(c.cursor, null);
assert.deepEqual(c.lines(), ["a a界b  "]);
const source = new ui.Canvas(2, 1);
source.write(0, 0, "界");
const dest = new ui.Canvas(4, 1);
dest.write(0, 0, "界界");
dest.setCursor(0, 0, 2);
dest.blit(source, ui.rect(0, 0, 2, 1), 1, 0);
assert.deepEqual(dest.lines(), [" 界 "]);
assert.equal(dest.cursor, null);
source.fill(ui.rect(0, 0, 2, 1));
assert.deepEqual(dest.lines(), [" 界 "]);
assert.throws(() => dest.blit(source, ui.rect(0, 0, -1, 1), 0, 0));
console.log(
  "Canvas cell copying, source/destination wide edges, self snapshot, styles and cursor occlusion passed",
);
