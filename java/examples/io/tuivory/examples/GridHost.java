package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.util.*;
/** The application owns example records, approval and search/details modes. */
public final class GridHost {
  private final boolean en;
  private boolean density;
  private Rect area = new Rect(0, 0, 0, 0);
  private List<GridRecord> rows = new ArrayList<>();
  private final Grid grid;
  private Text search;
  private TextDocument detail;
  private GridViewState saved;
  private GridEvent pending;
  private GridPasteRequest paste;
  private String message = "";
  private String word(String ko, String english) {
    return en ? english : ko;
  }
  private GridRecord row(String id, String number, String name, String value, String state) {
    var r = new GridRecord(id);
    r.cells.put("id", number);
    r.cells.put("name", name);
    r.cells.put("value", value);
    r.cells.put("state", state);
    return r;
  }
  public GridHost(boolean en, boolean ascii) {
    this.en = en;
    rows.add(
        row("r1", "01", word("한글 👩‍💻", ascii ? "ASCII sample" : "Unicode 👩‍💻"),
            "1234", word("준비", "Ready")));
    rows.add(row("r2", "02", word("널 값", "Null value"), null, "NULL"));
    rows.add(
        row("r3", "03", word("비활성 행", "Disabled row"), "blocked", word("비활성", "Disabled")));
    rows.get(2).state.disabled = true;
    rows.add(row(
        "r4", "04", word("읽기 전용", "Read only"), "read-only", word("읽기 전용", "Read only")));
    rows.get(3).state.readOnly = true;
    rows.add(
        row("r5", "05", word("수정된 셀", "Edited cell"), "changed", word("수정됨", "Edited")));
    var edited = new State();
    edited.edited = true;
    rows.get(4).cellStates.put("value", edited);
    rows.add(row("r6", "06", word("빈 문자열", "Empty string"), "", word("비어 있음", "Empty")));
    rows.add(row("r7", "07", "Find target", "long_value_for_horizontal_scrolling",
        word("검색 가능", "Searchable")));
    rows.add(
        row("r8", "08", word("오류 표시", "Invalid cell"), "invalid", word("오류", "Invalid")));
    var invalid = new State();
    invalid.invalid = true;
    rows.get(7).cellStates.put("value", invalid);
    var id = new GridColumn("id", "ID", 5, false);
    id.pin = "left";
    var state = new GridColumn("state", word("상태", "State"), 12, false);
    state.pin = "right";
    grid = new Grid(List.of(id, new GridColumn("name", word("이름", "Name"), 18, true),
                        new GridColumn("value", word("값", "Value"), 22, true), state),
        rows);
    grid.setOptions(gridPreset("data"));
    var labels = new GridLabels();
    labels.loading = word("로딩 중", "loading");
    labels.empty = word("비어 있음", "empty");
    labels.range = word("범위", "range");
    labels.more = word("더 있음", "more");
    grid.setLabels(labels);
    var editing = new GridEditOptions();
    editing.enabled = editing.startTyping = editing.allowNull = true;
    grid.setEditOptions(editing);
    var co = new GridColumnOptions();
    co.align = "auto";
    co.overflow = "scroll";
    co.expand = 1;
    grid.setColumnOptions("value", co);
    grid.setCellInfo((r, c) -> {
      var i = new GridCellInfo();
      i.display = "1,234";
      i.hasDisplay = i.numeric = c.id.equals("value") && "1234".equals(r.cells.get("value"));
      return i;
    });
    grid.focus("r1", "name");
  }
  public void draw(Canvas c, Rect a, boolean ascii) {
    area = new Rect(a.x(), a.y(), a.width(), Math.max(0, a.height() - 3));
    grid.draw(c, area, search == null && detail == null, ascii);
    if (detail != null) {
      var inner = c.panel(area, word("원문 상세", "Raw cell details"), true, ascii);
      detail.wrap = true;
      detail.draw(c, inner, true, ascii);
    }
    if (a.height() >= 3) {
      int y = a.y() + a.height() - 3;
      if (search != null) {
        String prompt = word("검색: ", "Find: ");
        int offset = Math.min(a.width(), cells(prompt));
        c.write(a.x(), y, prompt, "hint", false, a.width());
        search.draw(c, new Rect(a.x() + offset, y, Math.max(0, a.width() - offset), 1), true);
      } else
        c.write(a.x(), y, message, "info", false, a.width());
    }
    if (a.height() >= 2)
      c.write(a.x(), a.y() + a.height() - 2,
          word("Enter 편집 | / 검색 | d 원문 | p 붙여넣기 | c 복사",
              "Enter edit | / find | d details | p paste | c copy"),
          "hint", false, a.width());
    if (a.height() > 0)
      c.write(a.x(), a.y() + a.height() - 1,
          word("대기: y 승인/r 거절 | Ctrl+N NULL | v 간격 | b 보기 저장/복원",
              "Pending: y approve/r reject | Ctrl+N NULL | v density | b view"),
          "hint", false, a.width());
  }
  private void approve(boolean accept) {
    if (pending == null && paste == null)
      return;
    if (!accept) {
      if (pending != null)
        grid.resolveEdit(
            pending.id(), word("거절됨: 수정 후 다시 제출", "Rejected: edit and retry"));
      else
        grid.cancelPaste();
      message = word("앱이 요청을 거절했습니다.", "Host rejected the request.");
      pending = null;
      paste = null;
      return;
    }
    var next = new ArrayList<GridRecord>();
    for (var r : rows) {
      var copy = new GridRecord(r.id, r.cells);
      copy.state = r.state;
      copy.cellStates.putAll(r.cellStates);
      next.add(copy);
    }
    var changes = paste != null
        ? paste.changes()
        : List.of(new GridChange(pending.rowId(), pending.columnId(), pending.value()));
    for (var change : changes) {
      var r = next.stream().filter(v -> v.id.equals(change.rowId())).findFirst().orElse(null);
      if (r != null) {
        r.cells.put(change.columnId(), change.value().isNull() ? null : change.value().text());
        var state = new State();
        state.edited = true;
        r.cellStates.put(change.columnId(), state);
      }
    }
    var source = new MemoryRows(next);
    boolean accepted = pending != null ? grid.resolveEdit(pending.id(), "", source)
                                       : grid.resolvePaste(paste.id(), source);
    if (accepted)
      rows = next;
    message = accepted ? word("앱이 요청을 승인했습니다.", "Host approved the request.")
                       : word("만료된 요청입니다.", "Stale request.");
    pending = null;
    paste = null;
  }
  public void handle(String action, String text) {
    String command = action.equals("insert") ? text : action;
    if (detail != null) {
      if (action.equals("cancel"))
        detail = null;
      else
        detail.handle(action, text);
      return;
    }
    if (search != null) {
      if (action.equals("cancel"))
        search = null;
      else if (action.equals("activate")) {
        boolean found = grid.find(search.value());
        search = null;
        message = found ? word("검색 일치", "Match found") : word("검색 결과 없음", "No match");
      } else
        search.handle(action, text);
      return;
    }
    if (pending != null || paste != null) {
      if (command.equals("y") || command.equals("r"))
        approve(command.equals("y"));
      else if (action.equals("cancel")) {
        if (grid.edit != null)
          grid.handle("cancel");
        grid.cancelPaste();
        pending = null;
        paste = null;
        message = word("요청 취소", "Request cancelled");
      }
      return;
    }
    GridEvent event;
    if (grid.edit != null)
      event = grid.handle(action, Math.max(0, area.height()), text);
    else if (command.equals("/")) {
      search = new Text("");
      search.multiline = false;
      return;
    } else if (command.equals("d")) {
      detail = grid.details().orElse(null);
      return;
    } else if (command.equals("p")) {
      paste = grid.requestPaste("\"paste\tname\"\t\"raw\nvalue\"").orElse(null);
      message = paste != null
          ? word("승인 대기: y 승인 / r 거절", "Pending approval: y approve / r reject")
          : word("편집할 수 없는 셀입니다.", "This cell cannot be edited.");
      return;
    } else if (command.equals("c"))
      event = grid.copySelection();
    else if (command.equals("v")) {
      density = !density;
      grid.setOptions(gridPreset("data").withDensity(density ? "comfortable" : "normal"));
      return;
    } else if (command.equals("b")) {
      if (saved == null) {
        saved = grid.saveView();
        message = word("보기 저장됨", "View saved");
      } else {
        grid.restoreView(saved);
        saved = null;
        message = word("보기 복원됨", "View restored");
      }
      return;
    } else if (command.equals("click")) {
      String[] point = text.strip().split("\\s+");
      if (point.length == 2)
        pointer(area.x() + Integer.parseInt(point[0]), area.y() + Integer.parseInt(point[1]), 0);
      return;
    } else
      event = grid.handle(action, Math.max(0, area.height()), text);
    if (event.kind().equals("edit_submit")) {
      pending = event;
      message = word("승인 대기: y 승인 / r 거절", "Pending approval: y approve / r reject");
    } else if (event.kind().equals("copy"))
      message = word("복사 원문: ", "Raw copy: ") + event.text();
    else if (event.kind().equals("edit_denied") || event.kind().equals("paste_rejected"))
      message = word("편집할 수 없는 셀입니다.", "This cell cannot be edited.");
  }
  public void pointer(int x, int y, int button) {
    if (button != 0 || detail != null || search != null || pending != null || paste != null
        || !area.contains(x, y))
      return;
    var event = grid.click(x - area.x(), y - area.y(), area.width(), area.height());
    if (event.kind().equals("sort_request"))
      message = word("정렬 요청: 앱이 처리합니다.", "Sort requested: handled by the host.");
  }
}
