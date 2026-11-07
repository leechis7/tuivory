import * as ui from "../dist/index.js";
export class DocumentDemo {
  constructor(en = false, ascii = false, syntax = false) {
    this.en = en;
    this.area = ui.rect();
    this.syntaxDemo = syntax;
    this.syntaxEnabled = false;
    this.syntaxFailed = false;
    this.syntaxCalls = 0;
    this.analyzer = new ui.SQLAnalyzer();
    const literal = this.word(
      "문서 편집 예제\n한글 é 界 문장을 좁은 화면에서도 확인합니다.\n[error]태그도 원문 그대로입니다.[/]\n마지막 줄입니다.",
      "Document viewer/editor\n" +
        (ascii
          ? "Literal ASCII text with a long wrapped line."
          : "Unicode é 界 with a long wrapped line.") +
        "\n[error]Tags remain literal text.[/]\nFinal line.",
    );
    const sql =
      "SELECT COUNT(*) AS total,\n       CAST(:id AS NUMBER), NVL(:name, '" +
      (en && ascii ? "sample" : en ? "é 界" : "한글 é 界") +
      "')\nFROM sample_table\nWHERE id >= 1.2e-3D; -- " +
      this.word("실행하지 않는 견본", "Example only");
    this.document = ui.TextDocument.editor(syntax ? sql : literal);
    this.document.wrap = true;
    this.document.buffer.select(0, 0);
    if (syntax) this.enableSyntax();
    else this.document.setSyntax([{ start: 0, end: 2, role: "info" }]);
  }
  word(ko, en) {
    return this.en ? en : ko;
  }
  analyze(text, request) {
    this.syntaxCalls++;
    if (this.syntaxFailed) throw new Error("sample analysis failure");
    return this.analyzer.analyzeSyntax(text, request);
  }
  enableSyntax() {
    this.syntaxFailed = false;
    this.document.setSyntaxAnalyzer((text, request) =>
      this.analyze(text, request),
    );
    this.syntaxEnabled = true;
  }
  draw(c, a, ascii) {
    this.area = ui.rect(a.x, a.y, a.width, Math.max(0, a.height - 2));
    const d = this.document;
    d.draw(c, this.area, true, ascii);
    let status =
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
    if (this.syntaxDemo)
      status =
        this.word("구문 ", "Syntax ") +
        (d.syntaxError ? "error" : this.syntaxEnabled ? "on" : "off") +
        " | " +
        this.word("분석 ", "Calls ") +
        this.syntaxCalls +
        " | " +
        status;
    if (a.height >= 2)
      c.write(a.x, a.y + a.height - 2, status, "hint", false, a.width);
    if (a.height)
      c.write(
        a.x,
        a.y + a.height - 1,
        this.syntaxDemo
          ? this.word(
              "a 구문 전환 | f 실패 | w 줄바꿈 | x 비활성",
              "a analyzer | f failure | w wrap | x disabled",
            )
          : this.word(
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
    if (this.syntaxDemo && command === "a") {
      if (this.syntaxEnabled) {
        d.setSyntaxAnalyzer(null);
        this.syntaxEnabled = false;
      } else this.enableSyntax();
    } else if (this.syntaxDemo && command === "f") {
      if (d.buffer.readOnly || d.buffer.disabled) return;
      if (this.syntaxFailed) this.enableSyntax();
      else if (this.syntaxEnabled) {
        this.syntaxFailed = true;
        d.handle("insert", " ");
      }
    } else if (command === "w") {
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
      this.syntaxEnabled = false;
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
