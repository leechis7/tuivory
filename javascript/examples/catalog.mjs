#!/usr/bin/env node
import { SurfaceDemo } from "./surface-host.mjs";
import { ContainerDemo } from "./container-host.mjs";
import * as ui from "../dist/index.js";
import { MenuDemo } from "./menu-host.mjs";
import { FeedbackDemo } from "./feedback-host.mjs";
import { LayoutDemo } from "./layout-host.mjs";
import { stdin, stdout, argv } from "node:process";
import { StringDecoder } from "node:string_decoder";
const args = argv.slice(2);
const value = (key, fallback) => {
  const i = args.indexOf(key);
  return i >= 0 ? args[i + 1] : fallback;
};
if (args.includes("--help")) {
  console.log(
    "--demo tree|workspace|text|form|list|picker|menu|context-menu|feedback|layout|container|surface --lang ko|en --theme dark|light|blackwhite --colors 8|16|256|truecolor --ascii --snapshot",
  );
  process.exit(0);
}
const surfaceDemo = value("--demo", "tree") === "surface";
const containerDemo = value("--demo", "tree") === "container";
const layoutDemo = value("--demo", "tree") === "layout";
const feedbackDemo = value("--demo", "tree") === "feedback";
const menuDemo = ["menu", "context-menu"].includes(value("--demo", "tree"));
const workspace = value("--demo", "tree") === "workspace";
const textDemo = value("--demo", "tree") === "text";
const formDemo = value("--demo", "tree") === "form";
const listDemo = value("--demo", "tree") === "list",
  pickerDemo = value("--demo", "tree") === "picker";
if (
  !layoutDemo &&
  !containerDemo &&
  !surfaceDemo &&
  !feedbackDemo &&
  !menuDemo &&
  !workspace &&
  !textDemo &&
  !formDemo &&
  !listDemo &&
  !pickerDemo &&
  value("--demo", "tree") !== "tree"
)
  throw new Error(
    "Supported demos: tree, workspace, text, form, list, picker, menu, context-menu, feedback, layout, container, surface",
  );
const en = value("--lang", "ko") === "en",
  ascii = args.includes("--ascii");
const layoutHost = new LayoutDemo(en);
const containerHost = new ContainerDemo(en, ascii);
const surfaceHost = new SurfaceDemo(en);
const feedbackHost = new FeedbackDemo(en);
const menuHost = new MenuDemo(en, value("--demo", "tree") === "context-menu");
const text = new ui.Text(
  en
    ? ascii
      ? "Grapheme text\nEdit with real cursor."
      : "Unicode é 界\nEdit with real cursor."
    : "한글 é 界\n여러 줄을 편집합니다.",
);
const form = new ui.Form([
  {
    id: "name",
    label: en ? "Name" : "이름",
    value: en ? "Input" : "한글 입력",
    required: true,
  },
  {
    id: "password",
    kind: "password",
    label: en ? "Password" : "비밀번호",
    value: "example",
  },
  {
    id: "off",
    kind: "checkbox",
    label: en ? "Disabled" : "비활성",
    state: { disabled: true },
  },
  {
    id: "mode",
    kind: "select",
    label: en ? "Mode" : "모드",
    choice: "a",
    options: [
      { id: "a", label: en ? "Default" : "기본" },
      { id: "off", label: en ? "Unavailable" : "사용 불가", disabled: true },
      { id: "b", label: en ? "Alternative" : "다른 값" },
    ],
  },
  {
    id: "apply",
    kind: "button",
    label: en ? "Apply" : "적용",
    action: "submit",
  },
]);
const collectionItems = [
  { id: "group", label: en ? "Languages" : "지원 언어", separator: true },
  {
    id: "go",
    label: "Go",
    secondary: en ? "Static package" : "정적 패키지",
    icon: "◆",
    ascii_icon: "G",
    shortcut: "G",
  },
  { id: "off", label: en ? "Disabled" : "비활성", disabled: true },
  {
    id: "rust",
    label: "Rust",
    secondary: en ? "Independent implementation" : "독립 구현",
    icon: "◆",
    ascii_icon: "R",
    shortcut: "R",
  },
  {
    id: "docs",
    label: en ? "Documentation" : "문서",
    secondary: en ? "Korean and English" : "한글·영어",
    icon: "◇",
    ascii_icon: "D",
  },
];
const list = new ui.List(collectionItems),
  picker = new ui.SearchPicker(collectionItems);
