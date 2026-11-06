#pragma once
#include "tuivory.hpp"
class SurfaceDemo {
  bool en_;
  int index_ = 1;
  tuivory::Text input_;
  std::string word(const std::string &ko, const std::string &en) const {
    return en_ ? en : ko;
  }

public:
  explicit SurfaceDemo(bool en)
      : en_(en), input_(word("읽기 전용", "Read only")) {
    input_.state.read_only = true;
  }
  void draw(tuivory::Canvas &c, tuivory::Rect area, bool) {
    using namespace tuivory;
    const char *roles[] = {"surface", "editor", "field", "button.focus"};
    Surface{roles[index_]}.draw(
        c, {area.x, area.y, area.width, std::max(0, area.height - 1)},
        [&](Canvas &child) {
          int w = child.width;
          child.write(0, 0, word("바탕 위 문구", "Body on surface"), "body",
                      false, w);
          child.write(0, 1, word("보조 설명", "Secondary"), "hint", false, w);
          child.write(0, 2, word("정상 상태", "Success"), "success", false, w);
          Chip off;
          off.id = "off";
          off.label = word("비활성", "Disabled");
          off.state.disabled = true;
          off.draw(child, {0, 3, w, 1});
          Badge selected;
          selected.label = word("선택", "Selected");
          selected.count = 0;
          selected.state.selected = true;
          selected.draw(child, {0, 4, w, 1});
          Chip edited;
          edited.id = "edited";
          edited.label = word("수정", "Edited");
          edited.state.edited = true;
          edited.draw(child, {0, 5, w, 1});
          input_.draw(child, {0, 6, w, 1}, false);
          Help({{"s", word("바탕 변경", "Change surface")}})
              .draw(child, {0, 8, w, 1});
        });
    const char *ko[] = {"패널", "편집", "입력", "포커스 버튼"},
               *en[] = {"panel", "editor", "field", "focused button"};
    if (area.height)
      c.write(area.x, area.y + area.height - 1,
              word("바탕: ", "Surface: ") + (en_ ? en[index_] : ko[index_]),
              "hint", false, area.width);
  }
  void handle(const std::string &action, const std::string &text = "") {
    if ((action == "insert" ? text : action) == "s")
      index_ = (index_ + 1) % 4;
  }
  void pointer(int, int, int) {}
};
