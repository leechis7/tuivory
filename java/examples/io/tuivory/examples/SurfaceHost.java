package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.util.List;
final class SurfaceHost {
  private final boolean en;
  private int index = 1;
  private final Text input;
  SurfaceHost(boolean en) {
    this.en = en;
    input = new Text(word("읽기 전용", "Read only"));
    input.state.readOnly = true;
  }
  private String word(String ko, String en) {
    return this.en ? en : ko;
  }
  void draw(Canvas c, Rect area, boolean ascii) {
    String[] roles = {"surface", "editor", "field", "button.focus"};
    new Surface(roles[index])
        .draw(c, new Rect(area.x(), area.y(), area.width(), Math.max(0, area.height() - 1)),
            child -> {
              int w = child.width;
              child.write(0, 0, word("바탕 위 문구", "Body on surface"), "body", false, w);
              child.write(0, 1, word("보조 설명", "Secondary"), "hint", false, w);
              child.write(0, 2, word("정상 상태", "Success"), "success", false, w);
              var off = new Chip("off", word("비활성", "Disabled"));
              off.state.disabled = true;
              off.draw(child, new Rect(0, 3, w, 1));
              var selected = new Badge();
              selected.label = word("선택", "Selected");
              selected.count = 0L;
              selected.state.selected = true;
              selected.draw(child, new Rect(0, 4, w, 1));
              var edited = new Chip("edited", word("수정", "Edited"));
              edited.state.edited = true;
              edited.draw(child, new Rect(0, 5, w, 1));
              input.draw(child, new Rect(0, 6, w, 1), false);
              new Help(List.of(new Shortcut("s", word("바탕 변경", "Change surface"))))
                  .draw(child, new Rect(0, 8, w, 1));
            });
    String[] ko = {"패널", "편집", "입력", "포커스 버튼"},
             en = {"panel", "editor", "field", "focused button"};
    if (area.height() > 0)
      c.write(area.x(), area.y() + area.height() - 1,
          word("바탕: ", "Surface: ") + (this.en ? en[index] : ko[index]), "hint", false,
          area.width());
  }
  void handle(String action, String text) {
    if ((action.equals("insert") ? text : action).equals("s"))
      index = (index + 1) % 4;
  }
}
