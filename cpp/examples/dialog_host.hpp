#pragma once
#include "tuivory.hpp"
// The host owns visibility, modal focus and acceptance of action requests.
class DialogDemo {
  bool en_, opened_ = false, disabled_ = false;
  tuivory::Focus focus_{"root", {{"editor"}}};
  tuivory::Text editor_;
  tuivory::Dialog dialog_;
  tuivory::Rect card_, area_;
  std::string status_;
  std::string word(const std::string &ko, const std::string &en) const {
    return en_ ? en : ko;
  }
  std::vector<tuivory::DialogButton> buttons() const {
    return {{"retry", word("작업 다시 시도", "Retry operation")},
            {"settings", word("연결 설정 열기", "Open settings")},
            {"cancel", word("취소", "Cancel"), disabled_}};
  }
  void open() {
    if (!opened_) {
      focus_.open("dialog", {{"buttons"}});
      opened_ = true;
    }
    dialog_.focus("cancel");
  }
  void accept(const tuivory::Event &e) {
    if (e.kind == "activate" || e.kind == "cancel") {
      status_ = word("앱이 수락한 요청: ", "Host accepted: ") + e.id;
      opened_ = false;
      focus_.close("dialog");
      card_ = {};
    }
  }

public:
  explicit DialogDemo(bool en)
      : en_(en), editor_(word("대화상자를 닫으면 편집합니다.",
                              "Close the dialog to edit this text.")),
        dialog_(
            word("다시 연결", "Reconnect"),
            word(
                "작업을 다시 시도할까요?\n내용과 실행은 앱이 결정합니다.",
                "Retry the operation?\nThe host supplies content and actions."),
            buttons(), "cancel"),
        status_(word("아직 실행하지 않았습니다.", "No action accepted.")) {
    open();
  }
  void draw(tuivory::Canvas &c, tuivory::Rect a, bool ascii) {
    using namespace tuivory;
    area_ = a;
    editor_.draw(c, {a.x, a.y, a.width, std::min(2, a.height)}, !opened_);
    std::string under;
    for (int x = 0; x < a.width; x++)
      under += ascii ? ":" : en_ ? "界" : "가";
    for (int y = a.y + 2; y < a.y + std::max(0, a.height - 2); y++)
      c.write(a.x, y, under, "hint", false, a.width);
    if (a.height >= 2)
      c.write(a.x, a.y + a.height - 2, status_, "hint", false, a.width);
    if (a.height)
      c.write(a.x, a.y + a.height - 1,
              word("m 열기 | x 취소 비활성 전환",
                   "m reopen | x toggle Cancel disabled"),
              "hint", false, a.width);
    if (opened_) {
      int w = std::min(41, a.width),
          h = std::min(12, std::max(0, a.height - 2));
      card_ = Shadow(ShadowOptions{"auto"})
                  .draw(
                      c,
                      {a.x + (a.width - w) / 2,
                       a.y + std::max(0, (a.height - h) / 2 - 1), w, h},
                      [&](Canvas &child) {
                        dialog_.draw(child, {0, 0, child.width, child.height},
                                     true, ascii);
                      },
                      ascii)
                  .card;
    }
  }
  void handle(const std::string &action, const std::string &text = "") {
    auto cmd = action == "insert" ? text : action;
    if (cmd == "m")
      open();
    else if (cmd == "x") {
      disabled_ = !disabled_;
      dialog_.set_buttons(buttons());
    } else if (opened_)
      accept(dialog_.handle(action));
    else
      editor_.handle(action == "activate" ? "newline" : action, text);
  }
  void pointer(int x, int y, int button) {
    if (button != 0)
      return;
    if (opened_) {
      if (card_.contains(x, y))
        accept(dialog_.click(x - card_.x, y - card_.y));
    } else if (area_.contains(x, y))
      editor_.click(x - area_.x, y - area_.y, area_.width,
                    std::min(2, area_.height));
  }
};
