#pragma once
// Example composition: hosts own screens, global shortcuts and action
#include "tuivory.hpp"
// callbacks.
class MenuDemo {
  bool en_, context_, shadow_demo_;
  int shadow_index_ = 0;
  std::string shadow_mode() const {
    const char *modes[] = {"auto", "solid", "off", "dim"};
    return shadow_demo_ ? modes[shadow_index_] : "off";
  }
  tuivory::Menu menu_;
  tuivory::Focus focus_{"root", {{"editor"}}};
  tuivory::Text editor_;
  tuivory::Rect area_{}, bar_{}, content_{}, editor_area_{};
  std::optional<tuivory::Rect> anchor_;
  std::string status_;
  static std::vector<tuivory::MenuItem> items(bool en) {
    std::vector<tuivory::MenuItem> out;
    auto add = [&](std::string id, std::string label, std::string parent = "",
                   std::string mnemonic = "", std::string shortcut = "",
                   bool disabled = false, bool separator = false) {
      tuivory::MenuItem i;
      i.id = id;
      i.label = label;
      i.parent = parent;
      i.mnemonic = mnemonic;
      i.shortcut = shortcut;
      i.disabled = disabled;
      i.separator = separator;
      out.push_back(i);
    };
    add("file", en ? "File" : "파일", "", "f");
    add("new", en ? "New document" : "새 문서", "file", "n", "Ctrl+N");
    add("line", "", "file", "", "", false, true);
    add("off", en ? "Unavailable" : "사용 불가", "file", "", "", true);
    add("recent", en ? "Recent documents" : "최근 문서", "file", "r");
    add("a", en ? "Example A" : "예제 A", "recent", "a");
    add("more", en ? "More" : "더 보기", "recent", "m");
    add("b", en ? "Example B" : "예제 B", "more", "b");
    add("edit", en ? "Edit" : "편집", "", "e");
    add("copy", en ? "Copy" : "복사", "edit", "c", "Ctrl+C");
    return out;
  }
  void sync(tuivory::MenuEvent e = {}) {
    if (!menu_.opened() && focus_.depth())
      focus_.close("popup");
    if (e.kind == "activate")
      for (const auto &i : menu_.items())
        if (i.id == e.id)
          status_ = (en_ ? "Selected: " : "선택: ") + i.label;
  }
  void open(const std::string &id) {
    menu_.open(id, "editor");
    if (menu_.opened() && !focus_.depth())
      focus_.open("popup", {{"menu"}});
    sync();
  }
  static bool contains(tuivory::Rect r, int x, int y) {
    return x >= r.x && x < r.x + r.width && y >= r.y && y < r.y + r.height;
  }

public:
  MenuDemo(bool en, bool context, bool shadow = false)
      : en_(en), context_(context), shadow_demo_(shadow), menu_(items(en)),
        editor_(en ? "Close the menu to edit this text."
                   : "메뉴를 닫으면 여기를 편집할 수 있습니다."),
        status_(en ? "Clicks outside the popup are blocked."
                   : "팝업 밖의 클릭은 배경에 전달되지 않습니다.") {
    menu_.back_label = en ? "Back" : "뒤로";
    menu_.empty_label = en ? "(empty)" : "항목 없음";
    open(context ? "" : "file");
  }
  void draw(tuivory::Canvas &c, tuivory::Rect area, bool ascii) {
    using namespace tuivory;
    area_ = area;
    bar_ = {area.x, area.y, area.width, context_ ? 0 : 1};
    editor_area_ = {area.x, area.y + bar_.height, area.width,
                    std::min(2, std::max(0, area.height - bar_.height))};
    editor_.draw(c, editor_area_, !menu_.opened());
    std::string underlay;
    for (int x = 0; x < area.width; x++)
      underlay += ascii ? (shadow_demo_ ? ":" : ".") : en_ ? "界" : "가";
    for (int y = editor_area_.y + editor_area_.height;
         y < area.y + std::max(0, area.height - 2); y++)
      c.write(area.x, y, underlay, "hint", false, area.width);
    if (bar_.height)
      menu_.draw_bar(c, bar_);
    c.write(area.x, area.y + std::max(0, area.height - 2), status_, "hint",
            false, area.width);
    const char *ko_modes[] = {"자동", "검정", "끄기", "Dim(호환)"};
    std::string footer =
        shadow_demo_ ? (en_ ? "Shadow: " + shadow_mode() + " | s cycle | d Dim"
                            : std::string("그림자: ") +
                                  ko_modes[shadow_index_] + " | s 변경 | d Dim")
                     : (en_ ? "F10 menu | Shift+F10 / right click"
                            : "F10 메뉴 | Shift+F10 / 오른쪽 클릭");
    c.write(area.x, area.y + std::max(0, area.height - 1), footer, "hint",
            false, area.width);
    Rect anchor =
        anchor_.value_or(Rect{area.x + (context_ ? area.width / 2 : 1),
                              area.y + (context_ ? 5 : 0), 1, 1});
    if (context_ || anchor_)
      c.write(anchor.x, anchor.y, "+", "warning", false, 1);
    if (menu_.opened()) {
      auto size = menu_.content_size();
      ShadowOptions options{shadow_mode()};
      auto place = popup_placement(anchor, area,
                                   std::min(48, ((size.first + 5) / 2) * 2),
                                   size.second + 4, options);
      auto title = menu_.title();
      auto caption =
          title.empty() ? (en_ ? "Context menu" : "문맥 메뉴") : title;
      Rect local;
      auto layout = Shadow(options).draw(
          c, place.bounds,
          [&](Canvas &child) {
            local = menu_.draw_popup(child, {0, 0, child.width, child.height},
                                     caption, 1, ascii);
          },
          ascii);
      content_ = {layout.card.x + local.x, layout.card.y + local.y, local.width,
                  local.height};

    } else
      content_ = {};
  }
  void handle(const std::string &action, const std::string &text = "") {
    auto command = action == "insert" ? text : action;
    if (shadow_demo_ && (command == "s" || command == "d")) {
      shadow_index_ = command == "d"      ? 3
                      : shadow_index_ < 3 ? (shadow_index_ + 1) % 3
                                          : 0;
      content_ = {};
      return;
    }
    if (action == "f10") {
      if (menu_.opened())
        sync(menu_.close());
      else {
        anchor_.reset();
        open(context_ ? "" : "file");
      }
    } else if (action == "shift_f10") {
      anchor_ = tuivory::Rect{area_.x + area_.width / 2, area_.y + 4, 1, 1};
      open("");
    } else if (menu_.opened()) {
      if (action == "cancel" && !focus_.request_close())
        return;
      sync(menu_.handle(action == "insert" ? "mnemonic" : action, text,
                        content_.height));
    } else if (!focus_.route("root").blocked)
      editor_.handle(action == "activate" ? "newline" : action, text);
  }
  void pointer(int x, int y, int button) {
    if (button == 2 && contains(area_, x, y)) {
      anchor_ = tuivory::Rect{x, y, 1, 1};
      open("");
    } else if (button == 0) {
      if (menu_.opened() && contains(content_, x, y))
        sync(menu_.click(x - content_.x, y - content_.y, content_.height));
      else if (contains(bar_, x, y)) {
        auto e = menu_.bar_click(x - bar_.x, bar_.width);
        if (e.kind == "open_request") {
          anchor_.reset();
          open(e.id);
        }
      } else if (!focus_.route("root").blocked && contains(editor_area_, x, y))
        editor_.click(x - editor_area_.x, y - editor_area_.y,
                      editor_area_.width, editor_area_.height);
    }
  }
};
