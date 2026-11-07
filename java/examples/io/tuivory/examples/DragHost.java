package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.util.*;
/** Application-owned focus and approvals for the independent drag API. */
public final class DragHost {
  private final boolean en;
  private boolean tabFocus;
  private Tree tree;
  private Tabs tabs;
  private final DragState drag = new DragState(true);
  private final DragOptions options = new DragOptions();
  private Rect tabArea = new Rect(0, 0, 0, 0), treeArea = new Rect(0, 0, 0, 0);
  private DropRequest pending;
  private String message = "";
  private String word(String ko, String english) {
    return en ? english : ko;
  }
  public DragHost(boolean en) {
    this.en = en;
    var a = new Tab("a", word("데이터", "Data"));
    a.edited = true;
    var d = new Tab("d", word("비활성", "Disabled"));
    d.disabled = true;
    tabs = new Tabs(
        List.of(a, new Tab("b", word("로그", "Logs")), new Tab("c", word("작업", "Tasks")), d));
    var root = new Node("root", word("작업 공간", "Workspace"));
    root.branch = true;
    var reports = new Node("a", word("보고서", "Reports"), "root");
    reports.branch = true;
    var archive = new Node("b", word("보관함", "Archive"), "root");
    archive.branch = true;
    tree =
        new Tree(List.of(root, reports, new Node("a1", word("월별 보고서", "Monthly report"), "a"),
            archive, new Node("b1", word("이전 자료", "Previous data"), "b"),
            new Node("c", word("메모", "Notes"), "root")));
    tree.expanded.addAll(List.of("root", "a"));
    options.autoScroll = options.hoverExpand = true;
  }
  public void draw(Canvas c, Rect area, boolean ascii) {
    tabArea = new Rect(area.x(), area.y(), area.width(), Math.min(1, area.height()));
    treeArea = new Rect(area.x(), area.y() + Math.min(2, area.height()), area.width(),
        Math.max(0, area.height() - 6));
    if (tabFocus) {
      tree.draw(c, treeArea, false, ascii);
      drag.draw(tabs, c, tabArea, true, ascii);
    } else {
      tabs.draw(c, tabArea, false, ascii);
      drag.draw(tree, c, treeArea, true, ascii);
    }
    String status = message.isEmpty()
        ? word("앱 승인 후에만 순서가 바뀝니다.", "Order changes only after host approval.")
        : message;
    if (pending != null)
      status = word("승인 대기: ", "Pending approval: ") + pending.sourceId() + " -> "
          + pending.targetId() + " (" + pending.position() + ") | y / r";
    var lines = List.of(word("Tab 대상 전환 | [ 이전 / ] 다음 | i 안으로 / o 밖으로",
                            "Tab switch | [ previous / ] next | i inside / o outside"),
        word("마우스로 끌기 | d 드래그 켜기/끄기 | Esc 취소",
            "Drag with mouse | d toggle dragging | Esc cancel"),
        status,
        word("드래그: ", "Dragging: ") + (drag.enabled ? "ON" : "OFF") + " | " + drag.phase);
    for (int i = 0; i < 4; i++) {
      int y = area.y() + area.height() - 4 + i;
      if (y >= area.y())
        c.write(area.x(), y, lines.get(i), i == 2 ? "info" : "hint", false, area.width());
    }
  }
  public void handle(String action, String text) {
    String command = action.equals("insert") ? text : action;
    if (pending != null) {
      if (command.equals("y")) {
        try {
          if (tabFocus)
            tabs = tabs.applyDrop(pending);
          else
            tree = tree.applyDrop(pending);
          message = word("앱이 이동을 승인했습니다.", "Host approved the move.");
        } catch (DropError failure) {
          message = failure.reason;
        }
        pending = null;
      } else if (command.equals("r") || action.equals("cancel")) {
        pending = null;
        message = word("앱이 이동을 거절했습니다.", "Host rejected the move.");
      }
      return;
    }
    if (action.equals("next") || action.equals("previous") || action.equals("tab")) {
      drag.cancel();
      tabFocus = !tabFocus;
      return;
    }
    if (action.equals("cancel")) {
      drag.cancel();
      return;
    }
    if (command.equals("d")) {
      drag.enabled = !drag.enabled;
      drag.cancel();
      return;
    }
    // Portable line mode also accepts: pointer down|move|up x y (zero-based).
    if (action.equals("pointer")) {
      var fields = text.split(" ");
      if (fields.length == 3)
        try {
          pointer(Integer.parseInt(fields[1]), Integer.parseInt(fields[2]), 0, fields[0]);
        } catch (NumberFormatException failure) {
          message = "invalid pointer";
        }
      return;
    }
    drag.cancel();
    if (List.of("[", "]", "i", "o").contains(command)) {
      String direction = switch (command) {
        case "[" -> "previous";
        case "]" -> "next";
        case "i" -> "inside";
        default -> "outside";
      };
      try {
        pending = tabFocus ? tabs.keyboardDrop(direction, options, null)
                           : tree.keyboardDrop(direction, options, null);
      } catch (DropError failure) {
        message = failure.reason;
      }
      return;
    }
    if (tabFocus)
      tabs.handle(action.equals("left") ? "previous" : action.equals("right") ? "next" : action);
    else
      tree.handle(action, treeArea.height());
  }
  public void pointer(int x, int y, int button, String kind) {
    if (pending != null || (button & 64) != 0 || ((button & 3) != 0 && (button & 3) != 3))
      return;
    if (kind.equals("down")) {
      boolean target;
      if (tabArea.contains(x, y))
        target = true;
      else if (treeArea.contains(x, y))
        target = false;
      else
        return;
      if (target != tabFocus) {
        drag.cancel();
        tabFocus = target;
      }
    }
    var a = tabFocus ? tabArea : treeArea;
    if (!kind.equals("down") && !drag.captured())
      return;
    var p = new DragPointer(kind, x - a.x(), y - a.y(), a.width(), a.height());
    var r = tabFocus ? drag.pointer(tabs, p, options, null) : drag.pointer(tree, p, options, null);
    if (r != null)
      pending = r;
    if (kind.equals("up") && drag.result.isEmpty() && a.contains(x, y)) {
      if (tabFocus)
        tabs.click(x - a.x(), a.width());
      else
        tree.click(x - a.x(), y - a.y(), a.height());
    }
  }
}
