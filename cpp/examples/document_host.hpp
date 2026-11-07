#pragma once
#include "tuivory.hpp"
class DocumentDemo {
  bool en_, syntax_demo_, syntax_enabled_ = false, syntax_failed_ = false;
  int syntax_calls_ = 0;
  tuivory::Rect area_;
  tuivory::TextDocument document_;
  std::string word(const std::string &ko, const std::string &en) const {
    return en_ ? en : ko;
  }
  void enable_syntax() {
    syntax_failed_ = false;
    document_.set_syntax_analyzer(
        [this](const std::string &text, const tuivory::SyntaxRequest &request) {
          syntax_calls_++;
          if (syntax_failed_)
            throw std::invalid_argument("sample analysis failure");
          return tuivory::SQLAnalyzer{}.analyze_syntax(text, request);
        });
    syntax_enabled_ = true;
  }

public:
  DocumentDemo(bool en, bool ascii, bool syntax = false)
      : en_(en), syntax_demo_(syntax),
        document_(tuivory::TextDocument::editor(
            word("문서 편집 예제\n한글 é 界 문장을 좁은 화면에서도 "
                 "확인합니다.\n[error]태그도 원문 그대로입니다.[/]\n마지막 "
                 "줄입니다.",
                 std::string("Document viewer/editor\n") +
                     (ascii ? "Literal ASCII text with a long wrapped line."
                            : "Unicode é 界 with a long wrapped line.") +
                     "\n[error]Tags remain literal text.[/]\nFinal line."))) {
    document_.wrap = true;
    if (syntax) {
      document_.set_text(std::string("SELECT COUNT(*) AS total,\n       "
                                     "CAST(:id AS NUMBER), NVL(:name, '") +
                         (en && ascii ? "sample"
                          : en        ? "é 界"
                                      : "한글 é 界") +
                         "')\nFROM sample_table\nWHERE id >= 1.2e-3D; -- " +
                         word("실행하지 않는 견본", "Example only"));
      document_.buffer.select(0, 0);
      enable_syntax();
    } else {
      document_.buffer.select(0, 0);
      document_.set_syntax({{0, 2, "info"}});
    }
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
    if (syntax_demo_)
      status = word("구문 ", "Syntax ") +
               (d.syntax_error()  ? "error"
                : syntax_enabled_ ? "on"
                                  : "off") +
               " | " + word("분석 ", "Calls ") + std::to_string(syntax_calls_) +
               " | " + status;
    if (a.height >= 2)
      c.write(a.x, a.y + a.height - 2, status, "hint", false, a.width);
    if (a.height)
      c.write(
          a.x, a.y + a.height - 1,
          syntax_demo_
              ? word("a 구문 전환 | f 실패 | w 줄바꿈 | x 비활성",
                     "a analyzer | f failure | w wrap | x disabled")
              : word(
                    "w 줄바꿈 | n 번호 | v 보기 | s 검색 | x 비활성 | m 마크업",
                    "w wrap | n numbers | v viewer | s search | x disabled | m "
                    "markup"),
          "hint", false, a.width);
  }
  void handle(const std::string &action, const std::string &text = "") {
    auto cmd = action == "insert" ? text : action;
    auto &d = document_;
    if (syntax_demo_ && cmd == "a") {
      if (syntax_enabled_) {
        d.set_syntax_analyzer({});
        syntax_enabled_ = false;
      } else
        enable_syntax();
    } else if (syntax_demo_ && cmd == "f") {
      if (d.buffer.state.read_only || d.buffer.state.disabled)
        return;
      if (syntax_failed_)
        enable_syntax();
      else if (syntax_enabled_) {
        syntax_failed_ = true;
        d.handle("insert", " ");
      }
    } else if (cmd == "w") {
      d.wrap = !d.wrap;
      d.reveal_cursor();
    } else if (cmd == "n") {
      d.line_numbers = !d.line_numbers;
      d.reveal_cursor();
    } else if (cmd == "v")
      d.buffer.state.read_only = !d.buffer.state.read_only;
    else if (cmd == "x")
      d.buffer.state.disabled = !d.buffer.state.disabled;
    else if (cmd == "s")
      d.set_search_matches(
          d.search_matches().empty()
              ? std::vector<tuivory::DocumentRange>{{0,
                                                     std::min<std::size_t>(
                                                         2, tuivory::graphemes(
                                                                d.buffer.value)
                                                                .size())}}
              : std::vector<tuivory::DocumentRange>{});
    else if (cmd == "m") {
      syntax_enabled_ = false;
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
