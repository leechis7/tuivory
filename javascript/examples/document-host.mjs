import * as ui from "../dist/index.js";
export class DocumentDemo {
  constructor(en = false, ascii = false) {
    this.en = en;
    this.area = ui.rect();
    this.document = ui.TextDocument.editor(
      this.word(
        "문서 편집 예제\n한글 é 界 문장을 좁은 화면에서도 확인합니다.\n[error]태그도 원문 그대로입니다.[/]\n마지막 줄입니다.",
        "Document viewer/editor\n" +
          (ascii
            ? "Literal ASCII text with a long wrapped line."
            : "Unicode é 界 with a long wrapped line.") +
          "\n[error]Tags remain literal text.[/]\nFinal line.",
      ),
    );
    this.document.wrap = true;
    this.document.buffer.select(0, 0);
    this.document.setSyntax([{ start: 0, end: 2, role: "info" }]);
  }
  word(ko, en) {
    return this.en ? en : ko;
  }
  draw(c, a, ascii) {
    this.area = ui.rect(a.x, a.y, a.width, Math.max(0, a.height - 2));
    const d = this.document;
    d.draw(c, this.area, true, ascii);
    const status =
      (d.buffer.readOnly
        ? this.word("보기", "Viewer")
        : this.word("편집", "Editor")) +
      " | " +
      this.word("줄바꿈 ", "Wrap ") +
      (d.wrap ? "on" : "off") +
      " | " +
      this.word("줄 번호 ", "Numbers ") +
      (d.lineNumbers ? "on" : "off") +
      " | " +
      this.word("비활성 ", "Disabled ") +
      (d.buffer.disabled ? "on" : "off");
    if (a.height >= 2)
      c.write(a.x, a.y + a.height - 2, status, "hint", false, a.width);
    if (a.height)
      c.write(
        a.x,
        a.y + a.height - 1,
        this.word(
          "w 줄바꿈 | n 번호 | v 보기 | s 검색 | x 비활성 | m 마크업",
          "w wrap | n numbers | v viewer | s search | x disabled | m markup",
        ),
        "hint",
        false,
        a.width,
      );
  }
  handle(action, text = "") {
    const command = action === "insert" ? text : action,
      d = this.document;
    if (command === "w") {
      d.wrap = !d.wrap;
      d.revealCursor();
    } else if (command === "n") {
      d.lineNumbers = !d.lineNumbers;
      d.revealCursor();
    } else if (command === "v") d.buffer.readOnly = !d.buffer.readOnly;
    else if (command === "x") d.buffer.disabled = !d.buffer.disabled;
    else if (command === "s")
      d.setSearchMatches(
        d.searchMatches.length
          ? []
          : [
              {
                start: 0,
                end: Math.min(2, ui.graphemes(d.buffer.value).length),
              },
            ],
      );
    else if (command === "m") {
      d.setMarkup(
        this.word(
          "[info]명시적 마크업[/]\n[[error]는 리터럴입니다.",
          "[info]Explicit markup[/]\n[[error] stays literal.",
        ),
      );
      d.buffer.select(0, 0);
    } else d.handle(action === "activate" ? "newline" : action, text);
  }
  pointer(x, y, button) {
    const a = this.area;
    if (
      button === 0 &&
      x >= a.x &&
      y >= a.y &&
      x < a.x + a.width &&
      y < a.y + a.height
    )
      this.document.click(x - a.x, y - a.y, a.width, a.height);
  }
}
