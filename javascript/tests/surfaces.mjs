import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as ui from "../dist/index.js";
const f = JSON.parse(
  readFileSync(new URL("../../design/surface-cases.json", import.meta.url)),
);
for (const v of f.text) {
  const p = new ui.Palette(v.theme, v.colors),
    s = p.textOnSurface(v.role, v.surface);
  assert.deepEqual(
    [s.foreground, s.background, s.dim],
    [v.foreground, v.background, v.dim ?? false],
  );
}
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"])
    for (const surface of f.surfaces) {
      const p = new ui.Palette(theme, colors),
        before = JSON.stringify(p.roles),
        c = new ui.Canvas(26, 10, p);
      c.write(0, 0, "Outside");
      new ui.Surface(surface).draw(c, ui.rect(1, 1, 24, 8), (child) => {
        assert.equal(child.surfaceRole, surface);
        new ui.Badge({ label: "Text" }).draw(child, ui.rect(0, 0, 20, 1));
        new ui.Chip({
          id: "off",
          label: "Disabled",
          state: { disabled: true },
        }).draw(child, ui.rect(0, 1, 20, 1));
        new ui.Help([{ key: "x", text: "Help" }]).draw(
          child,
          ui.rect(0, 2, 20, 1),
        );
        child.panel(ui.rect(0, 3, 20, 3), "Panel", true);
        child.write(0, 6, "Selection", "selection");
        new ui.Container([{ id: "body" }]).draw(
          child,
          ui.rect(20, 0, 2, 2),
          (id, inner, focused) => inner.write(0, 0, "OK"),
        );
        child.writeStyle(0, 7, "Raw", child.palette.style("body"));
      });
      const bg = p.style(surface).background;
      for (const y of [1, 2, 3, 4, 5, 6])
        for (let x = 1; x < 21; x++)
          assert.equal(c.data[y][x].style.background, bg);
      assert.equal(
        c.data[7][1].style.background,
        p.style("selection").background,
      );
      assert.equal(c.data[1][21].style.background, bg);
      assert.deepEqual(c.data[8][1].style, p.style("body"));
      assert.equal(c.lines()[0], "Outside" + " ".repeat(19));
      assert.equal(JSON.stringify(p.roles), before);
      for (const name of ["selected", "edited"]) {
        const state = new ui.ControlState({ [name]: true });
        assert.deepEqual(
          p.controlOnSurface(state, surface),
          p.style(state.role),
        );
      }
      assert.equal(
        p.controlOnSurface(
          new ui.ControlState({ disabled: true, selected: true }),
          surface,
          true,
        ).underline,
        false,
      );
      assert.equal(p.textOnSurface("disabled", surface, true).underline, false);
      for (const role of f.explicit_roles) {
        const raw = new ui.Canvas(2, 1, p, surface);
        raw.write(0, 0, "X", role);
        assert.deepEqual(raw.data[0][0].style, p.style(role));
      }
      const original = c.ansi();
      assert.throws(() =>
        new ui.Surface(surface).draw(c, ui.rect(1, 1, 24, 8), (child) => {
          child.write(0, 0, "changed");
          throw new Error("host");
        }),
      );
      assert.equal(c.ansi(), original);
    }
console.log(
  "Actual surfaces, plain/control contrast, explicit state backgrounds, nested clipping and exact raw styles passed",
);

{
  const canvas = new ui.Canvas(2, 1);
  const style = canvas.palette.style("body");
  const original = { ...style };
  canvas.writeStyle(0, 0, "X", style);
  style.background = "1";
  assert.deepEqual(canvas.data[0][0].style, original);
}
