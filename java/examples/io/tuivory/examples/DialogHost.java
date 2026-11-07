package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.util.List;
/** The host owns visibility, modal focus and acceptance of action requests. */
final class DialogHost {
  private final boolean en;
  private boolean opened, disabled;
  private final Focus focus = new Focus("root", List.of(new FocusTarget("editor")));
  private final Text editor;
  private final Dialog dialog;
  private Rect card = new Rect(0, 0, 0, 0), area = card;
  private String status;
  private String word(String ko, String eng) {
    return en ? eng : ko;
  }
  private List<DialogButton> buttons() {
    return List.of(new DialogButton("retry", word("작업 다시 시도", "Retry operation")),
        new DialogButton("settings", word("연결 설정 열기", "Open settings")),
        new DialogButton("cancel", word("취소", "Cancel"), disabled));
  }
  DialogHost(boolean en) {
    this.en = en;
    editor = new Text(word("대화상자를 닫으면 편집합니다.", "Close the dialog to edit this text."));
    dialog = new Dialog(word("다시 연결", "Reconnect"),
        word("작업을 다시 시도할까요?\n내용과 실행은 앱이 결정합니다.",
            "Retry the operation?\nThe host supplies content and actions."),
        buttons(), "cancel");
    status = word("아직 실행하지 않았습니다.", "No action accepted.");
    open();
  }
  private void open() {
    if (!opened) {
      focus.open("dialog", List.of(new FocusTarget("buttons")));
      opened = true;
    }
    dialog.focus("cancel");
  }
  private void accept(Event e) {
    if (e.kind().equals("activate") || e.kind().equals("cancel")) {
      status = word("앱이 수락한 요청: ", "Host accepted: ") + e.id();
      opened = false;
      focus.close("dialog");
      card = new Rect(0, 0, 0, 0);
    }
  }
  void draw(Canvas c, Rect a, boolean ascii) {
    area = a;
    editor.draw(c, new Rect(a.x(), a.y(), a.width(), Math.min(2, a.height())), !opened);
    String under = (ascii ? ":" : en ? "界" : "가").repeat(a.width());
    for (int y = a.y() + 2; y < a.y() + Math.max(0, a.height() - 2); y++)
      c.write(a.x(), y, under, "hint", false, a.width());
    if (a.height() >= 2)
      c.write(a.x(), a.y() + a.height() - 2, status, "hint", false, a.width());
    if (a.height() > 0)
      c.write(a.x(), a.y() + a.height() - 1,
          word("m 열기 | x 취소 비활성 전환", "m reopen | x toggle Cancel disabled"), "hint", false,
          a.width());
    if (opened) {
      int w = Math.min(41, a.width()), h = Math.min(12, Math.max(0, a.height() - 2));
      card = new Shadow(new ShadowOptions("auto"))
                 .draw(c,
                     new Rect(a.x() + (a.width() - w) / 2,
                         a.y() + Math.max(0, (a.height() - h) / 2 - 1), w, h),
                     child
                     -> dialog.draw(child, new Rect(0, 0, child.width, child.height), true, ascii),
                     ascii)
                 .card();
    }
  }
  void handle(String action, String text) {
    String cmd = action.equals("insert") ? text : action;
    if (cmd.equals("click")) {
      String[] p = text.split(" ");
      if (p.length == 2)
        try {
          pointer(Integer.parseInt(p[0]), Integer.parseInt(p[1]), 0);
        } catch (NumberFormatException ignored) {
        }
      return;
    }
    if (cmd.equals("m"))
      open();
    else if (cmd.equals("x")) {
      disabled = !disabled;
      dialog.setButtons(buttons());
    } else if (opened)
      accept(dialog.handle(action.equals("tab") ? "next" : action));
    else
      editor.handle(action.equals("activate") ? "newline" : action, text);
  }
  void pointer(int x, int y, int button) {
    if (button != 0)
      return;
    if (opened) {
      if (card.contains(x, y))
        accept(dialog.click(x - card.x(), y - card.y()));
    } else if (area.contains(x, y))
      editor.click(x - area.x(), y - area.y(), area.width(), Math.min(2, area.height()), false);
  }
}
