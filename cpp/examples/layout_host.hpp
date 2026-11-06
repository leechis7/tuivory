#pragma once
#include "tuivory.hpp"
// Hosts choose contents/global keys and decide whether to accept removal.
class LayoutDemo {
  bool en_, active_ = true;
  std::string density_ = "auto", status_;
  tuivory::Chip filter_, readonly_, disabled_;
  struct Hit {
    tuivory::Rect rect;
    int chip;
    bool disabled;
  };
  std::vector<Hit> hits_;
  std::string word(const std::string &ko, const std::string &en) const {
    return en_ ? en : ko;
  }
  void apply(const tuivory::Event &e) {
    if (e.kind == "remove" && e.id == "filter" && active_) {
      active_ = false;
      hits_.clear();
      status_ = word("필터를 제거했습니다.", "Filter removed.");
    }
  }

public:
  explicit LayoutDemo(bool en) : en_(en) {
    filter_.id = "filter";
    filter_.label = word("최근", "Recent");
    filter_.removable = true;
    readonly_.id = "fixed";
    readonly_.label = word("읽기 전용", "Read only");
    readonly_.state.read_only = true;
    readonly_.removable = true;
    disabled_.id = "off";
    disabled_.label = word("비활성", "Disabled");
    disabled_.state.disabled = true;
    disabled_.removable = true;
  }
  void draw(tuivory::Canvas &c, tuivory::Rect area, bool ascii) {
    using namespace tuivory;
    hits_.clear();
    auto tokens = SpacingTokens::for_width(density_, area.width);
    auto layout =
        stack_rects({area.x, area.y, area.width, std::max(0, area.height - 1)},
                    {{"badges", 16, 20, 0}, {"support", 24, 40, 1}}, tokens);
    Badge items;
    items.label = word("항목", "Items");
    items.count = 123;
    Badge selected;
    selected.label = word("선택", "Selected");
    selected.count = 0;
    selected.state.selected = true;
    Badge off;
    off.label = word("비활성", "Disabled");
    off.state.disabled = true;
    for (const auto &named : layout.rects) {
      if (!named.rect.width || !named.rect.height)
        continue;
      auto inner = c.panel(named.rect,
                           named.id == "badges"
                               ? word("배지", "Badges")
                               : word("칩·단축키", "Chips and shortcuts"),
                           false, ascii);
      int y = inner.y;
      if (named.id == "badges") {
        for (const auto &b : {items, selected, off}) {
          if (y >= inner.y + inner.height)
            break;
          b.draw(c, {inner.x, y, inner.width, 1});
          y += 1 + tokens.control_gap;
        }
      } else {
        std::vector<Chip *> chips;
        if (active_)
          chips.push_back(&filter_);
        chips.push_back(&readonly_);
        chips.push_back(&disabled_);
        for (auto *chip : chips) {
          if (y >= inner.y + inner.height)
            break;
          chip->draw(c, {inner.x, y, inner.width, 1});
          for (const auto &s : chip->line(inner.width).spans)
            hits_.push_back({{inner.x + s.start, y, s.width, 1},
                             chip == &filter_     ? 0
                             : chip == &readonly_ ? 1
                                                  : 2,
                             s.disabled});
          y += 1 + tokens.control_gap;
        }
        Help({{"d", word("간격 변경", "Change density"), 10, false},
              {"x", word("필터 제거", "Remove filter"), 5, !active_},
              {"r", word("사용 불가", "Unavailable"), 0, true}})
            .draw(c, {inner.x, y, inner.width,
                      std::max(0, inner.y + inner.height - y)});
      }
    }
    auto label = density_ == "auto"      ? word("자동", "auto")
                 : density_ == "compact" ? word("촘촘", "compact")
                                         : word("여유", "comfortable");
    auto text = status_.empty()
                    ? word("밀도: ", "Density: ") + label +
                          word(" | 숨긴 패널: ", " | Hidden panes: ") +
                          std::to_string(layout.hidden.size())
                    : status_;
    if (area.height)
      c.write(area.x, area.y + area.height - 1, text, "hint", false,
              area.width);
  }
  void handle(const std::string &action, const std::string &text = "") {
    auto command = action == "insert" ? text : action;
    if (command == "x" || command == "activate")
      apply(filter_.request_remove());
    else if (command == "d") {
      density_ = density_ == "comfortable" ? "compact" : "comfortable";
      hits_.clear();
      status_ = density_ == "compact"
                    ? word("밀도: 촘촘", "Density: compact")
                    : word("밀도: 여유", "Density: comfortable");
    }
  }
  void pointer(int x, int y, int button) {
    if (button != 0)
      return;
    for (const auto &hit : hits_)
      if (hit.rect.contains(x, y)) {
        if (!hit.disabled)
          apply((hit.chip == 0   ? filter_
                 : hit.chip == 1 ? readonly_
                                 : disabled_)
                    .request_remove());
        return;
      }
  }
};
