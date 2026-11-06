package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.util.ArrayList;
import java.util.List;
/** Host supplies literal contents, global keys and removal approval. */
final class LayoutHost {
  private final boolean en;
  private boolean active = true;
  private String density = "auto", status = "";
  private final Chip filter, readonly, disabled;
  private record Hit(Rect rect, Chip chip, boolean disabled) {}
  private final ArrayList<Hit> hits = new ArrayList<>();
  LayoutHost(boolean en) {
    this.en = en;
    filter = new Chip("filter", word("최근", "Recent"));
    filter.removable = true;
    readonly = new Chip("fixed", word("읽기 전용", "Read only"));
    readonly.state.readOnly = true;
    readonly.removable = true;
    disabled = new Chip("off", word("비활성", "Disabled"));
    disabled.state.disabled = true;
    disabled.removable = true;
  }
  private String word(String ko, String en) {
    return this.en ? en : ko;
  }
  void draw(Canvas c, Rect area, boolean ascii) {
    hits.clear();
    var tokens = SpacingTokens.forWidth(density, area.width());
    var layout =
        stackRects(new Rect(area.x(), area.y(), area.width(), Math.max(0, area.height() - 1)),
            List.of(new StackItem("badges", 16, 20, 0), new StackItem("support", 24, 40, 1)),
            tokens, false);
    var items = new Badge();
    items.label = word("항목", "Items");
    items.count = 123L;
    var selected = new Badge();
    selected.label = word("선택", "Selected");
    selected.count = 0L;
    selected.state.selected = true;
    var off = new Badge();
    off.label = word("비활성", "Disabled");
    off.state.disabled = true;
    for (var named : layout.rects()) {
      if (named.rect().width() == 0 || named.rect().height() == 0)
        continue;
      var inner = c.panel(named.rect(),
          named.id().equals("badges") ? word("배지", "Badges")
                                      : word("칩·단축키", "Chips and shortcuts"),
          false, ascii);
      int y = inner.y();
      if (named.id().equals("badges")) {
        for (var b : List.of(items, selected, off)) {
          if (y >= inner.y() + inner.height())
            break;
          b.draw(c, new Rect(inner.x(), y, inner.width(), 1));
          y += 1 + tokens.controlGap();
        }
      } else {
        for (var chip :
            active ? List.of(filter, readonly, disabled) : List.of(readonly, disabled)) {
          if (y >= inner.y() + inner.height())
            break;
          chip.draw(c, new Rect(inner.x(), y, inner.width(), 1));
          for (var s : chip.line(inner.width()).spans())
            hits.add(new Hit(new Rect(inner.x() + s.start(), y, s.width(), 1), chip, s.disabled()));
          y += 1 + tokens.controlGap();
        }
        var d = new Shortcut("d", word("간격 변경", "Change density"));
        d.priority = 10;
        var x = new Shortcut("x", word("필터 제거", "Remove filter"));
        x.priority = 5;
        x.disabled = !active;
        var r = new Shortcut("r", word("사용 불가", "Unavailable"));
        r.disabled = true;
        new Help(List.of(d, x, r))
            .draw(c,
                new Rect(inner.x(), y, inner.width(), Math.max(0, inner.y() + inner.height() - y)));
      }
    }
    String label = density.equals("auto") ? word("자동", "auto")
        : density.equals("compact")       ? word("촘촘", "compact")
                                          : word("여유", "comfortable");
    String text = status.isEmpty() ? word("밀도: ", "Density: ") + label
            + word(" | 숨긴 패널: ", " | Hidden panes: ") + layout.hidden().size()
                                   : status;
    if (area.height() > 0)
      c.write(area.x(), area.y() + area.height() - 1, text, "hint", false, area.width());
  }
  private void apply(Event event) {
    if (event.kind().equals("remove") && event.id().equals("filter") && active) {
      active = false;
      hits.clear();
      status = word("필터를 제거했습니다.", "Filter removed.");
    }
  }
  void handle(String action, String text) {
    String command = action.equals("insert") ? text : action;
    if (command.equals("x") || command.equals("activate"))
      apply(filter.requestRemove());
    else if (command.equals("d")) {
      density = density.equals("comfortable") ? "compact" : "comfortable";
      hits.clear();
      status = density.equals("compact") ? word("밀도: 촘촘", "Density: compact")
                                         : word("밀도: 여유", "Density: comfortable");
    } else if (action.equals("click")) {
      String[] xy = text.split(" +");
      if (xy.length == 2)
        try {
          pointer(Integer.parseInt(xy[0]), Integer.parseInt(xy[1]), 0);
        } catch (NumberFormatException ignored) { /* Invalid host command leaves state unchanged. */
        }
    }
  }
  void pointer(int x, int y, int button) {
    if (button != 0)
      return;
    for (var hit : hits)
      if (hit.rect().contains(x, y)) {
        if (!hit.disabled())
          apply(hit.chip().requestRemove());
        return;
      }
  }
}
