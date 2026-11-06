#!/usr/bin/env node
import * as ui from "../dist/index.js";
import { stdin, stdout, argv } from "node:process";
import { StringDecoder } from "node:string_decoder";
const args = argv.slice(2);
const value = (key, fallback) => {
  const i = args.indexOf(key);
  return i >= 0 ? args[i + 1] : fallback;
};
if (args.includes("--help")) {
  console.log(
    "--demo tree --lang ko|en --theme dark|light|blackwhite --colors 8|16|256|truecolor --ascii --snapshot",
  );
  process.exit(0);
}
if (value("--demo", "tree") !== "tree")
  throw new Error("Only --demo tree is supported");
const en = value("--lang", "ko") === "en",
  ascii = args.includes("--ascii");
let theme = value("--theme", "dark"),
  colors = value("--colors", "256");
const tree = new ui.Tree([
  { id: "root", name: en ? "Workspace" : "작업 공간" },
  { id: "src", name: en ? "Sources" : "소스", parent: "root" },
  { id: "components", name: en ? "Components" : "컴포넌트", parent: "src" },
  { id: "tree", name: en ? "Tree" : "트리", parent: "components" },
  { id: "leaf", name: en ? "Fifth level" : "다섯 단계", parent: "tree" },
  { id: "docs", name: en ? "Documentation" : "문서", parent: "root" },
]);
tree.expanded = new Set(["root", "src", "components", "tree"]);
let area = ui.rect();
function draw(snapshot = false, ansiSnapshot = false) {
  const width = snapshot ? 72 : stdout.columns || 80,
    height = snapshot ? 18 : stdout.rows || 24;
  const c = new ui.Canvas(width, height, new ui.Palette(theme, colors));
  area = c.panel(
    ui.rect(0, 0, width, Math.max(0, height - 1)),
    en ? "Tuivory JavaScript example" : "Tuivory JavaScript 예제",
    true,
    ascii,
  );
  tree.draw(c, area, true, ascii);
  c.write(
    0,
    height - 1,
    (en
      ? "Ctrl+Q quit · arrows navigate · F1 theme · F2 colors"
      : "Ctrl+Q 종료 · 방향키 탐색 · F1 테마 · F2 색상"
    ).replaceAll("·", ascii ? "|" : "·"),
    "hint",
    false,
    width,
  );
  if (snapshot && ansiSnapshot) stdout.write(c.ansi());
  else if (snapshot)
    console.log(JSON.stringify({ lines: c.lines(), cursor: c.cursor }));
  else stdout.write(c.ansi());
}
if (args.includes("--snapshot") || args.includes("--snapshot-ansi")) {
  draw(true, args.includes("--snapshot-ansi"));
  process.exit(0);
}
if (!stdin.isTTY || !stdout.isTTY)
  throw new Error("Interactive example requires a TTY; use --snapshot");
let active = false,
  pending = "";
const decoder = new StringDecoder("utf8");
function restore() {
  if (!active) return;
  active = false;
  try {
    stdout.write("\x1b[0m\x1b[?1000l\x1b[?1006l\x1b[?25h\x1b[?1049l");
  } finally {
    stdin.setRawMode(false);
    stdin.pause();
  }
}
process.once("exit", restore);
for (const signal of ["SIGINT", "SIGTERM"])
  process.once(signal, () => {
    restore();
    process.exit(0);
  });
try {
  stdin.setRawMode(true);
  active = true;
  stdout.write("\x1b[?1049h\x1b[?1000h\x1b[?1006h");
  draw();
  stdout.on("resize", () => draw());
  stdin.on("data", (chunk) => {
    try {
      pending += decoder.write(chunk);
      while (pending) {
        if (pending[0] === "\x11" || pending[0] === "\x03") {
          restore();
          process.exit(0);
        }
        const mouse = pending.match(/^\x1b\[<(\d+);(\d+);(\d+)([Mm])/);
        if (mouse) {
          pending = pending.slice(mouse[0].length);
          const x = Number(mouse[2]) - 1,
            y = Number(mouse[3]) - 1;
          if (
            mouse[4] === "M" &&
            Number(mouse[1]) === 0 &&
            x >= area.x &&
            x < area.x + area.width &&
            y >= area.y &&
            y < area.y + area.height
          )
            tree.click(x - area.x, y - area.y, area.height);
          continue;
        }
        const keys = {
          "\x1b[A": "up",
          "\x1b[B": "down",
          "\x1b[C": "right",
          "\x1b[D": "left",
          "\x1b[H": "home",
          "\x1b[F": "end",
          "\x1b[5~": "page_up",
          "\x1b[6~": "page_down",
          "\r": "activate",
          " ": "toggle",
        };
        const key = Object.keys(keys).find((k) => pending.startsWith(k));
        if (key) {
          tree.handle(keys[key], area.height);
          pending = pending.slice(key.length);
          continue;
        }
        if (pending.startsWith("\x1bOP")) {
          theme = ["dark", "light", "blackwhite"][
            (["dark", "light", "blackwhite"].indexOf(theme) + 1) % 3
          ];
          pending = pending.slice(3);
          continue;
        }
        if (pending.startsWith("\x1bOQ")) {
          colors = ["8", "16", "256", "truecolor"][
            (["8", "16", "256", "truecolor"].indexOf(colors) + 1) % 4
          ];
          pending = pending.slice(3);
          continue;
        }
        if (
          [...Object.keys(keys), "\x1bOP", "\x1bOQ", "\x1b[<"].some(
            (sequence) => sequence.startsWith(pending),
          ) ||
          (pending.startsWith("\x1b[<") && !/[Mm]$/.test(pending))
        )
          break;
        if (
          pending.startsWith("\x1b") &&
          pending.length < 32 &&
          !/[A-Za-z~]$/.test(pending)
        )
          break;
        pending = pending.slice(1);
      }
      draw();
    } catch (error) {
      restore();
      console.error(error);
      process.exitCode = 1;
    }
  });
} catch (error) {
  restore();
  throw error;
}
