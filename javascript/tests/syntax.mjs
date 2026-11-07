import assert from "node:assert/strict";
import fs from "node:fs";
import * as ui from "../dist/index.js";
const cases = ["syntax-cases.json", "syntax-extra-cases.json"].flatMap(
  (name) =>
    JSON.parse(
      fs.readFileSync(new URL("../../design/" + name, import.meta.url)),
    ).cases,
);
const analyzer = new ui.SQLAnalyzer();
for (const f of cases) {
  const a = analyzer.analyzeSyntax(f.source, f);
  ui.validateSyntaxAnalysis(a, f.source);
  assert.deepEqual(a.tokens, f.tokens, f.name);
}
assert.throws(() => analyzer.analyzeSyntax("x", { language: "python" }));
let calls = 0,
  fail = false;
const callback = (text, request) => {
  calls++;
  if (fail) throw new Error("sample failure");
  return analyzer.analyzeSyntax(text, request);
};
const d = ui.TextDocument.editor("SELECT 1");
d.setSyntaxAnalyzer(callback);
assert.equal(calls, 1);
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"])
    d.draw(
      new ui.Canvas(40, 4, new ui.Palette(theme, colors)),
      ui.rect(0, 0, 40, 4),
    );
d.handle("scroll_down");
d.layout(12, 2);
assert.equal(calls, 1);
d.handle("insert", " ");
d.layout(40, 4);
assert.equal(calls, 2);
const before = d.buffer.value,
  cursor = d.buffer.cursor;
fail = true;
d.handle("insert", "X");
assert.equal(calls, 3);
assert.deepEqual(d.syntax, []);
assert.match(d.syntaxError, /sample failure/);
d.buffer.secret = true;
assert.equal(d.syntaxError, undefined);
d.buffer.secret = false;
d.layout(40, 4);
assert.equal(calls, 3);
assert.equal(d.handle("undo").kind, "change");
assert.equal(d.buffer.value, before);
assert.equal(d.buffer.cursor, cursor);
assert.equal(calls, 4);
fail = false;
d.setSyntaxAnalyzer(callback);
assert.equal(calls, 5);
assert.equal(d.syntaxError, undefined);
d.buffer.secret = true;
d.layout(40, 4);
assert.deepEqual(d.syntax, []);
assert.throws(() => d.setSyntaxAnalyzer(callback));
assert.equal(calls, 5);
d.buffer.secret = false;
d.layout(40, 4);
assert.equal(calls, 6);
d.setSyntaxAnalyzer(null);
d.handle("insert", "Z");
d.layout(40, 4);
assert.equal(calls, 6);
assert.deepEqual(d.syntax, []);
const atomic = ui.TextDocument.editor("한é界");
atomic.setSyntax([{ start: 0, end: 3, role: "warning" }]);
const old = atomic.syntax;
assert.throws(() =>
  atomic.setSyntaxAnalyzer(new ui.SQLAnalyzer(), { language: "unknown" }),
);
assert.deepEqual(atomic.syntax, old);
assert.throws(() =>
  atomic.setSyntaxAnalysis({
    source: "wrong",
    language: "sql",
    dialect: "oracle",
    tokens: [],
  }),
);
assert.deepEqual(atomic.syntax, old);
const split = {
  source: atomic.buffer.value,
  language: "custom",
  dialect: "",
  tokens: [{ start: 3, end: 4, role: "keyword" }],
};
ui.validateSyntaxAnalysis(split, atomic.buffer.value);
assert.throws(() => atomic.setSyntaxAnalysis(split));
assert.deepEqual(atomic.syntax, old);
for (const tokens of [
  [{ start: 1, end: 3, role: "keyword" }],
  [
    { start: 0, end: 3, role: "keyword" },
    { start: 2, end: 6, role: "comment" },
  ],
  [{ start: 0, end: 0, role: "number" }],
])
  assert.throws(() =>
    ui.validateSyntaxAnalysis({ ...split, tokens }, atomic.buffer.value),
  );
const tokens = [{ start: 0, end: 3, role: "identifier" }];
atomic.setSyntaxAnalysis({ ...split, tokens });
tokens[0].role = "keyword";
assert.equal(atomic.syntax[0].role, "body");
atomic.handle("insert", "x");
atomic.layout(40, 4);
assert.deepEqual(atomic.syntax, []);
assert.equal(ui.syntaxRoleStyle("macro"), "syntax.function");
assert.equal(ui.syntaxRoleStyle("lifetime"), "syntax.parameter");
const kinds = [
  "keyword",
  "function",
  "type",
  "string",
  "number",
  "comment",
  "parameter",
];
for (const theme of ["dark", "light", "blackwhite"])
  for (const colors of ["8", "16", "256", "truecolor"])
    for (const surface of ["editor", "button.focus"]) {
      const p = new ui.Palette(theme, colors),
        c = new ui.Canvas(12, 4, p, surface);
      kinds.forEach((kind, x) => {
        const s = ui.syntaxStyle(p, "syntax." + kind, surface);
        assert.equal(s.background, p.style(surface).background);
        assert(!s.dim);
        if (theme === "dark" && colors === "8") {
          assert.equal(s.bold, ["keyword", "number"].includes(kind));
          assert.equal(
            s.underline,
            ["keyword", "type", "parameter"].includes(kind),
          );
          assert.equal(s.italic, ["string", "comment"].includes(kind));
          assert(Number(s.foreground) < 8);
        }
        c.writeStyle(x, 0, "X", s, 1);
      });
      const raw = {
          foreground: "7",
          background: p.style(surface).background,
          bold: false,
          dim: false,
          underline: false,
          italic: true,
        },
        normal = { ...raw, italic: false };
      c.writeStyle(0, 1, "I", raw, 1);
      c.writeStyle(1, 1, "N", normal, 1);
      c.blit(c, ui.rect(0, 1, 2, 1), 0, 2);
      assert(c.data[2][0].style.italic);
      assert(!c.data[2][1].style.italic);
      c.writeStyle(8, 2, "I", raw, 1);
      c.writeStyle(9, 2, "N", normal, 1);
      new ui.Shadow(new ui.ShadowOptions("dim")).draw(
        c,
        ui.rect(7, 0, 5, 3),
        () => {},
        false,
      );
      assert(c.data[2][8].style.dim && c.data[2][8].style.italic);
      assert(c.data[2][9].style.dim && !c.data[2][9].style.italic);
      assert.match(c.ansi(), /;3/);
    }
let detachedCalls = 0;
const markup = ui.TextDocument.editor("SELECT 1");
markup.setSyntaxAnalyzer((text, request) => {
  detachedCalls++;
  return analyzer.analyzeSyntax(text, request);
});
markup.setMarkup("[info]literal[/]");
markup.handle("insert", "x");
assert.equal(detachedCalls, 1);
console.log(
  "31 shared syntax cases, source/callback/secret/atomic bindings and all-palette attribute/copy/Dim cases passed",
);
