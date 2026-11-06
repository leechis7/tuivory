#pragma once
namespace tuivory {
struct Item {
  std::string id, label, secondary, shortcut, icon, ascii_icon, parent;
  bool disabled = false, separator = false;
};
struct CollectionRow {
  std::string id, text, role = "body";
  bool focused = false;
};
class List {
  std::vector<Item> items_;
  std::vector<CollectionRow> hits_;
  int layout_width_ = 0;
  static void validate(const std::vector<Item> &items) {
    std::set<std::string> ids;
    for (const auto &i : items) {
      if (i.id.empty() || !ids.insert(i.id).second)
        throw std::invalid_argument("invalid list ID");
      for (const auto *s :
           {&i.id, &i.label, &i.secondary, &i.shortcut, &i.icon, &i.ascii_icon})
        cells(*s);
    }
  }
  std::vector<std::string> eligible() {
    std::vector<std::string> out;
    for (const auto &i : visible())
      if (!i.disabled && !i.separator)
        out.push_back(i.id);
    if (std::find(out.begin(), out.end(), focused) == out.end())
      focused = out.empty() ? "" : out.front();
    return out;
  }

public:
  std::string focused, selected, query, empty = "(empty)";
  int scroll = 0;
  explicit List(std::vector<Item> items = {}) { set_items(std::move(items)); }
  const std::vector<Item> &items() const { return items_; }
  void set_items(std::vector<Item> items) {
    validate(items);
    if (std::none_of(items.begin(), items.end(),
                     [&](const Item &i) { return i.id == selected; }))
      selected.clear();
    items_ = std::move(items);
    eligible();
  }
  std::vector<Item> visible() const {
    auto q = fold(query);
    std::vector<Item> out;
    for (const auto &i : items_)
      if (q.empty() ||
          (!i.separator &&
           fold(i.label + " " + i.secondary).find(q) != std::string::npos))
        out.push_back(i);
    return out;
  }
  bool focus(const std::string &id) {
    for (const auto &i : visible())
      if (i.id == id && !i.disabled && !i.separator) {
        focused = id;
        return true;
      }
    return false;
  }
  Event set_query(const std::string &text) {
    std::string next;
    for (std::size_t p = 0; p < text.size();) {
      auto start = p;
      auto cp = detail::decode(text, p);
      if (cp >= 32 && !(cp >= 127 && cp < 160))
        next += text.substr(start, p - start);
    }
    query = std::move(next);
    eligible();
    return {"query", "", query};
  }
  Event handle(std::string action, int height = 10,
               const std::string &text = "") {
    if (action == "query")
      return set_query(text);
    auto ids = eligible();
    if (ids.empty())
      return {};
    std::size_t at = std::find(ids.begin(), ids.end(), focused) - ids.begin();
    if (action == "activate" || action == "select") {
      selected = focused;
      return {action, focused, ""};
    }
    if (action == "up")
      action = "previous";
    if (action == "down")
      action = "next";
    if (action == "home")
      action = "first";
    if (action == "end")
      action = "last";
    if (action == "previous")
      at = at ? at - 1 : 0;
    else if (action == "next")
      at = std::min(ids.size() - 1, at + 1);
    else if (action == "first")
      at = 0;
    else if (action == "last")
      at = ids.size() - 1;
    else if (action == "page_up") {
      auto n = static_cast<std::size_t>((height > 1 ? height - 1 : 1));
      at = at > n ? at - n : 0;
    } else if (action == "page_down")
      at = std::min(ids.size() - 1, at + static_cast<std::size_t>(
                                             (height > 1 ? height - 1 : 1)));
    else
      return {};
    focused = ids[at];
    return {"focus", focused, ""};
  }
  std::vector<CollectionRow> layout(int width, int height, bool ascii = false) {
    std::vector<CollectionRow> rows;
    std::size_t anchor = 0;
    for (const auto &i : visible()) {
      bool current = i.id == focused;
      if (current)
        anchor = rows.size();
      auto role = i.disabled         ? "disabled"
                  : i.id == selected ? "selection"
                                     : "body";
      if (i.separator) {
        rows.push_back({i.id, "--- " + i.label + " ---", "hint", false});
        continue;
      }
      auto icon = ascii ? i.ascii_icon : i.icon;
      rows.push_back({i.id,
                      (current ? "> " : "  ") +
                          std::string(i.id == selected ? "* " : "") +
                          (icon.empty() ? "" : icon + " ") + i.label +
                          (i.shortcut.empty() ? "" : " [" + i.shortcut + "]"),
                      role, current});
      if (!i.secondary.empty())
        rows.push_back({i.id, "    " + i.secondary,
                        i.disabled ? "disabled" : "hint", false});
    }
    if (rows.empty())
      rows.push_back({"", empty, "hint", false});
    width = std::max(0, width);
    height = std::max(0, height);
    scroll = std::min(
        std::max(0, static_cast<int>(anchor) - std::max(0, height - 2)),
        std::max(0, static_cast<int>(rows.size()) - height));
    layout_width_ = width;
    auto end = std::min(rows.size(), static_cast<std::size_t>(scroll + height));
    hits_ = {rows.begin() + scroll, rows.begin() + end};
    for (auto &r : hits_)
      r.text = clip(r.text, width, true);
    return hits_;
  }
  Event click_id(const std::string &id) {
    return focus(id) ? handle("activate") : Event{};
  }
  Event click(int x, int y, int height = 10) {
    if (x < 0 || x >= layout_width_ || y < 0 || y >= height ||
        static_cast<std::size_t>(y) >= hits_.size())
      return {};
    return click_id(hits_[y].id);
  }
  void draw(Canvas &c, Rect r, bool focus_view = true, bool ascii = false) {
    c.fill(r);
    auto rows = layout(r.width, r.height, ascii);
    for (std::size_t y = 0; y < rows.size(); y++) {
      c.fill({r.x, r.y + static_cast<int>(y), r.width, 1}, rows[y].role);
      c.write(r.x, r.y + static_cast<int>(y), rows[y].text, rows[y].role,
              focus_view && rows[y].focused, r.width, false);
    }
  }
};
class SearchPicker {
  int width_ = 0, height_ = 0;

public:
  List list;
  bool open = false;
  std::string value;
  explicit SearchPicker(std::vector<Item> items) : list(std::move(items)) {}
  Event handle(const std::string &action, const std::string &text = "",
               int height = 10) {
    if (action == "open") {
      open = true;
      list.set_query("");
      list.focus(value);
      return {"open", "", ""};
    }
    if (action == "cancel") {
      open = false;
      return {"cancel", "", ""};
    }
    if (action == "insert" || action == "backspace") {
      if (!open)
        handle("open");
      auto query = list.query;
      if (action == "insert")
        query += text;
      else {
        auto g = graphemes(query);
        if (!g.empty())
          query.erase(query.size() - g.back().text.size());
      }
      return list.set_query(query);
    }
    if (action == "activate") {
      if (!open)
        return handle("open");
      auto e = list.handle("activate", height);
      if (!e.id.empty()) {
        value = e.id;
        open = false;
        e.kind = "change";
      }
      return e;
    }
    return open ? list.handle(action, height) : Event{};
  }
  Event click_id(const std::string &id) {
    return list.focus(id) ? handle("activate") : Event{};
  }
  Event click(int x, int y, int height = 10) {
    if (x < 0 || x >= width_ || y < 0 || y >= std::min(height, height_))
      return {};
    if (!open)
      return handle("open");
    if (!y)
      return {};
    auto e = list.click(x, y - 1, std::max(0, height - 1));
    if (!e.id.empty()) {
      value = e.id;
      open = false;
      return {"change", e.id, ""};
    }
    return {};
  }
  std::vector<CollectionRow> layout(int width, int height, bool ascii = false) {
    width_ = std::max(0, width);
    height_ = std::max(0, height);
    width = width_;
    height = height_;
    if (height <= 0)
      return {};
    if (!open) {
      auto label = list.empty;
      for (const auto &i : list.items())
        if (i.id == value)
          label = i.label;
      return {{value, clip("v " + label, width), "field", false}};
    }
    std::string shown;
    int used = 0;
    auto gs = graphemes(list.query);
    for (auto it = gs.rbegin(); it != gs.rend(); ++it) {
      int n = cells(it->text);
      if (used + n > std::max(0, width - 3))
        break;
      shown = it->text + shown;
      used += n;
    }
    std::vector<CollectionRow> rows = {
        {"", clip("? " + shown, width), "field", false}};
    auto body = list.layout(width, std::max(0, height - 1), ascii);
    rows.insert(rows.end(), body.begin(), body.end());
    return rows;
  }
  void draw(Canvas &c, Rect r, bool focused = true, bool ascii = false) {
    c.fill(r);
    auto rows = layout(r.width, r.height, ascii);
    if (!open) {
      if (!rows.empty()) {
        c.fill({r.x, r.y, r.width, 1}, "field");
        c.write(r.x, r.y, rows[0].text, "field", false, r.width, false);
      }
      return;
    }
    if (r.height > 0) {
      c.fill({r.x, r.y, r.width, 1}, "field");
      c.write(r.x, r.y, "? ", "field", false, r.width, false);
      if (r.width > 2) {
        Text query(list.query);
        query.multiline = false;
        query.draw(c, {r.x + 2, r.y, r.width - 2, 1}, focused);
      }
    }
    if (r.height > 1)
      list.draw(c, {r.x, r.y + 1, r.width, r.height - 1}, focused, ascii);
  }
};
} // namespace tuivory
