#pragma once
// Internal part of the single tuivory.hpp entry point.
namespace tuivory {
struct Tab {
  std::string id, title;
  bool edited = false, closable = false, disabled = false;
};
struct TabCell {
  std::string id, text;
  int start = 0, width = 0;
  bool active = false, focused = false, disabled = false;
};
class Tabs {
  std::vector<Tab> items_;
  void reconcile() {
    std::vector<std::string> ids;
    for (const auto &t : items_)
      if (!t.disabled)
        ids.push_back(t.id);
    if (std::find(ids.begin(), ids.end(), active) == ids.end())
      active = ids.empty() ? "" : ids.front();
    if (std::find(ids.begin(), ids.end(), focused) == ids.end())
      focused = active;
  }
  static int item_width(const Tab &t) {
    return std::clamp(cells(t.title) + 5, 6, 24);
  }

public:
  std::string active, focused;
  int first = 0;
  explicit Tabs(std::vector<Tab> items) : items_(std::move(items)) {
    std::set<std::string> ids;
    for (const auto &t : items_)
      if (t.id.empty() || !ids.insert(t.id).second)
        throw std::invalid_argument("empty/duplicate tab ID");
    reconcile();
  }
  const std::vector<Tab> &items() const { return items_; }
  Event handle(const std::string &action) {
    reconcile();
    std::vector<const Tab *> enabled;
    for (const auto &t : items_)
      if (!t.disabled)
        enabled.push_back(&t);
    if (enabled.empty())
      return {};
    int i = 0;
    while (enabled[i]->id != focused)
      i++;
    if (action == "activate") {
      active = focused;
      return {"activate", active, {}};
    }
    if (action == "close")
      return enabled[i]->closable ? Event{"close", focused, {}} : Event{};
    int target = i;
    if (action == "previous")
      target = std::max(0, i - 1);
    else if (action == "next")
      target = std::min(static_cast<int>(enabled.size()) - 1, i + 1);
    else if (action == "first")
      target = 0;
    else if (action == "last")
      target = static_cast<int>(enabled.size()) - 1;
    if (target != i) {
      focused = enabled[target]->id;
      return {"focus", focused, {}};
    }
    return {};
  }
  std::vector<TabCell> layout(int width) {
    reconcile();
    if (width <= 2 || items_.empty())
      return {};
    int target = 0;
    for (std::size_t i = 0; i < items_.size(); i++)
      if (items_[i].id == focused)
        target = static_cast<int>(i);
    first = std::clamp(first, 0, target);
    auto sum = [&](int start) {
      int w = 0;
      for (int i = start; i <= target; i++)
        w += item_width(items_[i]);
      return w;
    };
    while (first < target && sum(first) > width - 2)
      first++;
    while (first > 0 && sum(first - 1) <= width - 2)
      first--;
    std::vector<TabCell> out;
    int x = 1;
    for (std::size_t i = first; i < items_.size() && x < width - 1; i++) {
      const auto &t = items_[i];
      int w = std::min(item_width(t), width - 1 - x);
      if (w < 4 && !out.empty())
        break;
      bool a = t.id == active, f = t.id == focused;
      auto suffix =
          std::string(t.edited ? " *" : "") + (t.closable ? " x" : "");
      auto text = clip(
          std::string(f ? ">" : " ") + (a ? "[" : " ") +
              clip(t.title,
                   std::max(0, w - 3 - static_cast<int>(suffix.size())), true) +
              suffix + (a ? "]" : " "),
          w, true);
      out.push_back({t.id, text, x, w, a, f, t.disabled});
      x += w;
    }
    return out;
  }
  Event click(int x, int width) {
    auto views = layout(width);
    if (x == 0 && first > 0)
      return handle("previous");
    if (width > 0 && x == width - 1 &&
        first + static_cast<int>(views.size()) <
            static_cast<int>(items_.size()))
      return handle("next");
    for (const auto &v : views)
      if (x >= v.start && x < v.start + v.width && !v.disabled) {
        focused = v.id;
        bool close =
            v.text.size() >= 2 && (v.text.substr(v.text.size() - 2) == "x]" ||
                                   v.text.substr(v.text.size() - 2) == "x ");
        if (close &&
            std::any_of(
                items_.begin(), items_.end(),
                [&](const auto &t) { return t.id == v.id && t.closable; }) &&
            x == v.start + cells(v.text) - 2)
          return {"close", v.id, {}};
        active = v.id;
        return {"activate", v.id, {}};
      }
    return {};
  }
  void draw(Canvas &c, Rect r, bool has_focus = true, bool ascii = false) {
    (void)ascii;
    c.fill(r);
    auto views = layout(r.width);
    if (first > 0)
      c.write(r.x, r.y, "<", "hint");
    if (first + static_cast<int>(views.size()) <
            static_cast<int>(items_.size()) &&
        r.width > 0)
      c.write(r.x + r.width - 1, r.y, ">", "hint");
    for (const auto &v : views) {
      c.write(r.x + v.start, r.y, std::string(v.width, ' '),
              v.disabled ? "disabled"
              : v.active ? "selection"
                         : "body",
              has_focus && v.focused, v.width);
      c.write(r.x + v.start, r.y, v.text,
              v.disabled ? "disabled"
              : v.active ? "selection"
                         : "body",
              has_focus && v.focused, v.width);
    }
  }
};
struct SplitLayout {
  int first = 0, divider = 0, second = 0;
  bool compact = false;
};
class Split {
public:
  int preferred = 0, first_min = 1, second_min = 1;
  Split(int first = 1, int second = 1, int size = 0)
      : preferred(size), first_min(std::max(1, first)),
        second_min(std::max(1, second)) {}
  SplitLayout layout(int total) const {
    if (total < 0)
      throw std::invalid_argument("negative split size");
    if (static_cast<long long>(total) <
        static_cast<long long>(first_min) + second_min + 1)
      return {0, 0, total, true};
    int first = std::clamp(preferred ? preferred : (total - 1) / 2, first_min,
                           total - 1 - second_min);
    return {first, 1, total - first - 1, false};
  }
  bool resize(int total, int position) {
    auto old = layout(total);
    if (old.compact)
      return false;
    preferred = std::clamp(position, first_min, total - 1 - second_min);
    return old.first != preferred;
  }
};
struct LineRun {
  std::string text, role, id;
  int start = 0, width = 0;
};
struct LineLayout {
  std::vector<LineRun> runs;
  std::size_t omitted = 0;
  std::string text() const {
    std::string out;
    for (const auto &r : runs)
      out += r.text;
    return out;
  }
  std::string hit(int x) const {
    for (const auto &r : runs)
      if (x >= r.start && x < r.start + r.width)
        return r.id;
    return {};
  }
  void draw(Canvas &canvas, Rect area) const {
    canvas.fill(area);
    for (const auto &r : runs)
      canvas.write(area.x + r.start, area.y, r.text, r.role, false,
                   std::max(0, area.width - r.start));
  }
};
struct PathItem {
  std::string id, label;
};
inline std::string tail_cells(const std::string &text, int width) {
  if (cells(text) <= width)
    return clip(text, width);
  if (width <= 0)
    return {};
  const auto gs = graphemes(text);
  std::size_t start = gs.size();
  int used = 0;
  while (start > 0 && used + gs[start - 1].width <= width - 1)
    used += gs[--start].width;
  std::string out = "~";
  for (; start < gs.size(); start++)
    out += gs[start].text;
  return out;
}
inline LineLayout breadcrumbs(const std::vector<PathItem> &items, int width) {
  LineLayout out;
  if (items.empty() || width <= 0)
    return out;
  int x = 0;
  auto add = [&](const std::string &text, const std::string &id,
                 const std::string &role) {
    auto value = clip(text, cells(text));
    out.runs.push_back({value, role, id, x, cells(value)});
    x += cells(value);
  };
  std::int64_t full = 3 * static_cast<std::int64_t>(items.size() - 1);
  for (const auto &p : items)
    full += cells(p.label);
  if (full <= width) {
    for (std::size_t i = 0; i < items.size(); i++) {
      if (i)
        add(" / ", "", "hint");
      add(items[i].label, items[i].id, i + 1 == items.size() ? "body" : "hint");
    }
    return out;
  }
  const auto &last = items.back();
  std::string prefix;
  if (items.size() > 2 &&
      cells(items.front().label) + 9 + cells(last.label) <= width) {
    add(items.front().label, items.front().id, "hint");
    prefix = " / ... / ";
  } else if (items.size() > 1 && width >= 7)
    prefix = "... / ";
  add(prefix, "", "hint");
  add(tail_cells(last.label, width - x), last.id, "body");
  return out;
}
struct StatusItem {
  std::string id, text, role = "hint";
  int priority = 0;
};
inline LineLayout status_line(std::vector<StatusItem> items, int width) {
  std::stable_sort(
      items.begin(), items.end(),
      [](const auto &a, const auto &b) { return a.priority > b.priority; });
  LineLayout out;
  out.omitted = items.size();
  if (width <= 0)
    return out;
  int x = 0;
  std::size_t included = 0;
  auto add = [&](const std::string &text, const std::string &role,
                 const std::string &id) {
    out.runs.push_back({text, role, id, x, cells(text)});
    x += cells(text);
  };
  for (std::size_t i = 0; i < items.size(); i++) {
    const auto &item = items[i];
    int reserve =
        i + 1 < items.size()
            ? static_cast<int>(
                  std::string(" +" + std::to_string(items.size() - i - 1))
                      .size())
            : 0;
    std::string sep = included ? " | " : "",
                prefix = item.role == "error" || item.role == "warning" ? "! "
                         : item.role == "edited"                        ? "* "
                         : item.role == "success"                       ? "+ "
                         : item.role == "info"                          ? "i "
                                                                        : "",
                text = prefix + clip(item.text, cells(item.text));
    int needed = cells(sep) + cells(text);
    if (needed + reserve > width - x) {
      if (included)
        break;
      int available = width - reserve > 0 ? width - reserve : width;
      text = available == 1 && !prefix.empty() ? prefix.substr(0, 1)
                                               : clip(text, available, true);
      sep.clear();
    }
    if (!sep.empty())
      add(sep, "hint", "");
    add(text, item.role.empty() ? "body" : item.role, item.id);
    included++;
    if (needed + reserve > width)
      break;
  }
  out.omitted = items.size() - included;
  const auto marker = " +" + std::to_string(out.omitted);
  if (out.omitted && x + static_cast<int>(marker.size()) <= width)
    add(marker, "hint", "");
  return out;
}
} // namespace tuivory