picker.handle("open");
list.empty = picker.list.empty = en ? "(empty)" : "항목 없음";
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
const tabs = new ui.Tabs([
  { id: "overview", title: en ? "Overview" : "개요" },
  {
    id: "draft",
    title: en ? "Draft document" : "초안 문서",
    edited: true,
    closable: true,
  },
  { id: "disabled", title: en ? "Disabled" : "비활성", disabled: true },
]);
const split = new ui.Split(16, 20, 24);
let tabFocus = false;
let treeArea = ui.rect();
function workspaceDraw(c, area) {
  tabs.draw(c, ui.rect(area.x, area.y, area.width, 1), tabFocus);
  ui.pathRuns(
    [
      { id: "root", label: en ? "Workspace" : "작업 공간" },
      { id: "current", label: en ? "Components" : "컴포넌트" },
    ],
    area.width,
  ).draw(c, ui.rect(area.x, area.y + 1, area.width, 1));
  const layout = split.layout(area.width),
    body = Math.max(0, area.height - 3);
  let right = ui.rect(area.x, area.y + 2, area.width, body);
  treeArea = ui.rect();
  if (!layout.compact) {
    const left = c.panel(
      ui.rect(area.x, area.y + 2, layout.first, body),
      en ? "Explorer" : "탐색",
      !tabFocus,
      ascii,
    );
    treeArea = left;
    tree.draw(c, left, !tabFocus, ascii);
    for (let y = 0; y < body; y++)
      c.write(
        area.x + layout.first,
        area.y + 2 + y,
        ascii ? "|" : "│",
        "focus.border",
      );
    right = ui.rect(area.x + layout.first + 1, area.y + 2, layout.second, body);
  }
  right = c.panel(right, en ? "Content" : "내용", false, ascii);
  c.write(
    right.x,
    right.y,
    en ? "Selected tab" : "선택한 탭",
    "hint",
    false,
    right.width,
  );
  c.write(
    right.x,
    right.y + 1,
    tabs.items.find((t) => t.id === tabs.active)?.title ?? "",
    "body",
    false,
    right.width,
  );
  ui.statusLine(
    [
      {
        id: "ready",
        text: en ? "Ready" : "준비",
        role: "success",
        priority: 10,
      },
      {
        id: "keys",
        text: en ? "Tab focus | < > resize" : "Tab 포커스 | < > 크기",
        role: "hint",
        priority: 1,
      },
    ],
    area.width,
  ).draw(c, ui.rect(area.x, area.y + area.height - 1, area.width, 1));
}
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
  if (surfaceDemo) surfaceHost.draw(c, area, ascii);
  else if (containerDemo) containerHost.draw(c, area, ascii);
  else if (layoutDemo) layoutHost.draw(c, area, ascii);
  else if (feedbackDemo) feedbackHost.draw(c, area, ascii);
  else if (menuDemo) menuHost.draw(c, area, ascii);
  else if (listDemo) list.draw(c, area, true, ascii);
  else if (pickerDemo) picker.draw(c, area, true, ascii);
  else if (formDemo) form.draw(c, area);
  else if (textDemo) text.draw(c, area);
  else if (workspace) workspaceDraw(c, area);
  else tree.draw(c, area, true, ascii);
  c.write(
    0,
    height - 1,
    (surfaceDemo
      ? en
        ? "Ctrl+Q quit | s surface"
        : "Ctrl+Q 종료 | s 바탕 변경"
      : containerDemo
        ? en
          ? "Ctrl+Q quit | m popup | h/l scroll | Tab focus"
          : "Ctrl+Q 종료 | m 팝업 | h/l 스크롤 | Tab 포커스"
        : layoutDemo
          ? en
            ? "Ctrl+Q quit | x/Enter remove filter | d density | click x"
            : "Ctrl+Q 종료 | x/Enter 필터 제거 | d 간격 | x 클릭"
          : feedbackDemo
            ? en
              ? "Ctrl+Q quit | Enter retry | Del dismiss | t expire | c cancel"
              : "Ctrl+Q 종료 | Enter 재시도 | Del 닫기 | t 만료 | c 취소"
            : en
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
let escapeTimer;
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
      clearTimeout(escapeTimer);
      pending += decoder.write(chunk);
      while (pending) {
        if (pending[0] === "\x11" || pending[0] === "\x03") {
          restore();
          process.exit(0);
        }
        // A queued Escape must not swallow a following control key or UTF-8 text.
        if (
          pending[0] === "\x1b" &&
          pending.length > 1 &&
          !["[", "O"].includes(pending[1])
        ) {
          pending = pending.slice(1);
          if (containerDemo) containerHost.handle("cancel");
          else if (menuDemo) menuHost.handle("cancel");
          else if (pickerDemo) picker.handle("cancel");
          else if (formDemo) form.handle("cancel");
          continue;
        }
        const mouse = pending.match(/^\x1b\[<(\d+);(\d+);(\d+)([Mm])/);
        if (mouse) {
          pending = pending.slice(mouse[0].length);
          const x = Number(mouse[2]) - 1,
            y = Number(mouse[3]) - 1;
          if (
            (menuDemo ||
              feedbackDemo ||
              layoutDemo ||
              containerDemo ||
              surfaceDemo) &&
            mouse[4] === "M"
          ) {
            (surfaceDemo
              ? surfaceHost
              : containerDemo
                ? containerHost
                : layoutDemo
                  ? layoutHost
                  : feedbackDemo
                    ? feedbackHost
                    : menuHost
            ).pointer(x, y, Number(mouse[1]));
          } else if (
            mouse[4] === "M" &&
            Number(mouse[1]) === 0 &&
            x >= area.x &&
            x < area.x + area.width &&
            y >= area.y &&
            y < area.y + area.height
          ) {
            if (listDemo) list.click(x - area.x, y - area.y, area.height);
            else if (pickerDemo)
              picker.click(x - area.x, y - area.y, area.height);
            else if (formDemo) form.click(x - area.x, y - area.y, area.height);
            else if (textDemo)
              text.click(x - area.x, y - area.y, area.width, area.height);
            else if (workspace && y === area.y) {
              tabFocus = true;
              tabs.click(x - area.x, area.width);
            } else if (
              workspace &&
              x >= treeArea.x &&
              x < treeArea.x + treeArea.width &&
              y >= treeArea.y &&
              y < treeArea.y + treeArea.height
            ) {
              tabFocus = false;
              tree.click(x - treeArea.x, y - treeArea.y, treeArea.height);
            } else if (!workspace)
              tree.click(x - area.x, y - area.y, area.height);
          }
          continue;
        }
        const keys = {
          "\x1b[21~": "f10",
          "\x1b[21;2~": "shift_f10",
          "\x1b[A": "up",
          "\x1b[B": "down",
          "\x1b[C": "right",
          "\x1b[D": "left",
          "\x1b[H": "home",
          "\x1b[F": "end",
          "\x1b[5~": "page_up",
          "\x1b[6~": "page_down",
          "\r": "activate",
          "\x7f": "backspace",
          "\x1b[3~": "delete",
          "\x01": "select_all",
          "\x1a": "undo",
          "\x19": "redo",
          " ": "toggle",
        };
        const key = Object.keys(keys).find((k) => pending.startsWith(k));
        if (key) {
          if (
            menuDemo ||
            feedbackDemo ||
            layoutDemo ||
            containerDemo ||
            surfaceDemo
          )
            (surfaceDemo
              ? surfaceHost
              : containerDemo
                ? containerHost
                : layoutDemo
                  ? layoutHost
                  : feedbackDemo
                    ? feedbackHost
                    : menuHost
            ).handle(
              keys[key] === "toggle" ? "insert" : keys[key],
              keys[key] === "toggle" ? " " : "",
            );
          else if (listDemo)
            list.handle(
              keys[key] === "toggle" ? "select" : keys[key],
              area.height,
            );
          else if (pickerDemo)
            picker.handle(
              keys[key] === "toggle" ? "insert" : keys[key],
              keys[key] === "toggle" ? " " : "",
              area.height,
            );
          else if (formDemo)
            form.handle(
              keys[key] === "toggle" ? "insert" : keys[key],
              keys[key] === "toggle" ? " " : "",
            );
          else if (textDemo)
            text.handle(
              keys[key] === "activate"
                ? "newline"
                : keys[key] === "toggle"
                  ? "insert"
                  : keys[key],
              keys[key] === "toggle" ? " " : "",
            );
          else if (workspace && tabFocus)
            tabs.handle(
              { left: "previous", right: "next" }[keys[key]] ?? keys[key],
            );
          else
            tree.handle(keys[key], workspace ? treeArea.height : area.height);
          pending = pending.slice(key.length);
          continue;
        }
        if (containerDemo && pending.startsWith("\t")) {
          containerHost.handle("next");
          pending = pending.slice(1);
          continue;
        }
        if (formDemo && pending.startsWith("\t")) {
          form.handle("next");
          pending = pending.slice(1);
          continue;
        }
        if (workspace && pending.startsWith("\t")) {
          tabFocus = !tabFocus;
          pending = pending.slice(1);
          continue;
        }
        if (workspace && ["<", ">"].includes(pending[0])) {
          split.resize(
            area.width,
            split.preferred + (pending[0] === "<" ? -1 : 1),
          );
          pending = pending.slice(1);
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
        if (
          (surfaceDemo ||
            containerDemo ||
            layoutDemo ||
            feedbackDemo ||
            menuDemo ||
            textDemo ||
            formDemo ||
            pickerDemo) &&
          pending.codePointAt(0) >= 32 &&
          pending[0] !== "\x1b"
        ) {
          const cp = String.fromCodePoint(pending.codePointAt(0));
          (surfaceDemo
            ? surfaceHost
            : containerDemo
              ? containerHost
              : layoutDemo
                ? layoutHost
                : feedbackDemo
                  ? feedbackHost
                  : menuDemo
                    ? menuHost
                    : pickerDemo
                      ? picker
                      : formDemo
                        ? form
                        : text
          ).handle("insert", cp);
          pending = pending.slice(cp.length);
        } else pending = pending.slice(1);
      }
      if (pending === "\x1b")
        escapeTimer = setTimeout(() => {
          if (pending === "\x1b") {
            pending = "";
            if (containerDemo) containerHost.handle("cancel");
            else if (menuDemo) menuHost.handle("cancel");
            else if (pickerDemo) picker.handle("cancel");
            else if (formDemo) form.handle("cancel");
            draw();
          }
        }, 100);
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
