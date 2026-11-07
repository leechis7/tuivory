package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.util.ArrayList;
import java.util.List;
/** Example host owns screen composition, global shortcuts, callbacks and scopes. */
final class MenuHost {
  private final boolean en, context, shadowDemo;
  private int shadowIndex;
  private String shadowMode() {
    return shadowDemo ? new String[] {"auto", "solid", "off", "dim"}[shadowIndex] : "off";
  }
  private final Menu menu;
  private final Focus focus = new Focus("root", List.of(new FocusTarget("editor")));
  private final Text editor;
  private Rect area = new Rect(0, 0, 0, 0), bar = area, content = area, editorArea = area,
               anchor = null;
  private String status;
  MenuHost(boolean en, boolean context) {
    this(en, context, false);
  }
  MenuHost(boolean en, boolean context, boolean shadow) {
    this.shadowDemo = shadow;
    this.en = en;
    this.context = context;
    var items = new ArrayList<MenuItem>();
    add(items, "file", en ? "File" : "파일", "", "f", "", false, false);
    add(items, "new", en ? "New document" : "새 문서", "file", "n", "Ctrl+N", false, false);
    add(items, "line", "", "file", "", "", false, true);
    add(items, "off", en ? "Unavailable" : "사용 불가", "file", "", "", true, false);
    add(items, "recent", en ? "Recent documents" : "최근 문서", "file", "r", "", false, false);
    add(items, "a", en ? "Example A" : "예제 A", "recent", "a", "", false, false);
    add(items, "more", en ? "More" : "더 보기", "recent", "m", "", false, false);
    add(items, "b", en ? "Example B" : "예제 B", "more", "b", "", false, false);
    add(items, "edit", en ? "Edit" : "편집", "", "e", "", false, false);
    add(items, "copy", en ? "Copy" : "복사", "edit", "c", "Ctrl+C", false, false);
    menu = new Menu(items);
    menu.backLabel = en ? "Back" : "뒤로";
    menu.emptyLabel = en ? "(empty)" : "항목 없음";
    editor = new Text(
        en ? "Close the menu to edit this text." : "메뉴를 닫으면 여기를 편집할 수 있습니다.");
    status =
        en ? "Clicks outside the popup are blocked." : "팝업 밖의 클릭은 배경에 전달되지 않습니다.";
    open(context ? "" : "file");
  }
  private static void add(List<MenuItem> items, String id, String label, String parent,
      String mnemonic, String shortcut, boolean disabled, boolean separator) {
    var i = new MenuItem(id, label);
    i.parent = parent;
    i.mnemonic = mnemonic;
    i.shortcut = shortcut;
    i.disabled = disabled;
    i.separator = separator;
    items.add(i);
  }
  private void sync(MenuEvent e) {
    if (!menu.opened() && focus.depth() > 0)
      focus.close("popup");
    if (e != null && e.kind().equals("activate"))
      for (var i : menu.items())
        if (i.id.equals(e.id()))
          status = (en ? "Selected: " : "선택: ") + i.label;
  }
  private void open(String id) {
    menu.open(id, "editor");
    if (menu.opened() && focus.depth() == 0)
      focus.open("popup", List.of(new FocusTarget("menu")));
    sync(null);
  }
  void draw(Canvas c, Rect area, boolean ascii) {
    this.area = area;
    bar = new Rect(area.x(), area.y(), area.width(), context ? 0 : 1);
    editorArea = new Rect(area.x(), area.y() + bar.height(), area.width(),
        Math.min(2, Math.max(0, area.height() - bar.height())));
    editor.draw(c, editorArea, !menu.opened());
    String underlay = (ascii ? (shadowDemo ? ":" : ".") : en ? "界" : "가").repeat(area.width());
    for (int y = editorArea.y() + editorArea.height();
        y < area.y() + Math.max(0, area.height() - 2); y++)
      c.write(area.x(), y, underlay, "hint", false, area.width());
    if (bar.height() > 0)
      menu.drawBar(c, bar);
    c.write(
        area.x(), area.y() + Math.max(0, area.height() - 2), status, "hint", false, area.width());
    String footer = shadowDemo
        ? (en ? "Shadow: " + shadowMode() + " | s cycle | d Dim"
              : "그림자: " + new String[] {"자동", "검정", "끄기", "Dim(호환)"}[shadowIndex]
                      + " | s 변경 | d Dim")
        : (en ? "f10 menu | context x y | cancel" : "f10 메뉴 | context x y | cancel");
    c.write(
        area.x(), area.y() + Math.max(0, area.height() - 1), footer, "hint", false, area.width());
    Rect at = anchor != null
        ? anchor
        : new Rect(area.x() + (context ? area.width() / 2 : 1), area.y() + (context ? 5 : 0), 1, 1);
    if (context || anchor != null)
      c.write(at.x(), at.y(), "+", "warning", false, 1);
    if (menu.opened()) {
      int[] size = menu.contentSize();
      var options = new ShadowOptions(shadowMode());
      var place =
          popupPlacement(at, area, Math.min(48, ((size[0] + 5) / 2) * 2), size[1] + 4, options);
      String title = menu.title(),
             caption = title.isEmpty() ? (en ? "Context menu" : "문맥 메뉴") : title;
      Rect[] local = {new Rect(0, 0, 0, 0)};
      var layout = new Shadow(options).draw(c, place.bounds(),
          child
          -> local[0] = menu.drawPopup(
                 child, new Rect(0, 0, child.width, child.height), caption, 1, ascii),
          ascii);
      content = new Rect(layout.card().x() + local[0].x(), layout.card().y() + local[0].y(),
          local[0].width(), local[0].height());

    } else
      content = new Rect(0, 0, 0, 0);
  }
  void handle(String action, String text) {
    String command = action.equals("insert") ? text : action;
    if (shadowDemo && (command.equals("s") || command.equals("d"))) {
      shadowIndex = command.equals("d") ? 3 : shadowIndex < 3 ? (shadowIndex + 1) % 3 : 0;
      content = new Rect(0, 0, 0, 0);
      return;
    }
    if (action.equals("click")) {
      String[] xy = text.split(" +");
      if (xy.length == 2)
        try {
          pointer(Integer.parseInt(xy[0]), Integer.parseInt(xy[1]), 0);
        } catch (NumberFormatException ignored) {
        }
      return;
    }

    if (action.equals("f10")) {
      if (menu.opened())
        sync(menu.close());
      else {
        anchor = null;
        open(context ? "" : "file");
      }
    } else if (action.equals("context")) {
      String[] xy = text.split(" +");
      if (xy.length == 2)
        try {
          int x = Integer.parseInt(xy[0]), y = Integer.parseInt(xy[1]);
          if (contains(area, x, y)) {
            anchor = new Rect(x, y, 1, 1);
            open("");
          }
        } catch (NumberFormatException ignored) { /* Invalid host command leaves state unchanged. */
        }
    } else if (menu.opened()) {
      if (action.equals("cancel") && focus.requestClose() == null)
        return;
      sync(menu.handle(action.equals("insert") ? "mnemonic" : action, text, content.height()));
    } else if (!focus.route("root").blocked())
      editor.handle(action.equals("activate") ? "newline" : action, text);
  }
  void pointer(int x, int y, int button) {
    if (button == 2 && contains(area, x, y)) {
      anchor = new Rect(x, y, 1, 1);
      open("");
    } else if (button == 0) {
      if (menu.opened() && contains(content, x, y))
        sync(menu.click(x - content.x(), y - content.y(), content.height()));
      else if (contains(bar, x, y)) {
        var e = menu.barClick(x - bar.x(), bar.width());
        if (e.kind().equals("open_request")) {
          anchor = null;
          open(e.id());
        }
      } else if (!menu.opened() && !focus.route("root").blocked() && contains(editorArea, x, y))
        editor.click(
            x - editorArea.x(), y - editorArea.y(), editorArea.width(), editorArea.height(), false);
    }
  }
  private static boolean contains(Rect r, int x, int y) {
    return x >= r.x() && x < r.x() + r.width() && y >= r.y() && y < r.y() + r.height();
  }
}
