#pragma once
namespace tuivory {
struct MenuItem {
  std::string id, parent, label, secondary, shortcut, mnemonic, icon,
      ascii_icon;
  bool disabled = false, separator = false;
};
struct MenuEvent {
  std::string kind, id, return_id;
};
struct MenuSpan {
  int start = 0, width = 0;
  std::string text, role;
};
struct MenuRow {
  std::string id, text, role;
  std::vector<MenuSpan> spans;
  bool focused = false;
};
struct MenuBarCell {
  std::string id, text, role;
  int start = 0, width = 0;
  bool focused = false;
};
struct MenuBarLayout {
  std::vector<MenuBarCell> cells;
  bool previous = false, next = false;
};
class Menu {
  struct Data {
    std::map<std::string, std::size_t> index;
    std::map<std::string, std::vector<std::string>> children;
  };
  std::vector<MenuItem> items_;
  Data data_;
  std::vector<std::string> path_;
  std::map<std::string, std::string> focus_;
  std::map<std::string, int> tops_;
  bool opened_ = false, context_ = false;
  std::string caller_, bar_;
  int bar_first_ = 0, width_ = 0;
  std::vector<MenuRow> hits_;
  static std::string lower(std::string s) {
    for (auto &c : s)
      if (c >= 'A' && c <= 'Z')
        c = static_cast<char>(c + ('a' - 'A'));
    return s;
  }
  static bool mnemonic(const std::string &s) {
    return s.size() == 1 &&
           ((s[0] >= 'A' && s[0] <= 'Z') || (s[0] >= 'a' && s[0] <= 'z') ||
            (s[0] >= '0' && s[0] <= '9'));
  }
  static Data validate(const std::vector<MenuItem> &items) {
    if (items.size() > 10000)
      throw std::invalid_argument("too many menu items");
    Data d;
    std::set<std::pair<std::string, std::string>> keys;
    for (std::size_t n = 0; n < items.size(); n++) {
      const auto &i = items[n];
      if (i.id.empty() || i.id[0] == '@' || !d.index.emplace(i.id, n).second)
        throw std::invalid_argument("invalid menu ID");
      for (const auto *s : {&i.id, &i.parent, &i.label, &i.secondary,
                            &i.shortcut, &i.icon, &i.ascii_icon})
        cells(*s);
      if (!i.mnemonic.empty() &&
          (!mnemonic(i.mnemonic) || i.separator ||
           !keys.insert({i.parent, lower(i.mnemonic)}).second))
        throw std::invalid_argument("invalid sibling mnemonic");
      d.children[i.parent].push_back(i.id);
    }
    for (const auto &i : items) {
      if (i.separator && d.children.count(i.id))
        throw std::invalid_argument("separator children");
      std::set<std::string> seen{i.id};
      auto parent = i.parent;
      int depth = 1;
      while (!parent.empty()) {
        auto it = d.index.find(parent);
        if (it == d.index.end() || !seen.insert(parent).second ||
            items[it->second].separator)
          throw std::invalid_argument("invalid parent/cycle");
        if (++depth > 32)
          throw std::invalid_argument("menu depth exceeds32");
        parent = items[it->second].parent;
      }
    }
    return d;
  }
  std::vector<std::string> children(const std::string &p) const {
    auto it = data_.children.find(p);
    return it == data_.children.end() ? std::vector<std::string>{} : it->second;
  }
  bool usable(const std::string &id, const std::string &p) const {
    auto it = data_.index.find(id);
    if (it == data_.index.end())
      return false;
    const auto &i = items_[it->second];
    return i.parent == p && !i.disabled && !i.separator;
  }
  std::string first(const std::string &p) const {
    for (const auto &id : children(p))
      if (usable(id, p))
        return id;
    return "";
  }
  std::string parent() const { return path_.empty() ? "" : path_.back(); }
  bool back_allowed() const {
    return path_.size() > 1 || (context_ && !path_.empty());
  }
  void reconcile() {
    auto p = parent(), id = focused_id();
    if (id == "@back" && back_allowed())
      return;
    if (!usable(id, p)) {
      auto candidate = first(p);
      focus_[p] = candidate.empty() && back_allowed() ? "@back" : candidate;
    }
  }
  MenuEvent event(std::string kind, std::string id = "") const {
    return {std::move(kind), std::move(id), caller_};
  }
  MenuEvent finish(std::string kind, std::string id = "") {
    opened_ = false;
    path_.clear();
    hits_.clear();
    return event(std::move(kind), std::move(id));
  }
  MenuEvent enter(std::string id) {
    path_.push_back(id);
    reconcile();
    return event("open", id);
  }
  MenuEvent switch_root(bool next) {
    auto ids = children("");
    ids.erase(
        std::remove_if(ids.begin(), ids.end(),
                       [&](const std::string &id) { return !usable(id, ""); }),
        ids.end());
    if (ids.empty())
      return {};
    auto found = std::find(ids.begin(), ids.end(), bar_);
    std::size_t at = found == ids.end() ? 0 : found - ids.begin(),
                step = next ? 1 : ids.size() - 1;
    for (std::size_t n = 0; n < ids.size(); n++) {
      at = (at + step) % ids.size();
      if (ids[at] != bar_ && !children(ids[at]).empty())
        return open(ids[at], caller_);
    }
    return {};
  }
  static std::string label(const MenuItem &i) {
    auto key = i.mnemonic;
    for (auto &c : key)
      if (c >= 'a' && c <= 'z')
        c = static_cast<char>(c - ('a' - 'A'));
    return i.label + (key.empty() ? "" : " (" + key + ")");
  }
  std::vector<MenuItem> rows() const {
    std::vector<MenuItem> out;
    if (back_allowed()) {
      MenuItem b;
      b.id = "@back";
      b.label = back_label;
      out.push_back(b);
      MenuItem separator;
      separator.separator = true;
      out.push_back(separator);
    }
    for (const auto &id : children(parent()))
      out.push_back(items_[data_.index.at(id)]);
    return out;
  }

public:
  std::string back_label = "Back", empty_label = "(empty)";
  explicit Menu(std::vector<MenuItem> items) { set_items(std::move(items)); }
  const std::vector<MenuItem> &items() const { return items_; }
  bool opened() const { return opened_; }
  const std::vector<std::string> &path() const { return path_; }
  std::string focused_id() const {
    auto it = focus_.find(parent());
    return it == focus_.end() ? "" : it->second;
  }
  std::string return_id() const { return caller_; }
  std::string bar_focused_id() const { return bar_; }
  std::string title() const {
    std::string out;
    for (const auto &id : path_) {
      if (!out.empty())
        out += " / ";
      out += clean(items_[data_.index.at(id)].label);
    }
    return out;
  }
  MenuEvent set_items(std::vector<MenuItem> items) {
    auto data = validate(items);
    items_ = std::move(items);
    data_ = std::move(data);
    for (auto it = focus_.begin(); it != focus_.end();)
      if (!it->first.empty() && !data_.index.count(it->first))
        it = focus_.erase(it);
      else
        ++it;
    for (auto it = tops_.begin(); it != tops_.end();)
      if (!it->first.empty() && !data_.index.count(it->first))
        it = tops_.erase(it);
      else
        ++it;
    hits_.clear();
    if (!usable(bar_, ""))
      bar_ = first("");
    for (std::size_t n = 0; n < path_.size(); n++)
      if (!usable(path_[n], n ? path_[n - 1] : "") ||
          children(path_[n]).empty())
        return close();
    if (opened_)
      reconcile();
    return {};
  }
  MenuEvent open(std::string id = "", std::string caller = "") {
    std::vector<std::string> path;
    auto at = id;
    while (!at.empty()) {
      auto it = data_.index.find(at);
      if (it == data_.index.end())
        return {};
      const auto &i = items_[it->second];
      if (i.disabled || i.separator)
        return {};
      path.insert(path.begin(), at);
      at = i.parent;
    }
    caller_ = std::move(caller);
    path_ = std::move(path);
    hits_.clear();
    for (std::size_t n = 0; n < path_.size(); n++)
      focus_[n ? path_[n - 1] : ""] = path_[n];
    context_ = id.empty();
    opened_ = true;
    if (!path_.empty())
      bar_ = path_.front();
    if (!id.empty() && children(id).empty())
      return finish("activate", id);
    reconcile();
    return event("open", id);
  }
  MenuEvent close() { return opened_ ? finish("close") : MenuEvent{}; }
  MenuEvent back() {
    if (!opened_)
      return {};
    if (!back_allowed())
      return close();
    path_.pop_back();
    reconcile();
    return event("back", parent());
  }
  bool focus(const std::string &id) {
    if (!opened_)
      return false;
    if ((id == "@back" && back_allowed()) || usable(id, parent())) {
      focus_[parent()] = id;
      return true;
    }
    return false;
  }
  MenuEvent handle(std::string action, const std::string &value = "",
                   int height = 10) {
    if (!opened_)
      return {};
    reconcile();
    auto p = parent(), id = focused_id();
    if (action == "cancel" || action == "back")
      return back();
    if (action == "close")
      return close();
    if (action == "left")
      return back_allowed() ? back()
             : context_     ? MenuEvent{}
                            : switch_root(false);
    if (action == "right") {
      if (usable(id, p) && !children(id).empty())
        return enter(id);
      return !back_allowed() && !context_ ? switch_root(true) : MenuEvent{};
    }
    if (action == "activate") {
      if (id == "@back")
        return back();
      if (!usable(id, p))
        return {};
      return children(id).empty() ? finish("activate", id) : enter(id);
    }
    if (action == "mnemonic") {
      if (!mnemonic(value))
        return {};
      for (const auto &candidate : children(p)) {
        const auto &i = items_[data_.index.at(candidate)];
        if (usable(candidate, p) && !i.mnemonic.empty() &&
            lower(i.mnemonic) == lower(value)) {
          focus_[p] = candidate;
          return handle("activate", "", height);
        }
      }
      return {};
    }
    std::vector<std::string> ids;
    if (back_allowed())
      ids.push_back("@back");
    for (const auto &candidate : children(p))
      if (usable(candidate, p))
        ids.push_back(candidate);
    if (ids.empty())
      return {};
    auto found = std::find(ids.begin(), ids.end(), id);
    std::size_t at = found == ids.end() ? 0 : found - ids.begin(),
                step = static_cast<std::size_t>(height > 1 ? height - 1 : 1);
    if (action == "previous" || action == "up")
      at = (at + ids.size() - 1) % ids.size();
    else if (action == "next" || action == "down")
      at = (at + 1) % ids.size();
    else if (action == "first" || action == "home")
      at = 0;
    else if (action == "last" || action == "end")
      at = ids.size() - 1;
    else if (action == "page_up")
      at = at > step ? at - step : 0;
    else if (action == "page_down")
      at = std::min(ids.size() - 1, at + step);
    else
      return {};
    focus_[p] = ids[at];
    return event("focus", ids[at]);
  }
  MenuEvent handle_bar(std::string action, const std::string &value = "") {
    auto ids = children("");
    ids.erase(
        std::remove_if(ids.begin(), ids.end(),
                       [&](const std::string &id) { return !usable(id, ""); }),
        ids.end());
    if (ids.empty())
      return {};
    auto found = std::find(ids.begin(), ids.end(), bar_);
    std::size_t at = found == ids.end() ? 0 : found - ids.begin();
    if (action == "previous" || action == "left")
      at = (at + ids.size() - 1) % ids.size();
    else if (action == "next" || action == "right")
      at = (at + 1) % ids.size();
    else if (action == "first" || action == "home")
      at = 0;
    else if (action == "last" || action == "end")
      at = ids.size() - 1;
    else if (action == "activate" || action == "down")
      return {"open_request", ids[at], ""};
    else if (action == "mnemonic") {
      if (!mnemonic(value))
        return {};
      for (const auto &id : ids) {
        const auto &i = items_[data_.index.at(id)];
        if (!i.mnemonic.empty() && lower(i.mnemonic) == lower(value)) {
          bar_ = id;
          return {"open_request", id, ""};
        }
      }
      return {};
    } else
      return {};
    bar_ = ids[at];
    return {"focus", bar_, ""};
  }
  MenuEvent click_id(const std::string &id) {
    return focus(id) ? handle("activate") : MenuEvent{};
  }
  MenuEvent click(int x, int y, int height = 10) {
    if (!opened_ || x < 0 || x >= width_ || y < 0 || y >= height ||
        static_cast<std::size_t>(y) >= hits_.size())
      return {};
    return click_id(hits_[y].id);
  }
  std::pair<int, int> content_size() const {
    auto data = rows();
    int width = 12;
    for (const auto &i : data)
      width = std::max(width, cells(label(i)) + cells(i.secondary) +
                                  cells(i.shortcut) + cells(i.icon) + 8);
    return {std::min(width, 4096), std::max(1, static_cast<int>(data.size()))};
  }
  std::vector<MenuRow> layout(int width, int height, bool ascii = false) {
    hits_.clear();
    width_ = width = std::max(0, std::min(65535, width));
    height = std::max(0, std::min(4096, height));
    if (!opened_ || !width || !height)
      return {};
    reconcile();
    auto data = rows();
    if (data.empty()) {
      hits_.push_back({"", clip(empty_label, width, true), "hint", {}, false});
      return hits_;
    }
    int at = 0;
    for (std::size_t n = 0; n < data.size(); n++)
      if (data[n].id == focused_id())
        at = static_cast<int>(n);
    auto p = parent();
    int top = std::min(tops_[p], at);
    if (at >= top + height)
      top = at - height + 1;
    top = std::min(top, std::max(0, static_cast<int>(data.size()) - height));
    tops_[p] = top;
    for (int n = top; n < std::min(top + height, static_cast<int>(data.size()));
         n++) {
      const auto &i = data[n];
      if (i.separator) {
        std::string line;
        for (int x = 0; x < width; x++)
          line += ascii ? "-" : "─";
        hits_.push_back({"", line, "hint", {}, false});
        continue;
      }
      bool current = i.id == focused_id();
      auto role = i.disabled ? "disabled" : current ? "selection" : "surface";
      auto icon =
          ascii ? (i.ascii_icon.empty() && !i.icon.empty() ? "*" : i.ascii_icon)
                : i.icon;
      auto text = std::string(current ? "> " : "  ") +
                  (icon.empty() ? "" : icon + " ") +
                  (i.id == "@back" ? "< " + i.label : label(i)) +
                  (i.secondary.empty() ? "" : "  " + i.secondary);
      auto suffix = children(i.id).empty() ? "" : ascii ? " >" : " ›";
      auto shortcut = clean(i.shortcut);
      int reserve = std::min(width / 3, cells(shortcut));
      std::string tail =
          reserve ? " " + clip(shortcut, reserve) + suffix : suffix;
      int tw = std::min(width, cells(tail));
      auto left = clip(text, width - tw, true);
      std::vector<MenuSpan> spans = {{0, width, left, role}};
      if (tw)
        spans.push_back({width - tw, tw, clip(tail, tw),
                         std::string(role) == "surface" ? "hint" : role});
      auto combined = left +
                      std::string(std::max(0, width - tw - cells(left)), ' ') +
                      clip(tail, tw);
      hits_.push_back({i.id, combined, role, std::move(spans), current});
    }
    return hits_;
  }
  void draw(Canvas &c, Rect r, bool ascii = false) {
    if (!opened_)
      return;
    c.fill(r, "surface");
    auto out = layout(r.width, r.height, ascii);
    for (std::size_t y = 0; y < out.size(); y++) {
      const auto &row = out[y];
      c.fill({r.x, r.y + static_cast<int>(y), r.width, 1}, row.role);
      if (row.spans.empty())
        c.write(r.x, r.y + static_cast<int>(y), row.text, row.role, false,
                r.width, false);
      for (const auto &s : row.spans)
        c.write(r.x + s.start, r.y + static_cast<int>(y), s.text, s.role, false,
                s.width, false);
    }
  }
  // The host owns placement/visibility; returned coordinates are used for hits.
  Rect draw_popup(Canvas &c, Rect r, const std::string &title = "",
                  int padding = 1, bool ascii = false) {
    if (!opened_)
      return {r.x, r.y, 0, 0};
    auto inner = c.panel(r, title, false, ascii);
    padding = std::max(0, std::min(4096, padding));
    int px = std::min(padding, inner.width / 2),
        py = std::min(padding, inner.height / 2);
    Rect content{inner.x + px, inner.y + py, std::max(0, inner.width - 2 * px),
                 std::max(0, inner.height - 2 * py)};
    draw(c, content, ascii);
    return content;
  }
  MenuBarLayout bar_layout(int width) {
    MenuBarLayout out;
    width = std::max(0, std::min(65535, width));
    if (width < 3)
      return out;
    auto ids = children("");
    ids.erase(std::remove_if(ids.begin(), ids.end(),
                             [&](const std::string &id) {
                               return items_[data_.index.at(id)].separator;
                             }),
              ids.end());
    if (ids.empty())
      return out;
    auto found = std::find(ids.begin(), ids.end(), bar_);
    int target = found == ids.end() ? 0 : static_cast<int>(found - ids.begin());
    bar_first_ = std::min(bar_first_, target);
    auto size = [&](int n) {
      return std::min(24, cells(label(items_[data_.index.at(ids[n])])) + 2);
    };
    auto sum = [&](int a, int b) {
      int total = 0;
      for (int n = a; n <= b; n++)
        total += size(n);
      return total;
    };
    while (bar_first_ < target && sum(bar_first_, target) > width - 2)
      bar_first_++;
    while (bar_first_ > 0 && sum(bar_first_ - 1, target) <= width - 2)
      bar_first_--;
    int x = 1, last = bar_first_;
    for (int n = bar_first_; n < static_cast<int>(ids.size()); n++) {
      if (x >= width - 1)
        break;
      const auto &i = items_[data_.index.at(ids[n])];
      int w = std::min(size(n), width - 1 - x);
      bool current = i.id == bar_;
      auto role = i.disabled ? "disabled" : current ? "selection" : "header";
      out.cells.push_back(
          {i.id, clip(" " + label(i) + " ", w, true), role, x, w, current});
      x += w;
      last = n + 1;
    }
    out.previous = bar_first_ > 0;
    out.next = last < static_cast<int>(ids.size());
    return out;
  }
  MenuEvent bar_click(int x, int width) {
    if (x < 0 || x >= width)
      return {};
    auto l = bar_layout(width);
    if (x == 0 && l.previous)
      return handle_bar("previous");
    if (x + 1 == width && l.next)
      return handle_bar("next");
    for (const auto &c : l.cells)
      if (x >= c.start && x < c.start + c.width && usable(c.id, "")) {
        bar_ = c.id;
        return {"open_request", c.id, ""};
      }
    return {};
  }
  void draw_bar(Canvas &c, Rect r) {
    if (r.height <= 0)
      return;
    c.fill({r.x, r.y, r.width, 1}, "surface");
    auto l = bar_layout(r.width);
    for (const auto &cell : l.cells) {
      c.fill({r.x + cell.start, r.y, cell.width, 1}, cell.role);
      c.write(r.x + cell.start, r.y, cell.text, cell.role, false, cell.width,
              false);
    }
    if (l.previous)
      c.write(r.x, r.y, "<", "hint", false, 1);
    if (l.next)
      c.write(r.x + r.width - 1, r.y, ">", "hint", false, 1);
  }
};
inline Rect menu_placement(Rect anchor, Rect viewport, int width, int height) {
  long long vw = std::max(0, viewport.width), vh = std::max(0, viewport.height),
            w = std::min<long long>(std::max(0, width), vw),
            h = std::min<long long>(std::max(0, height), vh),
            x = std::max<long long>(
                viewport.x,
                std::min<long long>(static_cast<long long>(viewport.x) + vw - w,
                                    anchor.x)),
            y = static_cast<long long>(anchor.y) + std::max(0, anchor.height);
  if (y + h > static_cast<long long>(viewport.y) + vh)
    y = static_cast<long long>(anchor.y) - h;
  y = std::max<long long>(
      viewport.y,
      std::min<long long>(static_cast<long long>(viewport.y) + vh - h, y));
  return {static_cast<int>(x), static_cast<int>(y), static_cast<int>(w),
          static_cast<int>(h)};
}
} // namespace tuivory
