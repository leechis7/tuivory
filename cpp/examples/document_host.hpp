#pragma once
#include "tuivory.hpp"
class DocumentDemo {
  bool en_;
  tuivory::Rect area_;
  tuivory::TextDocument document_;
  std::string word(const std::string &ko, const std::string &en) const {
    return en_ ? en : ko;
  }

public:
  DocumentDemo(bool en, bool ascii)
      : en_(en),
        document_(tuivory::TextDocument::editor(
            word("문서 편집 예제\n한글 é 界 문장을 좁은 화면에서도 "
                 "확인합니다.\n[error]태그도 원문 그대로입니다.[/]\n마지막 "
                 "줄입니다.",
                 std::string("Document viewer/editor\n") +
                     (ascii ? "Literal ASCII text with a long wrapped line."
                            : "Unicode é 界 with a long wrapped line.") +
                     "\n[error]Tags remain literal text.[/]\nFinal line."))) {
    document_.wrap = true;
    document_.buffer.select(0, 0);
    document_.set_syntax({{0, 2, "info"}});
  }
  void draw(tuivory::Canvas &c, tuivory::Rect a, bool ascii) {
    using namespace tuivory;
    area_ = {a.x, a.y, a.width, std::max(0, a.height - 2)};
    auto &d = document_;
    d.draw(c, area_, true, ascii);
    std::string status =
        (d.buffer.state.read_only ? word("보기", "Viewer")
                                  : word("편집", "Editor")) +
        " | " + word("줄바꿈 ", "Wrap ") + (d.wrap ? "on" : "off") + " | " +
        word("줄 번호 ", "Numbers ") + (d.line_numbers ? "on" : "off") + " | " +
        word("비활성 ", "Disabled ") + (d.buffer.state.disabled ? "on" : "off");
    if (a.height >= 2)
      c.write(a.x, a.y + a.height - 2, status, "hint", false, a.width);
    if (a.height)
      c.write(a.x, a.y + a.height - 1,
              word("w 줄바꿈 | n 번호 | v 보기 | s 검색 | x 비활성 | m 마크업",
                   "w wrap | n numbers | v viewer | s search | x disabled | m "
                   "markup"),
              "hint", false, a.width);
  }
  void handle(const std::string &action, const std::string &text = "") {
    auto cmd = action == "insert" ? text : action;
    auto &d = document_;
    if (cmd == "w") {
      d.wrap = !d.wrap;
      d.reveal_cursor();
    } else if (cmd == "n") {
      d.line_numbers = !d.line_numbers;
      d.reveal_cursor();
    } else if (cmd == "v")
      d.buffer.state.read_only = !d.buffer.state.read_only;
    else if (cmd == "x")
      d.buffer.state.disabled = !d.buffer.state.disabled;
    else if (cmd == "s") {
      bool search_ = d.search_matches().empty();
      d.set_search_matches(
          search_
              ? std::vector<tuivory::DocumentRange>{{0,
                                                     std::min<std::size_t>(
                                                         2, tuivory::graphemes(
                                                                d.buffer.value)
                                                                .size())}}
              : std::vector<tuivory::DocumentRange>{});
    } else if (cmd == "m") {
      d.set_markup(word("[info]명시적 마크업[/]\n[[error]는 리터럴입니다.",
                        "[info]Explicit markup[/]\n[[error] stays literal."));
      d.buffer.select(0, 0);
    } else
      d.handle(action == "activate" ? "newline" : action, text);
  }
  void pointer(int x, int y, int button) {
    if (button == 0 && area_.contains(x, y))
      document_.click(x - area_.x, y - area_.y, area_.width, area_.height);
  }
};
