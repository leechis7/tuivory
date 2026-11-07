package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.util.List;
final class DocumentHost {
  private final boolean en;
  private Rect area = new Rect(0, 0, 0, 0);
  private final TextDocument document;
  private String word(String ko, String eng) {
    return en ? eng : ko;
  }
  DocumentHost(boolean en, boolean ascii) {
    this.en = en;
    document = TextDocument.editor(
        word("문서 편집 예제\n한글 é 界 문장을 좁은 화면에서도 확인합니다.\n[error]태그도 원문 "
             + "그대로입니다.[/]\n마지막 줄입니다.",
            "Document viewer/editor\n"
                + (ascii ? "Literal ASCII text with a long wrapped line."
                         : "Unicode é 界 with a long wrapped line.")
                + "\n[error]Tags remain literal text.[/]\nFinal line."));
    document.wrap = true;
    document.buffer.select(0, 0);
    document.setSyntax(List.of(new DocumentSpan(0, 2, "info")));
  }
  void draw(Canvas c, Rect a, boolean ascii) {
    area = new Rect(a.x(), a.y(), a.width(), Math.max(0, a.height() - 2));
    var d = document;
    d.draw(c, area, true, ascii);
    String status = (d.buffer.state.readOnly ? word("보기", "Viewer") : word("편집", "Editor"))
        + " | " + word("줄바꿈 ", "Wrap ") + (d.wrap ? "on" : "off") + " | "
        + word("줄 번호 ", "Numbers ") + (d.lineNumbers ? "on" : "off") + " | "
        + word("비활성 ", "Disabled ") + (d.buffer.state.disabled ? "on" : "off");
    if (a.height() >= 2)
      c.write(a.x(), a.y() + a.height() - 2, status, "hint", false, a.width());
    if (a.height() > 0)
      c.write(a.x(), a.y() + a.height() - 1,
          word("w 줄바꿈 | n 번호 | v 보기 | s 검색 | x 비활성 | m 마크업",
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
