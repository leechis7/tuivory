import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const geometry = JSON.parse(
    readFileSync(
      new URL("../../design/popup-shadow-cases.json", import.meta.url),
    ),
  ).cases,
  render = JSON.parse(
    readFileSync(
      new URL("../../design/popup-shadow-render-cases.json", import.meta.url),
    ),
  ).cases;
for (const f of geometry) {
  const o = f.options,
    l = ui.popupPlacement(
      ui.rect(...f.anchor),
      ui.rect(...f.viewport),
      f.width,
      f.height,
      new ui.ShadowOptions(o.mode, o.offsetX, o.offsetY),
    );
  for (const [key, value] of Object.entries(f.expected))
    assert.deepEqual(Object.values(l[key]), value, f.name);
  for (const r of l.shadowRegions())
    for (let y = r.y; y < r.y + r.height; y++)
      for (let x = r.x; x < r.x + r.width; x++)
        assert.equal(l.hit(x, y), false);
}
for (const f of render)
  for (const ascii of [false, true]) {
    const c = new ui.Canvas(20, 10, new ui.Palette(f.theme, f.colors)),
      style = {
        foreground: "1",
        background: f.backdrop,
        bold: true,
        dim: false,
        underline: true,
      };
    for (let y = 0; y < 10; y++) c.writeStyle(0, y, "A".repeat(20), style);
    const l = new ui.Shadow(new ui.ShadowOptions(f.mode)).draw(
      c,
      ui.rect(2, 1, 10, 7),
      (child) =>
        child.panel(
          ui.rect(0, 0, child.width, child.height),
          "Popup",
          false,
          ascii,
        ),
      ascii,
    );
    for (const [x, y, symbol] of [
      [11, 1, "▄"],
      [3, 7, "▀"],
    ]) {
      const cell = c.data[y][x];
      assert.equal(cell.text, ascii ? "." : symbol);
      assert.deepEqual(cell.style, {
        foreground: f.shade,
        background: f.backdrop,
        bold: false,
        dim: false,
        underline: false,
      });
    }
    assert.equal(c.data[2][11].style.background, ascii ? f.backdrop : f.shade);
    assert.equal(l.hit(11, 2), false);
  }
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"])
    for (const mode of ["off", "auto", "solid", "dim"])
      for (const ascii of [false, true]) {
        const c = new ui.Canvas(22, 12, new ui.Palette(theme, colors)),
          style = c.palette.style("body");
        for (let y = 0; y < 12; y++) c.writeStyle(0, y, "界".repeat(11), style);
        const beforeStyles = c.data.map((row) =>
          row.map((cell) => ({ ...cell.style })),
        );
        c.setCursor(6, 8, 2);
        const bounds = ui.rect(3, 2, 10, 7),
          shadow = new ui.Shadow(new ui.ShadowOptions(mode)),
          paint = (child) =>
            child.panel(
              ui.rect(0, 0, child.width, child.height),
              "Popup",
              false,
              ascii,
            ),
          l = shadow.draw(c, bounds, paint, ascii);
        assert.equal(c.cursor, null);
        for (const [x, y, symbol] of [
          [l.card.x, l.card.y, "┌"],
          [l.card.x + l.card.width - 1, l.card.y, "┐"],
          [l.card.x, l.card.y + l.card.height - 1, "└"],
          [l.card.x + l.card.width - 1, l.card.y + l.card.height - 1, "┘"],
        ])
          assert.equal(c.data[y][x].text, ascii ? "+" : symbol);
        for (let y = 0; y < 12; y++)
          for (let x = 0; x < 22; x++) {
            const cell = c.data[y][x];
            if (x < 3 || x >= 13 || y < 2 || y >= 9)
              assert.deepEqual(cell.style, beforeStyles[y][x]);
            if (cell.owner >= 0)
              assert.ok(
                cell.owner < x &&
                  c.data[y][cell.owner].owner < 0 &&
                  ui.cells(c.data[y][cell.owner].text) > x - cell.owner,
              );
          }
        if (mode === "dim") {
          assert.equal(c.data[8][6].text, "界");
          assert.equal(c.data[8][6].style.dim, true);
        }
        c.setCursor(0, 0, 2);
        shadow.draw(c, bounds, paint, ascii);
        assert.deepEqual(c.cursor, [0, 0]);
        const before = c.ansi();
        assert.throws(() =>
          shadow.draw(
            c,
            bounds,
            (child) => {
              child.fill(ui.rect(0, 0, child.width, child.height));
              throw new Error("host");
            },
            ascii,
          ),
        );
        assert.equal(c.ansi(), before);
        shadow.draw(c, ui.rect(100, 100, 10, 7), () => {});
        assert.equal(c.ansi(), before);
      }
assert.throws(() => new ui.ShadowOptions("invalid"));
assert.throws(() => ui.popupPlacement(ui.rect(), ui.rect(), -1, 1));
console.log(
  "Popup footprint/32fixtures, backdrop-aware half/ASCII shadows, wide edges, Dim, hit isolation and cursor ownership passed",
);
