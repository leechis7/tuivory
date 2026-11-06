package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.util.List;
final class ContainerHost {
  private final boolean en;
  private boolean opened;
  private int ox, oy;
  private String status = "";
  private final Container base, layers;
  private final Text editor;
  private String word(String ko, String en) {
    return this.en ? en : ko;
  }
  ContainerHost(boolean en, boolean ascii) {
    this.en = en;
    var nav = new LayoutItem("nav");
    nav.track.fixed = 20;
    var editor = new LayoutItem("editor");
    var o = new ContainerOptions();
    o.kind = "row";
    o.gap = 1;
    o.virtualWidth = 96;
    base = new Container(List.of(nav, editor), o);
    base.state.moveFocus(base.items(), false);
    o = new ContainerOptions();
    o.kind = "layers";
    layers = new Container(List.of(new LayoutItem("background")), o);
    this.editor =
        new Text(word("편집 영역 한글 界", ascii ? "Editor area ASCII" : "Editor area Unicode 界"));
  }
  void draw(Canvas c, Rect area, boolean ascii) {
    ox = area.x();
    oy = area.y();
    ChildPainter pane = (id, child, focused) -> {
      var inner = child.panel(new Rect(0, 0, child.width, child.height),
          id.equals("nav") ? word("탐색", "Navigator") : word("편집", "Editor"), focused, ascii);
      if (id.equals("nav"))
        child.write(inner.x(), inner.y(), word("개요", "Overview"), "body", false, inner.width());
      else
        editor.draw(child, inner, focused);
    };
    layers.draw(c, new Rect(area.x(), area.y(), area.width(), Math.max(0, area.height() - 1)),
        (id, child, focused) -> {
          if (id.equals("background"))
            base.draw(child, new Rect(0, 0, child.width, child.height), pane);
          else {
            var inner = child.panel(
                new Rect(0, 0, child.width, child.height), word("팝업", "Modal"), false, ascii);
            child.write(inner.x(), inner.y(), word("배경 입력 차단", "Background input blocked"),
                "body", false, inner.width());
            child.write(inner.x(), inner.y() + 1, word("m / Esc 닫기", "m / Esc close"), "hint",
                false, inner.width());
          }
        });
    if (area.height() > 0)
      c.write(area.x(), area.y() + area.height() - 1,
          status.isEmpty() ? word("스크롤: ", "Scroll: ") + base.scrollX : status, "hint", false,
          area.width());
  }
  void handle(String action, String addition) {
    if (action.equals("click")) {
      var parts = addition.split(" ");
      if (parts.length == 2)
        try {
          pointer(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]), 0);
        } catch (NumberFormatException ignored) {
        }
      return;
    }
    String command = action.equals("insert") ? addition : action;
    if (command.equals("m") || (command.equals("cancel") && opened)) {
      opened = command.equals("m") ? !opened : false;
      var popup = new LayoutItem("popup");
      popup.modal = true;
      popup.centered = true;
      popup.area = new Rect(0, 0, 30, 6);
      layers.setItems(opened ? List.of(new LayoutItem("background"), popup)
                             : List.of(new LayoutItem("background")));
      status = opened ? word("팝업 열림", "Popup open") : word("팝업 닫힘", "Popup closed");
    } else if (!opened) {
      if (command.equals("h") || command.equals("l")) {
        base.scrollX = Math.max(0, base.scrollX + (command.equals("l") ? 4 : -4));
        status = word("스크롤: ", "Scroll: ") + base.scrollX;
      } else if (command.equals("next") || command.equals("previous"))
        base.state.moveFocus(base.items(), command.equals("previous"));
      else if (base.state.focused.equals("editor"))
        editor.handle(action, addition);
    }
  }
  void pointer(int x, int y, int button) {
    if (button == 0 && layers.pointer(x, y, true, true).equals("background"))
      base.pointer(x - ox, y - oy, true, true);
  }
}
