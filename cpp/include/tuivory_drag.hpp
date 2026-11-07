#pragma once
// Independent request-only movement. Hosts approve immutable replacements.
#include <iomanip>
#include <type_traits>
namespace tuivory {
class DropError : public std::invalid_argument {
public:
  std::string reason;
  explicit DropError(std::string why)
      : std::invalid_argument(why), reason(std::move(why)) {}
};
struct DropRequest {
  std::string source_id, target_id, position, revision;
};
struct DragOptions {
  int threshold = 0;
  bool auto_scroll = false, hover_expand = false;
  std::vector<std::string> locked;
};
struct DragPointer {
  std::string action;
  int x = 0, y = 0, width = 0, height = 0;
};
struct DragLayout {
  int first = 0, scroll = 0;
  std::set<std::string> expanded;
  std::vector<TabCell> tabs;
  std::vector<Node> rows;
};
namespace drag_detail {
inline void bounds(int n, int lo, int hi, const char *reason) {
  if (n < lo || n > hi)
    throw DropError(reason);
}
inline DragOptions options(DragOptions o) {
  bounds(o.threshold, 0, 1000000, "options");
  if (o.locked.size() > 65536)
    throw DropError("options");
  for (const auto &id : o.locked)
    if (id.empty())
      throw DropError("options");
  return o;
}
inline bool locked(const DragOptions &o, const std::string &id) {
  return std::find(o.locked.begin(), o.locked.end(), id) != o.locked.end();
}
inline std::string revision(const std::vector<std::string> &parts) {
  std::uint64_t hash = 14695981039346656037ull;
  for (const auto &s : parts) {
    dialog_detail::text(s, 1000000);
    auto input = std::to_string(s.size()) + ":" + s;
    for (unsigned char b : input) {
      hash ^= b;
      hash *= 1099511628211ull;
    }
  }
  std::ostringstream out;
  out << std::hex << std::setw(16) << std::setfill('0') << hash;
  return out.str();
}
inline std::vector<Node> nodes(const Tree &m) {
  auto result = m.nodes();
  for (auto &n : result)
    n.branch = m.is_branch(n.id);
  return result;
}
inline Tabs state(const Tabs &old, Tabs next) {
  next.active = old.active;
  next.focused = old.focused;
  next.first = old.first;
  next.handle("");
  return next;
}
inline Tree state(const Tree &old, Tree next) {
  next.selected = old.selected;
  next.scroll = old.scroll;
  next.horizontal = old.horizontal;
  for (const auto &id : old.expanded)
    if (std::any_of(next.nodes().begin(), next.nodes().end(),
                    [&](const auto &n) { return n.id == id; }))
      next.expanded.insert(id);
  return next;
}
inline std::string state_revision(const Tabs &m) {
  return revision({m.active, m.focused, std::to_string(m.first)});
}
inline std::string state_revision(const Tree &m) {
  std::vector<std::string> parts{m.selected, std::to_string(m.scroll),
                                 std::to_string(m.horizontal)};
  parts.insert(parts.end(), m.expanded.begin(), m.expanded.end());
  return revision(parts);
}
} // namespace drag_detail
inline std::string drag_revision(const Tabs &m) {
  std::vector<std::string> parts;
  for (const auto &t : m.items()) {
    parts.push_back(t.id);
    parts.push_back(t.title);
    parts.push_back(t.edited ? "true" : "false");
    parts.push_back(t.closable ? "true" : "false");
    parts.push_back(t.disabled ? "true" : "false");
  }
  return drag_detail::revision(parts);
}
inline std::string drag_revision(const Tree &m) {
  std::vector<std::string> parts;
  for (const auto &n : drag_detail::nodes(m)) {
    parts.push_back(n.id);
    parts.push_back(n.parent);
    parts.push_back(n.name);
    parts.push_back(n.secondary);
    parts.push_back(n.icon);
    parts.push_back(n.ascii_icon);
    parts.push_back(n.count ? std::to_string(*n.count) : "");
    parts.push_back(n.branch ? "true" : "false");
  }
  return drag_detail::revision(parts);
}
inline Tabs apply_drop(const Tabs &m, const DropRequest &r) {
  if (r.revision != drag_revision(m))
    throw DropError("stale");
  if (r.source_id == r.target_id)
    throw DropError("self");
  if (r.position != "before" && r.position != "after")
    throw DropError("position");
  auto items = m.items();
  auto source = std::find_if(items.begin(), items.end(),
                             [&](auto t) { return t.id == r.source_id; }),
       target = std::find_if(items.begin(), items.end(),
                             [&](auto t) { return t.id == r.target_id; });
  if (source == items.end() || target == items.end())
    throw DropError("missing");
  if (source->disabled || target->disabled)
    throw DropError("disabled");
  auto si = source - items.begin(), ti = target - items.begin();
  auto item = *source;
  items.erase(source);
  if (si < ti)
    --ti;
  if (r.position == "after")
    ++ti;
  if (si == ti)
    throw DropError("unchanged");
  items.insert(items.begin() + ti, std::move(item));
  return drag_detail::state(m, Tabs(std::move(items)));
}
inline Tree apply_drop(const Tree &m, const DropRequest &r) {
  if (r.revision != drag_revision(m))
    throw DropError("stale");
  auto nodes = drag_detail::nodes(m);
  std::map<std::string, std::size_t> index;
  for (std::size_t i = 0; i < nodes.size(); i++)
    index[nodes[i].id] = i;
  if (!index.count(r.source_id) || !index.count(r.target_id))
    throw DropError("missing");
  if (r.source_id == r.target_id)
    throw DropError("self");
  if (r.position != "before" && r.position != "after" && r.position != "inside")
    throw DropError("position");
  auto si = index.at(r.source_id), ti = index.at(r.target_id);
  auto parent = r.target_id;
  while (!parent.empty()) {
    if (parent == r.source_id)
      throw DropError("cycle");
    parent = nodes[index.at(parent)].parent;
  }
  if (r.position == "inside" && !nodes[ti].branch)
    throw DropError("leaf");
  auto end = si + 1;
  while (end < nodes.size() &&
         m.depth_of(nodes[end].id) > m.depth_of(r.source_id))
    end++;
  int extra = 0;
  for (auto i = si; i < end; i++)
    extra = std::max(extra, m.depth_of(nodes[i].id) - m.depth_of(r.source_id));
  if (m.depth_of(r.target_id) + (r.position == "inside" ? 1 : 0) + extra > 128)
    throw DropError("depth");
  std::vector<Node> block(nodes.begin() + si, nodes.begin() + end),
      remaining = nodes;
  remaining.erase(remaining.begin() + si, remaining.begin() + end);
  auto target = std::find_if(remaining.begin(), remaining.end(),
                             [&](auto n) { return n.id == r.target_id; });
  auto at = target - remaining.begin();
  parent = r.position == "inside" ? r.target_id : target->parent;
  if (r.position != "before") {
    at++;
    while (at < (std::ptrdiff_t)remaining.size() &&
           m.depth_of(remaining[at].id) > m.depth_of(r.target_id))
      at++;
  }
  block[0].parent = parent;
  remaining.insert(remaining.begin() + at, block.begin(), block.end());
  bool same = remaining.size() == nodes.size();
  for (std::size_t i = 0; same && i < nodes.size(); i++)
    same = remaining[i].id == nodes[i].id &&
           remaining[i].parent == nodes[i].parent;
  if (same)
    throw DropError("unchanged");
  return drag_detail::state(m, Tree(std::move(remaining)));
}
template <class Model>
DropRequest request_drop(const Model &m, const std::string &source,
                         const std::string &target, const std::string &position,
                         const DragOptions &value = DragOptions{},
                         const DropPolicy &allow = {}) {
  auto o = drag_detail::options(value);
  if (drag_detail::locked(o, source) || drag_detail::locked(o, target))
    throw DropError("locked");
  DropRequest r{source, target, position, drag_revision(m)};
  apply_drop(m, r);
  if (allow) {
    bool accepted = false;
    try {
      accepted = allow(r);
    } catch (...) {
      throw DropError("policy");
    }
    if (!accepted)
      throw DropError("policy");
    if (r.revision != drag_revision(m))
      throw DropError("stale");
  }
  return r;
}
inline DropRequest keyboard_drop(const Tabs &m, const std::string &direction,
                                 const DragOptions &o = DragOptions{},
                                 const DropPolicy &allow = {}) {
  auto source = std::find_if(m.items().begin(), m.items().end(),
                             [&](auto t) { return t.id == m.focused; });
  if (source == m.items().end())
    throw DropError("missing");
  if (direction != "previous" && direction != "next")
    throw DropError("position");
  auto i = source - m.items().begin(),
       j = i + (direction == "previous" ? -1 : 1);
  if (j < 0 || j >= (std::ptrdiff_t)m.items().size())
    throw DropError("missing");
  return request_drop(m, m.focused, m.items()[j].id,
                      direction == "previous" ? "before" : "after", o, allow);
}
inline DropRequest keyboard_drop(const Tree &m, const std::string &direction,
                                 const DragOptions &o = DragOptions{},
                                 const DropPolicy &allow = {}) {
  auto nodes = drag_detail::nodes(m);
  auto source = std::find_if(nodes.begin(), nodes.end(),
                             [&](auto n) { return n.id == m.selected; });
  if (source == nodes.end())
    throw DropError("missing");
  if (direction == "outside" && !source->parent.empty())
    return request_drop(m, source->id, source->parent, "after", o, allow);
  std::vector<Node> siblings;
  for (auto n : nodes)
    if (n.parent == source->parent)
      siblings.push_back(n);
  auto i = std::find_if(siblings.begin(), siblings.end(),
                        [&](auto n) { return n.id == source->id; }) -
           siblings.begin();
  if (direction != "previous" && direction != "next" && direction != "inside")
    throw DropError("position");
  auto j = i + (direction == "next" ? 1 : -1);
  if (j < 0 || j >= (std::ptrdiff_t)siblings.size())
    throw DropError("missing");
  return request_drop(m, source->id, siblings[j].id,
                      direction == "inside" ? "inside"
                      : direction == "next" ? "after"
                                            : "before",
                      o, allow);
}
inline DropRequest Tabs::request_drop(const std::string &s,
                                      const std::string &t,
                                      const std::string &p,
                                      const DragOptions &o,
                                      const DropPolicy &allow) const {
  return tuivory::request_drop(*this, s, t, p, o, allow);
}
inline DropRequest Tabs::request_drop(const std::string &s,
                                      const std::string &t,
                                      const std::string &p) const {
  return tuivory::request_drop(*this, s, t, p);
}
inline Tabs Tabs::apply_drop(const DropRequest &r) const {
  return tuivory::apply_drop(*this, r);
}
inline DropRequest Tabs::keyboard_drop(const std::string &d,
                                       const DragOptions &o,
                                       const DropPolicy &allow) const {
  return tuivory::keyboard_drop(*this, d, o, allow);
}
inline DropRequest Tabs::keyboard_drop(const std::string &d) const {
  return tuivory::keyboard_drop(*this, d);
}
inline DropRequest Tree::request_drop(const std::string &s,
                                      const std::string &t,
                                      const std::string &p,
                                      const DragOptions &o,
                                      const DropPolicy &allow) const {
  return tuivory::request_drop(*this, s, t, p, o, allow);
}
inline DropRequest Tree::request_drop(const std::string &s,
                                      const std::string &t,
                                      const std::string &p) const {
  return tuivory::request_drop(*this, s, t, p);
}
inline Tree Tree::apply_drop(const DropRequest &r) const {
  return tuivory::apply_drop(*this, r);
}
inline DropRequest Tree::keyboard_drop(const std::string &d,
                                       const DragOptions &o,
                                       const DropPolicy &allow) const {
  return tuivory::keyboard_drop(*this, d, o, allow);
}
inline DropRequest Tree::keyboard_drop(const std::string &d) const {
  return tuivory::keyboard_drop(*this, d);
}

class DragState {
  bool busy_ = false;
  std::string render_key_, revision_, state_revision_;
  int x_ = 0, y_ = 0, width_ = 0, height_ = 0, first_ = 0, scroll_ = 0;
  std::set<std::string> expanded_;
  std::optional<DropRequest> request_;
  DragPointer pointer_;
  void reset(const std::string &result_value) {
    phase = "idle";
    result = result_value;
    source_id.clear();
    target_id.clear();
    position.clear();
    reason.clear();
    allowed = false;
    revision_.clear();
    state_revision_.clear();
    x_ = y_ = width_ = height_ = first_ = scroll_ = 0;
    expanded_.clear();
    request_.reset();
    pointer_ = {};
  }
  template <class Model> bool valid(const Model &m, int width, int height) {
    if (!captured())
      return false;
    if (!enabled) {
      reset("cancel");
      return false;
    }
    if (revision_ != drag_revision(m) ||
        state_revision_ != drag_detail::state_revision(m) || width_ != width ||
        height_ != height) {
      reset("stale");
      return false;
    }
    return true;
  }
  std::vector<TabCell> tab_cells(const Tabs &m, int width, int first) const {
    std::vector<TabCell> out;
    int x = 1;
    if (width <= 2)
      return out;
    for (auto i = std::size_t(std::max(0, first)); i < m.items().size(); i++) {
      const auto &t = m.items()[i];
      if (x >= width - 1)
        break;
      int w = std::min(std::clamp(cells(t.title) + 5, 6, 24), width - 1 - x);
      if (w < 4 && !out.empty())
        break;
      bool active = t.id == m.active, focused = t.id == m.focused;
      auto suffix =
          std::string(t.edited ? " *" : "") + (t.closable ? " x" : "");
      auto text = clip(
          std::string(focused ? ">" : " ") + (active ? "[" : " ") +
              clip(t.title, std::max(0, w - 3 - int(suffix.size())), true) +
              suffix + (active ? "]" : " "),
          w, true);
      out.push_back({t.id, text, x, w, active, focused, t.disabled});
      x += w;
    }
    return out;
  }
  std::vector<Node> tree_rows(const Tree &m, int height) {
    auto preview = m;
    preview.expanded = expanded_;
    auto rows = preview.visible();
    scroll_ = std::max(
        0,
        std::min(scroll_, std::max(0, int(rows.size()) - std::max(1, height))));
    return rows;
  }

public:
  bool enabled = false;
  std::string phase = "idle", result, source_id, target_id, position, reason;
  bool allowed = false;
  explicit DragState(bool enabled = false) : enabled(enabled) {}
  bool captured() const { return phase == "armed" || phase == "dragging"; }
  void cancel() {
    if (busy_)
      throw DropError("reentrant");
    reset("cancel");
  }
  void render_key(std::string key) {
    if (busy_)
      throw DropError("reentrant");
    if (captured() && !render_key_.empty() && render_key_ != key)
      reset("stale");
    render_key_ = std::move(key);
  }
  template <class Model>
  DragLayout preview_layout(const Model &m, int width, int height) {
    if (busy_)
      throw DropError("reentrant");
    drag_detail::bounds(width, 0, 65535, "bounds");
    drag_detail::bounds(height, 0, 4096, "bounds");
    DragLayout out;
    if (!valid(m, width, height)) {
      auto preview = m;
      if constexpr (std::is_same_v<Model, Tabs>) {
        out.tabs = preview.layout(width);
        out.first = preview.first;
      } else {
        out.rows = preview.reconcile(height);
        out.scroll = preview.scroll;
        out.expanded = preview.expanded;
      }
      return out;
    }
    if constexpr (std::is_same_v<Model, Tabs>) {
      out.first = first_;
      out.tabs = tab_cells(m, width, first_);
    } else {
      out.rows = tree_rows(m, height);
      out.scroll = scroll_;
      out.expanded = expanded_;
    }
    return out;
  }
  template <class Model>
  std::optional<DropRequest> pointer(const Model &m, DragPointer p,
                                     const DragOptions &value = DragOptions{},
                                     const DropPolicy &policy = {}) {
    if (busy_)
      throw DropError("reentrant");
    auto o = drag_detail::options(value);
    if (p.action != "down" && p.action != "move" && p.action != "up" &&
        p.action != "cancel")
      throw DropError("pointer");
    drag_detail::bounds(p.x, -1000000000, 1000000000, "pointer");
    drag_detail::bounds(p.y, -1000000000, 1000000000, "pointer");
    drag_detail::bounds(p.width, 0, 65535, "pointer");
    drag_detail::bounds(p.height, 0, 4096, "pointer");
    if (p.action == "cancel") {
      cancel();
      return std::nullopt;
    }
    if (!enabled) {
      if (captured())
        reset("cancel");
      return std::nullopt;
    }
    if (p.action == "down") {
      reset("");
      if (p.x < 0 || p.x >= p.width || p.y < 0 || p.y >= p.height)
        return std::nullopt;
      auto preview = m;
      std::string id;
      int first = 0, scroll = 0;
      std::set<std::string> expanded;
      if constexpr (std::is_same_v<Model, Tabs>) {
        if (p.y)
          return std::nullopt;
        for (auto c : preview.layout(p.width))
          if (c.start <= p.x && p.x < c.start + c.width && !c.disabled) {
            id = c.id;
            break;
          }
        first = preview.first;
      } else {
        auto rows = preview.reconcile(p.height);
        auto i = std::size_t(preview.scroll + p.y);
        if (i < rows.size())
          id = rows[i].id;
        scroll = preview.scroll;
        expanded = preview.expanded;
      }
      if (id.empty() || drag_detail::locked(o, id))
        return std::nullopt;
      phase = "armed";
      source_id = id;
      revision_ = drag_revision(m);
      state_revision_ = drag_detail::state_revision(m);
      x_ = p.x;
      y_ = p.y;
      width_ = p.width;
      height_ = p.height;
      first_ = first;
      scroll_ = scroll;
      expanded_ = expanded;
      pointer_ = p;
      return std::nullopt;
    }
    if (!valid(m, p.width, p.height))
      return std::nullopt;
    pointer_ = p;
    if (std::max(std::abs(p.x - x_), std::abs(p.y - y_)) >=
        (o.threshold ? o.threshold : 2))
      phase = "dragging";
    if (phase == "dragging") {
      std::optional<DropRequest> raw;
      std::string error = "outside";
      if constexpr (std::is_same_v<Model, Tabs>) {
        if (o.auto_scroll && p.action == "move") {
          if (p.x <= 0)
            first_ = std::max(0, first_ - 1);
          else if (p.x >= p.width - 1)
            first_ =
                std::min(std::max(0, int(m.items().size()) - 1), first_ + 1);
        }
        for (auto c : tab_cells(m, p.width, first_))
          if (p.x >= 0 && p.x < p.width && p.y == 0 && c.start <= p.x &&
              p.x < c.start + c.width) {
            raw = DropRequest{source_id, c.id,
                              p.x - c.start >= c.width / 2 ? "after" : "before",
                              revision_};
            break;
          }
      } else {
        auto rows = tree_rows(m, p.height);
        if (o.auto_scroll && p.action == "move") {
          if (p.y <= 0)
            scroll_ = std::max(0, scroll_ - 1);
          else if (p.y >= p.height - 1)
            scroll_ =
                std::min(std::max(0, int(rows.size()) - std::max(1, p.height)),
                         scroll_ + 1);
        }
        auto i = scroll_ + p.y;
        if (p.x >= 0 && p.x < p.width && p.y >= 0 && p.y < p.height && i >= 0 &&
            i < int(rows.size())) {
          auto target = rows[i];
          auto pos = p.x <= 2 + m.depth_of(target.id) * 2          ? "before"
                     : m.is_branch(target.id) && p.x < p.width - 2 ? "inside"
                                                                   : "after";
          raw = DropRequest{source_id, target.id, pos, revision_};
        }
      }
      if (raw) {
        busy_ = true;
        try {
          tuivory::request_drop(m, raw->source_id, raw->target_id,
                                raw->position, o, policy);
          error.clear();
        } catch (const DropError &e) {
          error = e.reason;
        } catch (...) {
          busy_ = false;
          throw;
        }
        busy_ = false;
        if (!valid(m, p.width, p.height))
          return std::nullopt;
      }
      request_ = raw;
      target_id = raw ? raw->target_id : "";
      position = raw ? raw->position : "";
      allowed = error.empty();
      reason = error;
      if constexpr (std::is_same_v<Model, Tree>)
        if (raw && error.empty() && o.hover_expand && raw->position == "inside")
          expanded_.insert(raw->target_id);
    }
    if (p.action != "up")
      return std::nullopt;
    auto out = phase == "dragging" && allowed ? request_
                                              : std::optional<DropRequest>{};
    auto outcome = out ? "drop" : phase == "dragging" ? "reject" : "";
    reset(outcome);
    return out;
  }
  template <class Model>
  void draw(Model &m, Canvas &canvas, Rect r, bool focused = true,
            bool ascii = false) {
    if (busy_)
      throw DropError("reentrant");
    drag_detail::bounds(r.x, 0, 1000000000, "bounds");
    drag_detail::bounds(r.y, 0, 1000000000, "bounds");
    drag_detail::bounds(r.width, 0, 65535, "bounds");
    drag_detail::bounds(r.height, 0, 4096, "bounds");
    if (!focused && captured())
      reset("cancel");
    render_key(std::to_string(r.x) + "|" + std::to_string(r.y) + "|" +
               std::to_string(r.width) + "|" + std::to_string(r.height) + "|" +
               canvas.palette.theme() + "|" + canvas.palette.colors() + "|" +
               canvas.surface_role + "|" + (focused ? "1" : "0") + "|" +
               (ascii ? "1" : "0"));
    if (!valid(m, r.width, r.height)) {
      m.draw(canvas, r, focused, ascii);
      return;
    }
    Canvas child(r.width, r.height, canvas.palette, canvas.surface_role);
    int marker_x = 0, marker_y = 0;
    std::string marker = "!";
    if constexpr (std::is_same_v<Model, Tabs>) {
      auto views = tab_cells(m, r.width, first_);
      if (first_)
        child.write(0, 0, "<", "hint", false, 1);
      if (first_ + int(views.size()) < int(m.items().size()) && r.width)
        child.write(r.width - 1, 0, ">", "hint", false, 1);
      for (auto c : views) {
        auto role = c.disabled ? "disabled" : c.active ? "selection" : "body";
        child.write(c.start, 0, std::string(c.width, ' '), role,
                    focused && c.focused, c.width);
        child.write(c.start, 0, c.text, role, focused && c.focused, c.width);
      }
      auto target = std::find_if(views.begin(), views.end(),
                                 [&](auto c) { return c.id == target_id; });
      marker_x =
          target == views.end()
              ? std::max(0, std::min(r.width - 1, pointer_.x))
              : target->start + (position == "after" ? target->width - 1 : 0);
      marker = ascii ? "|" : "│";
    } else {
      auto rows = tree_rows(m, r.height);
      for (int y = 0; y < r.height && scroll_ + y < int(rows.size()); y++) {
        auto n = rows[scroll_ + y];
        bool selected = m.selected == n.id;
        auto arrow = m.is_branch(n.id) ? expanded_.count(n.id)
                                             ? ascii ? "v" : "▾"
                                         : ascii ? ">"
                                                 : "▸"
                                       : " ";
        auto icon = ascii ? n.ascii_icon : n.icon;
        auto text = std::string(m.depth_of(n.id) * 2, ' ') + arrow + " " +
                    (icon.empty() ? "" : icon + " ") + n.name +
                    (n.secondary.empty() ? "" : "  " + n.secondary) +
                    (n.count ? " (" + std::to_string(*n.count) + ")" : "");
        auto gs = graphemes(text);
        std::size_t start = 0;
        int skipped = 0;
        while (start < gs.size() && skipped < m.horizontal)
          skipped += cells(gs[start++].text);
        text.clear();
        for (auto i = start; i < gs.size(); i++)
          text += gs[i].text;
        child.write(0, y,
                    std::string(selected ? "> " : "  ") +
                        clip(text, std::max(0, r.width - 2), true),
                    selected ? "selection" : "body", focused && selected,
                    r.width);
      }
      auto at = std::find_if(rows.begin(), rows.end(),
                             [&](auto n) { return n.id == target_id; });
      marker_y = at == rows.end()
                     ? std::max(0, std::min(r.height - 1, pointer_.y))
                     : int(at - rows.begin()) - scroll_;
      marker = position == "before"   ? ascii ? "^" : "↑"
               : position == "after"  ? ascii ? "v" : "↓"
               : position == "inside" ? ascii ? "+" : "↳"
                                      : "!";
    }
    if (phase == "dragging" && marker_x >= 0 && marker_x < r.width &&
        marker_y >= 0 && marker_y < r.height) {
      auto old = child.data[marker_y][marker_x].style,
           semantic = child.palette.style(allowed ? "info" : "error");
      auto foreground = semantic.foreground;
      if (color_contrast(foreground, old.background) < 4.5 &&
          color_contrast(old.foreground, old.background) >
              color_contrast(foreground, old.background))
        foreground = old.foreground;
      child.write_style(
          marker_x, marker_y, allowed ? marker : "!",
          Style{foreground, old.background, true, false, true, false}, 1);
    }
    canvas.blit(child, {0, 0, r.width, r.height}, r.x, r.y);
  }
};
} // namespace tuivory
