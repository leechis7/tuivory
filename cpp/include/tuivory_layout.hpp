#pragma once
#include <set>
namespace tuivory {
namespace detail {
inline int layout_extent(int value, int maximum = 1000000000) {
  if (value < 0 || value > maximum)
    throw std::invalid_argument("invalid layout extent");
  return value;
}
inline void layout_rect(Rect r) {
  for (int v : {r.x, r.y, r.width, r.height})
    layout_extent(v);
}
inline bool layout_space(unsigned cp) {
  return (cp >= 9 && cp <= 13) || cp == 32 || cp == 0x85 || cp == 0xa0 ||
         cp == 0x1680 || (cp >= 0x2000 && cp <= 0x200a) || cp == 0x2028 ||
         cp == 0x2029 || cp == 0x202f || cp == 0x205f || cp == 0x3000;
}
inline std::string shortcut_key(const std::string &key) {
  auto text = clean(key);
  std::size_t p = 0, start = text.size(), end = 0;
  while (p < text.size()) {
    auto before = p;
    unsigned cp = decode(text, p);
    if (!layout_space(cp)) {
      start = std::min(start, before);
      end = p;
    }
  }
  return fold(end > start ? text.substr(start, end - start) : "");
}
} // namespace detail
struct SpacingTokens {
  int gap = 0, padding = 0, control_gap = 1, compact_below = 80;
  static SpacingTokens for_width(const std::string &density, int columns) {
    detail::layout_extent(columns);
    if (density != "auto" && density != "compact" && density != "comfortable")
      throw std::invalid_argument("invalid density");
    return density == "compact" || (density == "auto" && columns < 80)
               ? SpacingTokens{}
               : SpacingTokens{2, 1, 2, 80};
  }
};
inline Rect inset_rect(Rect r, int padding) {
  detail::layout_rect(r);
  detail::layout_extent(padding, 1024);
  return {r.x + std::min(padding, r.width), r.y + std::min(padding, r.height),
          std::max(0, r.width - 2 * padding),
          std::max(0, r.height - 2 * padding)};
}
struct StackItem {
  std::string id;
  int min = 1, preferred = 0, weight = 1;
};
struct StackSlot {
  std::string id;
  int start = 0, size = 0;
};
struct StackResult {
  std::vector<StackSlot> slots;
  std::vector<std::string> hidden;
  int gap = 0;
};
inline StackResult stack_layout(const std::vector<StackItem> &items, int total,
                                int gap = 0) {
  detail::layout_extent(total);
  detail::layout_extent(gap, 1024);
  if (items.size() > 1024)
    throw std::invalid_argument("too many stack items");
  std::set<std::string> ids;
  long long minimum = 0;
  for (const auto &i : items) {
    if (i.id.empty() || !ids.insert(i.id).second ||
        !detail::layout_extent(i.min, 1000000))
      throw std::invalid_argument("invalid stack minimum/ID");
    detail::layout_extent(i.preferred, 1000000);
    detail::layout_extent(i.weight, 1000000);
    minimum += i.min;
  }
  if (items.empty())
    return {};
  int gaps = gap * static_cast<int>(items.size() - 1);
  if (gaps > total || total - gaps < minimum)
    gap = 0;
  int available = total - gap * static_cast<int>(items.size() - 1);
  std::vector<int> sizes(items.size());
  std::vector<bool> active(items.size());
  for (std::size_t n = 0; n < items.size(); n++) {
    const auto &i = items[n];
    if (i.min > available && n > 0)
      continue;
    sizes[n] = std::min(i.min, available);
    available -= sizes[n];
    active[n] = true;
  }
  for (std::size_t n = 0; n < items.size(); n++)
    if (active[n]) {
      int add = std::min(std::max(0, items[n].preferred - sizes[n]), available);
      sizes[n] += add;
      available -= add;
    }
  long long weights = 0;
  for (std::size_t n = 0; n < items.size(); n++)
    if (active[n])
      weights += items[n].weight;
  if (weights) {
    int extra = available;
    for (std::size_t n = 0; n < items.size(); n++)
      if (active[n]) {
        int add = static_cast<int>(static_cast<long long>(extra) *
                                   items[n].weight / weights);
        sizes[n] += add;
        available -= add;
      }
    for (std::size_t n = 0; n < items.size(); n++)
      if (available && active[n] && items[n].weight) {
        sizes[n]++;
        available--;
      }
  }
  StackResult result;
  result.gap = gap;
  int start = 0, visible = 0;
  for (std::size_t n = 0; n < items.size(); n++) {
    if (!sizes[n])
      result.hidden.push_back(items[n].id);
    else {
      if (visible)
        start += gap;
      visible++;
    }
    result.slots.push_back({items[n].id, start, sizes[n]});
    start += sizes[n];
  }
  return result;
}
struct NamedRect {
  std::string id;
  Rect rect;
};
struct LayoutResult {
  std::vector<NamedRect> rects;
  std::vector<std::string> hidden;
};
inline LayoutResult stack_rects(Rect parent,
                                const std::vector<StackItem> &items,
                                SpacingTokens tokens = {},
                                bool vertical = false) {
  auto inner = inset_rect(parent, tokens.padding);
  auto result =
      stack_layout(items, vertical ? inner.height : inner.width, tokens.gap);
  LayoutResult out;
  for (const auto &s : result.slots) {
    Rect r = vertical ? Rect{inner.x, inner.y + s.start, inner.width, s.size}
                      : Rect{inner.x + s.start, inner.y, s.size, inner.height};
    out.rects.push_back({s.id, r});
    if (!r.width || !r.height)
      out.hidden.push_back(s.id);
  }
  return out;
}
struct DrawerPlacement {
  Rect rect;
  bool overlay = false;
};
inline DrawerPlacement drawer_layout(Rect parent, int preferred,
                                     int min_content = 0) {
  detail::layout_rect(parent);
  detail::layout_extent(preferred);
  detail::layout_extent(min_content);
  return {
      {parent.x, parent.y, std::min(parent.width, preferred), parent.height},
      parent.width < preferred + min_content};
}
struct Badge {
  std::string id, label;
  std::optional<std::uint64_t> count;
  std::uint64_t limit = 99;
  State state;
  FeedbackRow line(int width) const {
    detail::layout_extent(width, 65535);
    feedback_number(limit);
    auto text = label;
    if (count) {
      feedback_number(*count);
      auto cap = limit ? limit : 99;
      text +=
          " [" +
          (*count > cap ? std::to_string(cap) + "+" : std::to_string(*count)) +
          "]";
    }
    auto markers = state.markers();
    if (!markers.empty() && markers[0] == '-')
      markers.erase(0, 1);
    return {id, clip(markers + text, width, true), state.role(), false, {}};
  }
  void draw(Canvas &c, Rect r) const {
    feedback_draw(c, r, {line(std::max(0, r.width))});
  }
};
struct Chip {
  std::string id, label;
  State state;
  bool removable = false;
  FeedbackRow line(int width) const {
    detail::layout_extent(width, 65535);
    auto markers = state.markers();
    if (!markers.empty() && markers[0] == '-')
      markers.erase(0, 1);
    auto prefix = markers + "[";
    std::string suffix = removable ? "] x" : "]";
    auto text =
        clip(prefix +
                 clip(label, std::max(0, width - cells(prefix) - cells(suffix)),
                      true) +
                 suffix,
             width, true);
    std::vector<FeedbackSpan> spans;
    if (removable && text.size() >= 2 &&
        text.compare(text.size() - 2, 2, " x") == 0)
      spans.push_back({cells(text) - 1, 1, "x",
                       state.editable() ? state.role() : "disabled", "remove",
                       !state.editable()});
    return {id, text, state.role(), false, std::move(spans)};
  }
  Event request_remove() const {
    return !id.empty() && removable && state.editable()
               ? Event{"remove", id, ""}
               : Event{};
  }
  void draw(Canvas &c, Rect r) const {
    feedback_draw(c, r, {line(std::max(0, r.width))});
  }
};
struct Shortcut {
  std::string key, text;
  int priority = 0;
  bool disabled = false;
};
class Help {
  std::vector<Shortcut> items_;

public:
  explicit Help(std::vector<Shortcut> items) : items_(std::move(items)) {
    if (items_.size() > 65536)
      throw std::invalid_argument("too many shortcuts");
    std::set<std::string> keys;
    for (const auto &i : items_) {
      auto key = detail::shortcut_key(i.key);
      if (key.empty() || !keys.insert(key).second)
        throw std::invalid_argument("empty or duplicate shortcut");
    }
    std::stable_sort(items_.begin(), items_.end(),
                     [](const Shortcut &a, const Shortcut &b) {
                       return a.priority > b.priority;
                     });
  }
  std::vector<FeedbackRow> layout(int width, int height) const {
    detail::layout_extent(width, 65535);
    detail::layout_extent(height, 4096);
    auto limit = items_.size() > static_cast<std::size_t>(height) && height > 1
                     ? height - 1
                     : height;
    std::vector<FeedbackRow> rows;
    for (std::size_t i = 0;
         i < std::min(items_.size(), static_cast<std::size_t>(limit)); i++) {
      const auto &s = items_[i];
      rows.push_back({"",
                      clip("[" + s.key + "] " + s.text, width, true),
                      s.disabled ? "disabled" : "body",
                      false,
                      {}});
    }
    if (items_.size() > static_cast<std::size_t>(limit) &&
        height > static_cast<int>(rows.size()))
      rows.push_back(
          {"",
           clip("+" + std::to_string(items_.size() - limit), width, true),
           "hint",
           false,
           {}});
    return rows;
  }
  void draw(Canvas &c, Rect r) const {
    feedback_draw(c, r, layout(std::max(0, r.width), std::max(0, r.height)));
  }
};
} // namespace tuivory
