#pragma once
#include "tuivory.hpp"
// Host-owned focus and approval; no business I/O in the library.
class DragDemo {
  bool en_, tab_focus_ = false;
  tuivory::Tree tree_;
  tuivory::Tabs tabs_;
  tuivory::DragState drag_{true};
  tuivory::DragOptions options_;
  tuivory::Rect tabs_area_, tree_area_;
  std::optional<tuivory::DropRequest> pending_;
  std::string message_;
  std::string word(std::string ko, std::string en) const {
    return en_ ? en : ko;
  }
  static std::vector<tuivory::Node> nodes(bool en) {
    std::vector<tuivory::Node> out;
    auto add = [&](std::string id, std::string ko, std::string english,
                   std::string parent, bool branch) {
      tuivory::Node n;
      n.id = id;
      n.name = en ? english : ko;
      n.parent = parent;
      n.branch = branch;
      out.push_back(n);
    };
    add("root", "작업 공간", "Workspace", "", true);
    add("a", "보고서", "Reports", "root", true);
    add("a1", "월별 보고서", "Monthly report", "a", false);
    add("b", "보관함", "Archive", "root", true);
    add("b1", "이전 자료", "Previous data", "b", false);
    add("c", "메모", "Notes", "root", false);
    return out;
  }

public:
  explicit DragDemo(bool en)
      : en_(en), tree_(nodes(en)),
        tabs_({{"a", en ? "Data" : "데이터", true, false, false},
               {"b", en ? "Logs" : "로그", false, false, false},
               {"c", en ? "Tasks" : "작업", false, false, false},
               {"d", en ? "Disabled" : "비활성", false, false, true}}) {
    tree_.expanded = {"root", "a"};
    options_.auto_scroll = options_.hover_expand = true;
  }
  void draw(tuivory::Canvas &c, tuivory::Rect area, bool ascii) {
    using namespace tuivory;
    tabs_area_ = {area.x, area.y, area.width, std::min(1, area.height)};
    tree_area_ = {area.x, area.y + std::min(2, area.height), area.width,
                  std::max(0, area.height - 6)};
    if (tab_focus_) {
      tree_.draw(c, tree_area_, false, ascii);
      drag_.draw(tabs_, c, tabs_area_, true, ascii);
    } else {
      tabs_.draw(c, tabs_area_, false, ascii);
      drag_.draw(tree_, c, tree_area_, true, ascii);
    }
    auto status = message_.empty()
                      ? word("앱 승인 후에만 순서가 바뀝니다.",
                             "Order changes only after host approval.")
                      : message_;
    if (pending_)
      status = word("승인 대기: ", "Pending approval: ") + pending_->source_id +
               " -> " + pending_->target_id + " (" + pending_->position +
               ") | y / r";
    std::vector<std::string> lines{
        word("Tab 대상 전환 | [ 이전 / ] 다음 | i 안으로 / o 밖으로",
             "Tab switch | [ previous / ] next | i inside / o outside"),
        word("마우스로 끌기 | d 드래그 켜기/끄기 | Esc 취소",
             "Drag with mouse | d toggle dragging | Esc cancel"),
        status,
        word("드래그: ", "Dragging: ") + (drag_.enabled ? "ON" : "OFF") +
            " | " + drag_.phase};
    for (int i = 0; i < 4; i++) {
      int y = area.y + area.height - 4 + i;
      if (y >= area.y)
        c.write(area.x, y, lines[i], i == 2 ? "info" : "hint", false,
                area.width);
    }
  }
  void handle(std::string action, std::string text = "") {
    auto command = action == "insert" ? text : action;
    if (pending_) {
      if (command == "y") {
        try {
          if (tab_focus_)
            tabs_ = tabs_.apply_drop(*pending_);
          else
            tree_ = tree_.apply_drop(*pending_);
          message_ =
              word("앱이 이동을 승인했습니다.", "Host approved the move.");
        } catch (const tuivory::DropError &e) {
          message_ = e.reason;
        }
        pending_.reset();
      } else if (command == "r" || action == "cancel") {
        pending_.reset();
        message_ = word("앱이 이동을 거절했습니다.", "Host rejected the move.");
      }
      return;
    }
    if (action == "next" || action == "previous") {
      drag_.cancel();
      tab_focus_ = !tab_focus_;
      return;
    }
    if (action == "cancel") {
      drag_.cancel();
      return;
    }
    if (command == "d") {
      drag_.enabled = !drag_.enabled;
      drag_.cancel();
      return;
    }
    drag_.cancel();
    if (command == "[" || command == "]" || command == "i" || command == "o") {
      auto direction = command == "["   ? "previous"
                       : command == "]" ? "next"
                       : command == "i" ? "inside"
                                        : "outside";
      try {
        pending_ = tab_focus_ ? tabs_.keyboard_drop(direction, options_)
                              : tree_.keyboard_drop(direction, options_);
      } catch (const tuivory::DropError &e) {
        message_ = e.reason;
      }
      return;
    }
    if (tab_focus_)
      tabs_.handle(action == "left"    ? "previous"
                   : action == "right" ? "next"
                                       : action);
    else
      tree_.handle(action, tree_area_.height);
  }
  void pointer(int x, int y, int button, std::string kind = "down") {
    if (pending_ || (button & 64) || ((button & 3) != 0 && (button & 3) != 3))
      return;
    auto inside = [&](tuivory::Rect a) {
      return x >= a.x && x < a.x + a.width && y >= a.y && y < a.y + a.height;
    };
    if (kind == "down") {
      bool target;
      if (inside(tabs_area_))
        target = true;
      else if (inside(tree_area_))
        target = false;
      else
        return;
      if (target != tab_focus_) {
        drag_.cancel();
        tab_focus_ = target;
      }
    }
    auto a = tab_focus_ ? tabs_area_ : tree_area_;
    if (kind != "down" && !drag_.captured())
      return;
    tuivory::DragPointer p{kind, x - a.x, y - a.y, a.width, a.height};
    auto r = tab_focus_ ? drag_.pointer(tabs_, p, options_)
                        : drag_.pointer(tree_, p, options_);
    if (r)
      pending_ = r;
    if (kind == "up" && drag_.result.empty() && inside(a)) {
      if (tab_focus_)
        tabs_.click(x - a.x, a.width);
      else
        tree_.click(x - a.x, y - a.y, a.height);
    }
  }
};
