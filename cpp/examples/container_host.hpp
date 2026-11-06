#pragma once
#include "tuivory.hpp"
class ContainerDemo {
  bool en_, opened_ = false;
  int ox_ = 0, oy_ = 0;
  std::string status_;
  tuivory::Container base_, layers_;
  tuivory::Text editor_;
  std::string word(const std::string &ko, const std::string &en) const {
    return en_ ? en : ko;
  }
  static std::vector<tuivory::LayoutItem> base_items() {
    tuivory::LayoutItem nav, editor;
    nav.id = "nav";
    nav.track.fixed = 20;
    editor.id = "editor";
    return {nav, editor};
  }
  static tuivory::ContainerOptions base_options() {
    tuivory::ContainerOptions o;
    o.kind = "row";
    o.gap = 1;
    o.virtual_width = 96;
    return o;
  }
  static std::vector<tuivory::LayoutItem> layers(bool open) {
    tuivory::LayoutItem background, popup;
    background.id = "background";
    popup.id = "popup";
    popup.modal = true;
    popup.centered = true;
    popup.area = {0, 0, 30, 6};
    return open ? std::vector<tuivory::LayoutItem>{background, popup}
                : std::vector<tuivory::LayoutItem>{background};
  }
  static tuivory::ContainerOptions layer_options() {
    tuivory::ContainerOptions o;
    o.kind = "layers";
    return o;
  }

public:
  explicit ContainerDemo(bool en, bool ascii = false)
      : en_(en), base_(base_items(), base_options()),
        layers_(layers(false), layer_options()),
        editor_(word("편집 영역 한글 界",
                     ascii ? "Editor area ASCII" : "Editor area Unicode 界")) {
    base_.state.move_focus(base_.items());
  }
  void draw(tuivory::Canvas &c, tuivory::Rect area, bool ascii) {
    using namespace tuivory;
    ox_ = area.x;
    oy_ = area.y;
    auto pane = [&](const std::string &id, Canvas &child, bool focused) {
      auto inner = child.panel({0, 0, child.width, child.height},
                               id == "nav" ? word("탐색", "Navigator")
                                           : word("편집", "Editor"),
                               focused, ascii);
      if (id == "nav")
        child.write(inner.x, inner.y, word("개요", "Overview"), "body", false,
                    inner.width);
      else
        editor_.draw(child, inner, focused);
    };
    layers_.draw(
        c, {area.x, area.y, area.width, std::max(0, area.height - 1)},
        [&](const std::string &id, Canvas &child, bool) {
          if (id == "background")
            base_.draw(child, {0, 0, child.width, child.height}, pane);
          else {
            auto inner = child.panel({0, 0, child.width, child.height},
                                     word("팝업", "Modal"), false, ascii);
            child.write(inner.x, inner.y,
                        word("배경 입력 차단", "Background input blocked"),
                        "body", false, inner.width);
            child.write(inner.x, inner.y + 1,
                        word("m / Esc 닫기", "m / Esc close"), "hint", false,
                        inner.width);
          }
        });
    if (area.height)
      c.write(area.x, area.y + area.height - 1,
              status_.empty() ? word("스크롤: ", "Scroll: ") +
                                    std::to_string(base_.scroll_x)
                              : status_,
              "hint", false, area.width);
  }
  void handle(const std::string &action, const std::string &text = "") {
    auto command = action == "insert" ? text : action;
    if (command == "m" || (command == "cancel" && opened_)) {
      opened_ = command == "m" ? !opened_ : false;
      layers_.set_items(layers(opened_));
      status_ = opened_ ? word("팝업 열림", "Popup open")
                        : word("팝업 닫힘", "Popup closed");
    } else if (!opened_) {
      if (command == "h" || command == "l") {
        base_.scroll_x =
            std::max(0, base_.scroll_x + (command == "l" ? 4 : -4));
        status_ = word("스크롤: ", "Scroll: ") + std::to_string(base_.scroll_x);
      } else if (command == "next" || command == "previous")
        base_.state.move_focus(base_.items(), command == "previous");
      else if (base_.state.focused == "editor")
        editor_.handle(action, text);
    }
  }
  void pointer(int x, int y, int button) {
    if (button == 0 && layers_.pointer(x, y, true, true) == "background")
      base_.pointer(x - ox_, y - oy_, true, true);
  }
};
