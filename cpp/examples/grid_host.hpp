#pragma once
#include "tuivory.hpp"
// The application owns example rows, approval choices and search/details modes.
class GridDemo {
  bool en_, density_ = false;
  tuivory::Rect area_;
  std::vector<tuivory::GridRecord> rows_;
  tuivory::Grid grid_;
  std::optional<tuivory::Text> search_;
  std::optional<tuivory::TextDocument> detail_;
  std::optional<tuivory::GridViewState> saved_;
  std::optional<tuivory::GridEvent> pending_;
  std::optional<tuivory::GridPasteRequest> paste_;
  std::string message_;
  std::string word(const std::string &ko, const std::string &en) const {
    return en_ ? en : ko;
  }
  static std::vector<tuivory::GridColumn> columns(bool en) {
    return {{"id", "ID", 5, false, false, "left"},
            {"name", en ? "Name" : "이름", 18, true, false, ""},
            {"value", en ? "Value" : "값", 22, true, false, ""},
            {"state", en ? "State" : "상태", 12, false, false, "right"}};
  }
  static std::vector<tuivory::GridRecord> rows(bool en, bool ascii) {
    auto w = [&](std::string ko, std::string english) {
      return en ? english : ko;
    };
    auto r = [](std::string id, std::string number, std::string name,
                std::optional<std::string> value, std::string state) {
      tuivory::GridRecord r;
      r.id = id;
      r.cells = {
          {"id", number}, {"name", name}, {"value", value}, {"state", state}};
      return r;
    };
    std::vector<tuivory::GridRecord> out{
        r("r1", "01",
          w("한글 👩‍💻",
            ascii ? "ASCII sample" : "Unicode 👩‍💻"),
          "1234", w("준비", "Ready")),
        r("r2", "02", w("널 값", "Null value"), std::nullopt, "NULL"),
        r("r3", "03", w("비활성 행", "Disabled row"), "blocked",
          w("비활성", "Disabled")),
        r("r4", "04", w("읽기 전용", "Read only"), "read-only",
          w("읽기 전용", "Read only")),
        r("r5", "05", w("수정된 셀", "Edited cell"), "changed",
          w("수정됨", "Edited")),
        r("r6", "06", w("빈 문자열", "Empty string"), "",
          w("비어 있음", "Empty")),
        r("r7", "07", "Find target", "long_value_for_horizontal_scrolling",
          w("검색 가능", "Searchable")),
        r("r8", "08", w("오류 표시", "Invalid cell"), "invalid",
          w("오류", "Invalid"))};
    out[2].state.disabled = true;
    out[3].state.read_only = true;
    out[4].cell_states["value"].edited = true;
    out[7].cell_states["value"].invalid = true;
    return out;
  }
  void approve(bool accept) {
    if (!pending_ && !paste_)
      return;
    if (!accept) {
      if (pending_)
        grid_.resolve_edit(pending_->id, word("거절됨: 수정 후 다시 제출",
                                              "Rejected: edit and retry"));
      else
        grid_.cancel_paste();
      message_ =
          word("앱이 요청을 거절했습니다.", "Host rejected the request.");
      pending_.reset();
      paste_.reset();
      return;
    }
    auto next = rows_;
    std::vector<tuivory::GridChange> changes;
    if (paste_)
      changes = paste_->changes;
    else {
      tuivory::GridChange change;
      change.row_id = pending_->row_id;
      change.column_id = pending_->column_id;
      change.value = pending_->value;
      changes.push_back(std::move(change));
    }
    for (const auto &c : changes) {
      auto r = std::find_if(next.begin(), next.end(),
                            [&](const auto &r) { return r.id == c.row_id; });
      if (r != next.end()) {
        r->cells[c.column_id] = c.value.null
                                    ? std::nullopt
                                    : std::optional<std::string>(c.value.text);
        r->cell_states[c.column_id].edited = true;
      }
    }
    auto source = std::make_shared<tuivory::MemoryRows>(next);
    bool accepted = pending_ ? grid_.resolve_edit(pending_->id, "", source)
                             : grid_.resolve_paste(paste_->id, source);
    if (accepted)
      rows_ = std::move(next);
    message_ = accepted ? word("앱이 요청을 승인했습니다.",
                               "Host approved the request.")
                        : word("만료된 요청입니다.", "Stale request.");
    pending_.reset();
    paste_.reset();
  }

public:
  GridDemo(bool en, bool ascii)
      : en_(en), rows_(rows(en, ascii)), grid_(columns(en), rows_) {
    grid_.set_options(tuivory::grid_preset("data"));
    tuivory::GridLabels labels;
    labels.loading = word("로딩 중", "loading");
    labels.empty = word("비어 있음", "empty");
    labels.range = word("범위", "range");
    labels.more = word("더 있음", "more");
    grid_.set_labels(labels);
    tuivory::GridEditOptions editing;
    editing.enabled = editing.start_typing = editing.allow_null = true;
    grid_.set_edit_options(editing);
    tuivory::GridColumnOptions co;
    co.align = "auto";
    co.overflow = "scroll";
    co.expand = 1;
    grid_.set_column_options("value", co);
    grid_.set_cell_info([](const auto &r, const auto &c) {
      tuivory::GridCellInfo i;
      auto p = r.cells.find("value");
      bool numeric = c.id == "value" && p != r.cells.end() && p->second &&
                     *p->second == "1234";
      i.display = "1,234";
      i.has_display = i.numeric = numeric;
      return i;
    });
    grid_.focus("r1", "name");
  }
  void draw(tuivory::Canvas &c, tuivory::Rect a, bool ascii) {
    area_ = {a.x, a.y, a.width, std::max(0, a.height - 3)};
    grid_.draw(c, area_, !search_ && !detail_, ascii);
    if (detail_) {
      auto inner =
          c.panel(area_, word("원문 상세", "Raw cell details"), true, ascii);
      detail_->wrap = true;
      detail_->draw(c, inner, true, ascii);
    }
    if (a.height >= 3) {
      int y = a.y + a.height - 3;
      if (search_) {
        auto prompt = word("검색: ", "Find: ");
        int offset = std::min(a.width, tuivory::cells(prompt));
        c.write(a.x, y, prompt, "hint", false, a.width);
        search_->draw(c, {a.x + offset, y, std::max(0, a.width - offset), 1});
      } else
        c.write(a.x, y, message_, "info", false, a.width);
    }
    if (a.height >= 2)
      c.write(a.x, a.y + a.height - 2,
              word("Enter 편집 | / 검색 | d 원문 | p 붙여넣기 | c 복사",
                   "Enter edit | / find | d details | p paste | c copy"),
              "hint", false, a.width);
    if (a.height)
      c.write(
          a.x, a.y + a.height - 1,
          word(
              "대기: y 승인/r 거절 | Ctrl+N NULL | v 간격 | b 보기 저장/복원",
              "Pending: y approve/r reject | Ctrl+N NULL | v density | b view"),
          "hint", false, a.width);
  }
  void handle(const std::string &action, const std::string &text = "") {
    auto command = action == "insert" ? text : action;
    if (detail_) {
      if (action == "cancel")
        detail_.reset();
      else
        detail_->handle(action, text);
      return;
    }
    if (search_) {
      if (action == "cancel")
        search_.reset();
      else if (action == "activate") {
        bool found = grid_.find(search_->value);
        search_.reset();
        message_ = found ? word("검색 일치", "Match found")
                         : word("검색 결과 없음", "No match");
      } else
        search_->handle(action, text);
      return;
    }
    if (pending_ || paste_) {
      if (command == "y" || command == "r")
        approve(command == "y");
      else if (action == "cancel") {
        if (grid_.edit)
          grid_.handle("cancel");
        grid_.cancel_paste();
        pending_.reset();
        paste_.reset();
        message_ = word("요청 취소", "Request cancelled");
      }
      return;
    }
    tuivory::GridEvent event;
    if (grid_.edit)
      event = grid_.handle(action, std::max(0, area_.height), text);
    else if (command == "/") {
      search_.emplace("");
      search_->multiline = false;
      return;
    } else if (command == "d") {
      detail_ = grid_.details();
      return;
    } else if (command == "p") {
      paste_ = grid_.request_paste("\"paste\tname\"\t\"raw\nvalue\"");
      if (paste_)
        message_ = word("승인 대기: y 승인 / r 거절",
                        "Pending approval: y approve / r reject");
      else
        message_ =
            word("편집할 수 없는 셀입니다.", "This cell cannot be edited.");
      return;
    } else if (command == "c")
      event = grid_.copy_selection();
    else if (command == "v") {
      density_ = !density_;
      grid_.set_options(tuivory::grid_preset("data").with_density(
          density_ ? "comfortable" : "normal"));
      return;
    } else if (command == "b") {
      if (!saved_) {
        saved_ = grid_.save_view();
        message_ = word("보기 저장됨", "View saved");
      } else {
        grid_.restore_view(*saved_);
        saved_.reset();
        message_ = word("보기 복원됨", "View restored");
      }
      return;
    } else
      event = grid_.handle(action, std::max(0, area_.height), text);
    if (event.kind == "edit_submit") {
      pending_ = event;
      message_ = word("승인 대기: y 승인 / r 거절",
                      "Pending approval: y approve / r reject");
    } else if (event.kind == "copy")
      message_ = word("복사 원문: ", "Raw copy: ") + event.text;
    else if (event.kind == "edit_denied" || event.kind == "paste_rejected")
      message_ =
          word("편집할 수 없는 셀입니다.", "This cell cannot be edited.");
  }
  void pointer(int x, int y, int button, std::string kind) {
    if (detail_ || search_ || pending_ || paste_) {
      grid_.pointer("cancel", 0, 0, area_.width, area_.height);
      return;
    }
    const char *wheel[] = {"wheel_up", "wheel_down", "wheel_left",
                           "wheel_right"};
    if (button & 64)
      kind = wheel[button & 3];
    else if ((button & 3) && kind != "up")
      return;
    if (!grid_.pointer_captured() && !area_.contains(x, y))
      return;
    auto e = grid_.pointer(kind, x - area_.x, y - area_.y, area_.width,
                           area_.height, (button & 4) != 0);
    if (e.kind == "sort_request")
      message_ = word("정렬 요청: 앱이 처리합니다.",
                      "Sort requested: handled by the host.");
  }
};
