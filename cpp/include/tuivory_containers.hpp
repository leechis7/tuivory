#ifndef TUIVORY_CONTAINERS_HPP
#define TUIVORY_CONTAINERS_HPP
#include <functional>
namespace tuivory {
struct Track {
  int min = 0, max = 0, fixed = 0, weight = 0;
};
struct LayoutItem {
  std::string id;
  Track track;
  int row = 0, column = 0, row_span = 0, column_span = 0;
  bool hidden = false, disabled = false;
  std::string drawer;
  bool modal = false, centered = false;
  Rect area;
};
struct ContainerOptions {
  std::string kind = "row";
  int gap = 0, padding = 0;
  std::vector<Track> rows, columns;
  int virtual_width = 0, virtual_height = 0;
};
namespace container_detail {
inline void number(int n, int max = 1000000) {
  if (n < 0 || n > max)
    throw std::invalid_argument("invalid container constraints");
}
inline void track(Track t) {
  for (int n : {t.min, t.max, t.fixed, t.weight})
    number(n);
  if (t.max && (t.max < t.min || t.fixed > t.max))
    throw std::invalid_argument("invalid track maximum");
}
inline std::pair<std::vector<int>, int> allocate(std::vector<Track> tracks,
                                                 int total, int gap) {
  if (tracks.empty())
    return {{}, 0};
  for (auto &t : tracks)
    if (!t.min && !t.max && !t.fixed && !t.weight)
      t.weight = 1;
  gap = std::min(gap, total / static_cast<int>(tracks.size()));
  int available = total - gap * (static_cast<int>(tracks.size()) - 1);
  long long minimum = 0;
  for (auto t : tracks)
    minimum += std::max(t.min, t.fixed);
  if (minimum > available) {
    gap = 0;
    available = total;
  }
  std::vector<int> sizes;
  for (auto t : tracks) {
    int size = std::min(available, std::max(t.min, t.fixed));
    sizes.push_back(size);
    available -= size;
  }
  while (available) {
    long long weight = 0;
    for (std::size_t n = 0; n < tracks.size(); n++) {
      auto t = tracks[n];
      if (!t.fixed && t.weight && (!t.max || sizes[n] < t.max))
        weight += t.weight;
    }
    if (!weight)
      break;
    int budget = available;
    for (std::size_t n = 0; n < tracks.size(); n++) {
      auto t = tracks[n];
      if (t.fixed || !t.weight || (t.max && sizes[n] >= t.max))
        continue;
      int add = std::min(
          available,
          std::max(1, static_cast<int>((long long)budget * t.weight / weight)));
      if (t.max)
        add = std::min(add, t.max - sizes[n]);
      sizes[n] += add;
      available -= add;
    }
  }
  return {sizes, gap};
}
} // namespace container_detail
inline std::vector<NamedRect>
compute_container(Rect bounds, const std::vector<LayoutItem> &items,
                  const ContainerOptions &o = {}) {
  using container_detail::number;
  for (int v : {bounds.x, bounds.y, bounds.width, bounds.height,
                o.virtual_width, o.virtual_height})
    number(v);
  number(o.gap, 1024);
  number(o.padding, 1024);
  if ((o.kind != "row" && o.kind != "column" && o.kind != "grid" &&
       o.kind != "layers") ||
      items.size() > 1024 || o.rows.size() > 1024 || o.columns.size() > 1024)
    throw std::invalid_argument("invalid container kind/count");
  for (auto t : o.rows)
    container_detail::track(t);
  for (auto t : o.columns)
    container_detail::track(t);
  std::set<std::string> seen;
  std::vector<LayoutItem> visible;
  for (const auto &i : items) {
    if (i.id.empty() || !seen.insert(i.id).second)
      throw std::invalid_argument("invalid container ID");
    container_detail::track(i.track);
    for (int v : {i.row, i.column, i.row_span, i.column_span, i.area.x,
                  i.area.y, i.area.width, i.area.height})
      number(v);
    if (!i.drawer.empty() && (o.kind != "layers" || i.centered ||
                              (i.drawer != "left" && i.drawer != "right")))
      throw std::invalid_argument("invalid drawer");
    if (!i.hidden)
      visible.push_back(i);
  }
  auto inner = inset_rect(bounds, o.padding);
  std::vector<NamedRect> out;
  if (o.kind == "row" || o.kind == "column") {
    bool horizontal = o.kind == "row";
    int total = horizontal ? inner.width : inner.height, at = 0;
    std::vector<Track> tracks;
    for (const auto &i : visible)
      tracks.push_back(i.track);
    auto allocation = container_detail::allocate(tracks, total, o.gap);
    for (std::size_t n = 0; n < visible.size(); n++) {
      at = std::min(at, total);
      int size = allocation.first[n];
      out.push_back({visible[n].id,
                     horizontal
                         ? Rect{inner.x + at, inner.y, size, inner.height}
                         : Rect{inner.x, inner.y + at, inner.width, size}});
      at += size + allocation.second;
    }
  } else if (o.kind == "grid") {
    auto widths = container_detail::allocate(o.columns, inner.width, o.gap),
         heights = container_detail::allocate(o.rows, inner.height, o.gap);
    for (const auto &i : visible) {
      int rs = std::max(1, i.row_span), cs = std::max(1, i.column_span);
      if ((std::size_t)(i.row + rs) > heights.first.size() ||
          (std::size_t)(i.column + cs) > widths.first.size())
        throw std::invalid_argument("invalid grid span");
      int x = 0, y = 0, w = widths.second * (cs - 1),
          h = heights.second * (rs - 1);
      for (int n = 0; n < i.column; n++)
        x += widths.first[n] + widths.second;
      for (int n = 0; n < i.row; n++)
        y += heights.first[n] + heights.second;
      for (int n = i.column; n < i.column + cs; n++)
        w += widths.first[n];
      for (int n = i.row; n < i.row + rs; n++)
        h += heights.first[n];
      out.push_back({i.id,
                     {inner.x + std::min(x, inner.width),
                      inner.y + std::min(y, inner.height),
                      std::min(w, std::max(0, inner.width - x)),
                      std::min(h, std::max(0, inner.height - y))}});
    }
  } else {
    for (const auto &i : visible) {
      int ax = std::min(i.area.x, inner.width),
          ay = std::min(i.area.y, inner.height), w = inner.width - ax,
          h = inner.height - ay, x = inner.x + ax, y = inner.y + ay;
      if (i.area.width)
        w = std::min(w, i.area.width);
      if (i.area.height)
        h = std::min(h, i.area.height);
      if (i.centered) {
        x = inner.x + (inner.width - w) / 2;
        y = inner.y + (inner.height - h) / 2;
      }
      if (!i.drawer.empty()) {
        w = std::min(inner.width, i.area.width ? i.area.width : inner.width);
        x = inner.x + (i.drawer == "right" ? inner.width - w : 0);
      }
      out.push_back({i.id, {x, y, w, h}});
    }
  }
  return out;
}
class ContainerState {
  std::string modal_;
  std::map<std::string, std::string> restore_;

public:
  std::string focused, captured;
  std::vector<std::string>
  eligible(const std::vector<LayoutItem> &items) const {
    std::size_t start = 0;
    for (std::size_t n = 0; n < items.size(); n++)
      if (items[n].modal && !items[n].hidden)
        start = n;
    std::vector<std::string> ids;
    for (auto n = start; n < items.size(); n++)
      if (!items[n].hidden && !items[n].disabled)
        ids.push_back(items[n].id);
    return ids;
  }
  void reconcile(const std::vector<LayoutItem> &items) {
    auto ids = eligible(items);
    auto has = [&](const std::string &id) {
      return std::find(ids.begin(), ids.end(), id) != ids.end();
    };
    std::string modal;
    bool old_visible = false;
    for (const auto &i : items) {
      if (i.modal && !i.hidden) {
        modal = i.id;
        if (i.id == modal_)
          old_visible = true;
      }
    }
    if (modal != modal_) {
      if (!modal_.empty() && !old_visible) {
        auto it = restore_.find(modal_);
        std::string previous;
        if (it != restore_.end()) {
          previous = it->second;
          restore_.erase(it);
        }
        auto count = restore_.size() + 1;
        for (std::size_t n = 0; n < count; n++) {
          if (has(previous)) {
            focused = previous;
            break;
          }
          auto next = restore_.find(previous);
          if (next == restore_.end())
            break;
          previous = next->second;
          restore_.erase(next);
        }
      }
      if (!modal.empty())
        restore_.emplace(modal, focused);
      modal_ = modal;
    }
    if (!has(focused))
      focused = ids.empty() ? "" : ids.front();
    if (!has(captured))
      captured.clear();
  }
  std::string move_focus(const std::vector<LayoutItem> &items,
                         bool previous = false) {
    reconcile(items);
    auto ids = eligible(items);
    if (!ids.empty()) {
      auto at = std::find(ids.begin(), ids.end(), focused) - ids.begin();
      focused = ids[(at + (previous ? ids.size() - 1 : 1)) % ids.size()];
    }
    return focused;
  }
  std::string hit(const std::vector<LayoutItem> &items,
                  const std::vector<NamedRect> &rects, int x, int y) const {
    auto ids = eligible(items);
    for (auto i = rects.rbegin(); i != rects.rend(); ++i)
      if (std::find(ids.begin(), ids.end(), i->id) != ids.end() &&
          i->rect.contains(x, y))
        return i->id;
    return "";
  }
  std::string pointer(const std::vector<LayoutItem> &items,
                      const std::vector<NamedRect> &rects, int x, int y,
                      bool press = false, bool release = false) {
    reconcile(items);
    auto id = captured.empty() ? hit(items, rects, x, y) : captured;
    if (press && !id.empty()) {
      focused = id;
      captured = id;
    }
    if (release)
      captured.clear();
    return id;
  }
};
class Container {
  std::vector<LayoutItem> items_;
  ContainerOptions options_;
  std::vector<NamedRect> rects_;
  Rect bounds_;
  int sx_ = 0, sy_ = 0;

public:
  ContainerState state;
  int scroll_x = 0, scroll_y = 0;
  explicit Container(std::vector<LayoutItem> items,
                     ContainerOptions options = {}) {
    set_items(std::move(items), std::move(options));
  }
  std::vector<LayoutItem> items() const { return items_; }
  ContainerOptions options() const { return options_; }
  void set_items(std::vector<LayoutItem> items, ContainerOptions options) {
    compute_container({0, 0, 1, 1}, items, options);
    items_ = std::move(items);
    options_ = std::move(options);
    rects_.clear();
    bounds_ = {};
    state.reconcile(items_);
    state.captured.clear();
  }
  void set_items(std::vector<LayoutItem> items) {
    set_items(std::move(items), options_);
  }
  std::vector<NamedRect> draw(
      Canvas &canvas, Rect bounds,
      const std::function<void(const std::string &, Canvas &, bool)> &painter) {
    for (int v :
         {bounds.x, bounds.y, bounds.width, bounds.height, scroll_x, scroll_y})
      container_detail::number(v);
    int vw = std::max(bounds.width, options_.virtual_width),
        vh = std::max(bounds.height, options_.virtual_height);
    if ((long long)vw * vh > 1000000)
      throw std::invalid_argument("container virtual area exceeds limit");
    int sx = std::min(scroll_x, std::max(0, vw - bounds.width)),
        sy = std::min(scroll_y, std::max(0, vh - bounds.height));
    auto rects = compute_container({0, 0, vw, vh}, items_, options_);
    Canvas virtual_canvas(vw, vh, canvas.palette);
    state.reconcile(items_);
    for (const auto &n : rects) {
      auto r = n.rect;
      if (!r.width || !r.height)
        continue;
      Canvas child(r.width, r.height, canvas.palette);
      child.blit(virtual_canvas, r, 0, 0);
      child.clear_cursor();
      bool focused = n.id == state.focused;
      painter(n.id, child, focused);
      if (!focused)
        child.clear_cursor();
      virtual_canvas.blit(child, {0, 0, r.width, r.height}, r.x, r.y);
    }
    canvas.blit(virtual_canvas, {sx, sy, bounds.width, bounds.height}, bounds.x,
                bounds.y);
    scroll_x = sx;
    scroll_y = sy;
    sx_ = sx;
    sy_ = sy;
    bounds_ = bounds;
    rects_ = rects;
    return rects;
  }
  std::string pointer(int x, int y, bool press = false, bool release = false) {
    if (!bounds_.contains(x, y) && state.captured.empty())
      return "";
    return state.pointer(items_, rects_, x - bounds_.x + sx_,
                         y - bounds_.y + sy_, press, release);
  }
};
} // namespace tuivory
#endif
