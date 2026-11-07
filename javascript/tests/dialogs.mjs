import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const f = JSON.parse(
    readFileSync(new URL("../../design/dialog-cases.json", import.meta.url)),
  ),
  make = () => new ui.Dialog("Confirm", f.message, f.buttons, "cancel");
const d = make();
assert.equal(d.focused, "cancel");
for (const c of f.layouts) {
  const l = d.layout(c.width, c.height);
  assert.deepEqual(l.body, c.body);
  assert.deepEqual(
    l.buttons.map((b) => [b.id, ...Object.values(b.rect)]),
    c.buttons,
  );
  assert.deepEqual([l.hiddenButtons, l.bodyTruncated], [c.hidden, c.truncated]);
}
assert.equal(d.handle("activate").id, "cancel");
assert.equal(d.handle("cancel").kind, "cancel");
assert.equal(d.focused, "cancel");
assert.equal(d.message, f.message);
const buttons = d.buttons;
buttons[2].disabled = true;
d.setButtons(buttons);
assert.equal(d.focused, "retry");
assert.equal(d.handle("cancel").kind, "");
assert.equal(d.focus("cancel"), false);
assert.equal(d.handle("next").id, "details");
assert.equal(d.handle("next").id, "retry");
const before = d.buttons;
assert.throws(() => d.setButtons([{ id: "same" }, { id: "same" }]));
assert.deepEqual(d.buttons, before);
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"])
    for (const ascii of [false, true]) {
      const dialog = make(),
        canvas = new ui.Canvas(40, 12, new ui.Palette(theme, colors)),
        l = dialog.draw(canvas, ui.rect(0, 0, 40, 12), true, ascii),
        cancel = l.buttons.find((b) => b.id === "cancel"),
        x = cancel.rect.x + 2,
        y = cancel.rect.y + 2;
      assert.ok(x + cancel.rect.width <= 40);
      assert.ok(canvas.lines()[y].includes("Cancel"));
      assert.equal(canvas.cursor, null);
      assert.equal(dialog.click(x, y).id, "cancel");
      dialog.draw(canvas, ui.rect(0, 0, 40, 12), true, ascii);
      const b = dialog.buttons;
      b[2].disabled = true;
      dialog.setButtons(b);
      assert.equal(dialog.click(x, y).kind, "");
      const off = dialog
          .draw(canvas, ui.rect(0, 0, 40, 12), true, ascii)
          .buttons.find((b) => b.id === "cancel"),
        ox = off.rect.x + 2,
        oy = off.rect.y + 2,
        focus = dialog.focused;
      assert.equal(dialog.click(ox, oy).kind, "");
      assert.equal(dialog.focused, focus);
      assert.equal(canvas.data[oy][ox].style.dim, true);
      for (let width = 0; width < 12; width++) {
        const tiny = new ui.Canvas(width, 5, canvas.palette),
          layout = dialog.draw(tiny, ui.rect(0, 0, width, 5), true, ascii);
        for (const b of layout.buttons)
          assert.ok(b.rect.x + b.rect.width <= Math.max(0, width - 4));
      }
    }
const literal = make();
literal.setText(undefined, "한글\r\né [error]literal[/]");
assert.equal(literal.message, "한글\r\né [error]literal[/]");
assert.ok(literal.layout(40, 12).body.some((s) => s.includes("[error]")));
assert.throws(() => literal.setText(undefined, "\ud800"));
console.log(
  "Dialog wrapping/default cancel, requests, disabled actions, stale hits, tiny geometry and literal text passed",
);

for (const labels of [
  ["확인", "다시 연결한 다음 계속", "설정 열기", "취소"],
  ["OK", "Reconnect and continue", "Open settings", "Cancel"],
]) {
  for (let count = 1; count <= labels.length; count++) {
    const dialog = new ui.Dialog(
      "",
      "",
      labels
        .slice(0, count)
        .map((label, index) => ({ id: String(index), label })),
      "0",
    );
    for (const width of [36, 116]) {
      const layout = dialog.layout(width, 12);
      assert.equal(layout.buttons.length, count);
      const rows = new Map();
      for (const { rect } of layout.buttons) {
        const first = rows.get(rect.y)?.[0] ?? rect.x;
        rows.set(rect.y, [first, rect.x + rect.width]);
      }
      for (const [left, right] of rows.values()) {
        assert.ok(right <= width);
        assert.equal(left, Math.floor((width - (right - left)) / 2));
      }
    }
  }
}
