package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.util.List;
final class DocumentHost {
  private final boolean en, syntaxDemo;
  private boolean syntaxEnabled, syntaxFailed;
  private int syntaxCalls;
  private Rect area = new Rect(0, 0, 0, 0);
  private final TextDocument document;
  private String word(String ko, String eng) {
    return en ? eng : ko;
  }
  DocumentHost(boolean en, boolean ascii) {
    this(en, ascii, false);
  }
  DocumentHost(boolean en, boolean ascii, boolean syntax) {
    this.en = en;
    this.syntaxDemo = syntax;
    String literal = word("문서 편집 예제\n한글 é 界 문장을 좁은 화면에서도 "
                          + "확인합니다.\n[error]태그도 원문 그대로입니다.[/]\n마지막 줄입니다.",
        "Document viewer/editor\n"
            + (ascii ? "Literal ASCII text with a long wrapped line."
                     : "Unicode é 界 with a long wrapped line.")
            + "\n[error]Tags remain literal text.[/]\nFinal line.");
    String sql = "SELECT COUNT(*) AS total,\n       CAST(:id AS NUMBER), NVL(:name, '"
        + (en && ascii ? "sample"
                : en   ? "é 界"
                       : "한글 é 界")
        + "')\nFROM sample_table\nWHERE id >= 1.2e-3D; -- "
        + word("실행하지 않는 견본", "Example only");
    document = TextDocument.editor(syntax ? sql : literal);
    document.wrap = true;
    document.buffer.select(0, 0);
    if (syntax)
      enableSyntax();
    else
      document.setSyntax(List.of(new DocumentSpan(0, 2, "info")));
  }
  private void enableSyntax() {
    syntaxFailed = false;
    document.setSyntaxAnalyzer((text, request) -> {
      syntaxCalls++;
      if (syntaxFailed)
        throw new IllegalArgumentException("sample analysis failure");
      return new SQLAnalyzer().analyzeSyntax(text, request);
    });
    syntaxEnabled = true;
  }
  void draw(Canvas c, Rect a, boolean ascii) {
    area = new Rect(a.x(), a.y(), a.width(), Math.max(0, a.height() - 2));
    var d = document;
    d.draw(c, area, true, ascii);
    String status = (d.buffer.state.readOnly ? word("보기", "Viewer") : word("편집", "Editor"))
        + " | " + word("줄바꿈 ", "Wrap ") + (d.wrap ? "on" : "off") + " | "
        + word("줄 번호 ", "Numbers ") + (d.lineNumbers ? "on" : "off") + " | "
        + word("비활성 ", "Disabled ") + (d.buffer.state.disabled ? "on" : "off");
    if (syntaxDemo)
      status = word("구문 ", "Syntax ")
          + (d.syntaxError() != null ? "error"
                  : syntaxEnabled    ? "on"
                                     : "off")
          + " | " + word("분석 ", "Calls ") + syntaxCalls + " | " + status;
    if (a.height() >= 2)
      c.write(a.x(), a.y() + a.height() - 2, status, "hint", false, a.width());
    if (a.height() > 0)
      c.write(a.x(), a.y() + a.height() - 1,
          syntaxDemo ? word("a 구문 전환 | f 실패 | w 줄바꿈 | x 비활성",
                           "a analyzer | f failure | w wrap | x disabled")
                     : word("w 줄바꿈 | n 번호 | v 보기 | s 검색 | x 비활성 | m 마크업",
                           "w wrap | n numbers | v viewer | s search | x disabled | m markup"),
          "hint", false, a.width());
  }
  void handle(String action, String text) {
    String cmd = action.equals("insert") ? text : action;
    var d = document;
    if (cmd.equals("click")) {
      String[] p = text.split(" ");
      if (p.length == 2)
        try {
          pointer(Integer.parseInt(p[0]), Integer.parseInt(p[1]), 0);
        } catch (NumberFormatException ignored) {
        }
      return;
    }
    if (syntaxDemo && cmd.equals("a")) {
      if (syntaxEnabled) {
        d.setSyntaxAnalyzer(null);
        syntaxEnabled = false;
      } else
        enableSyntax();
    } else if (syntaxDemo && cmd.equals("f")) {
      if (d.buffer.state.readOnly || d.buffer.state.disabled)
        return;
      if (syntaxFailed)
        enableSyntax();
      else if (syntaxEnabled) {
        syntaxFailed = true;
        d.handle("insert", " ");
      }
    } else
      switch (cmd) {
        case "w" -> {
          d.wrap = !d.wrap;
          d.revealCursor();
        }
        case "n" -> {
          d.lineNumbers = !d.lineNumbers;
          d.revealCursor();
        }
        case "v" -> d.buffer.state.readOnly = !d.buffer.state.readOnly;
        case "x" -> d.buffer.state.disabled = !d.buffer.state.disabled;
        case "s" ->
          d.setSearchMatches(d.searchMatches().isEmpty()
                  ? List.of(new DocumentRange(0, Math.min(2, graphemes(d.buffer.value()).size())))
                  : List.of());
        case "m" -> {
          syntaxEnabled = false;
          d.setMarkup(word("[info]명시적 마크업[/]\n[[error]는 리터럴입니다.",
              "[info]Explicit markup[/]\n[[error] stays literal."));
          d.buffer.select(0, 0);
        }
        default -> d.handle(action.equals("activate") ? "newline" : action, text);
      }
  }
  void pointer(int x, int y, int button) {
    if (button == 0 && area.contains(x, y))
      document.click(x - area.x(), y - area.y(), area.width(), area.height());
  }
}
