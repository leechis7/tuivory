#pragma once
// Literal UTF-8 editing. Host owns clipboard transport and terminal cursor
// policy.
namespace tuivory {
class Text {
  struct Snapshot {
    std::string value;
    std::size_t cursor, anchor;
  };
  std::vector<Snapshot> undo_, redo_;
  static bool br(const std::string &g) {
    return g == "\r" || g == "\n" || g == "\r\n";
  }
  static std::size_t byte(const std::vector<Grapheme> &g, std::size_t at) {
    std::size_t n = 0;
    for (std::size_t i = 0; i < std::min(at, g.size()); i++)
      n += g[i].text.size();
    return n;
  }
  std::size_t index(std::size_t offset) const {
    auto g = graphemes(value);
    std::size_t n = 0;
    for (std::size_t i = 0; i < g.size(); i++) {
      if (n == offset)
        return i;
      n += g[i].text.size();
    }
    if (n == offset)
      return g.size();
    throw std::invalid_argument("offset splits a grapheme or is outside text");
  }
  Event replace(std::size_t a, std::size_t b, const std::string &addition) {
    if (!state.editable() || (a == b && addition.empty()))
      return {};
    auto g = graphemes(value);
    auto prefix = value.substr(0, byte(g, a)) + addition;
    auto next = prefix + value.substr(byte(g, b));
    auto parsed = graphemes(next);
    std::size_t offset = 0, at = 0;
    for (const auto &p : parsed) {
      if (offset >= prefix.size())
        break;
      offset += p.text.size();
      at++;
    }
    undo_.push_back({value, cursor, anchor});
    if (undo_.size() > 128)
      undo_.erase(undo_.begin());
    redo_.clear();
    value = std::move(next);
    select(at, at);
    state.edited = true;
    return {"change", "", ""};
  }
  std::string sanitize(const std::string &s) const {
    std::string out;
    for (std::size_t p = 0; p < s.size();) {
      auto start = p;
      auto cp = detail::decode(s, p);
      if (cp == '\r') {
        if (p < s.size() && s[p] == '\n')
          p++;
        if (multiline)
          out += '\n';
      } else if (cp == '\n') {
        if (multiline)
          out += '\n';
      } else if (cp == '\t')
        out += ' ';
      else if (cp >= 32 && !(cp >= 127 && cp < 160))
        out += s.substr(start, p - start);
    }
    return out;
  }
  struct Glyph {
    std::size_t index;
    std::string text;
  };
  using Rows = std::vector<std::vector<Glyph>>;
  Rows rows() const {
    Rows out(1);
    auto g = graphemes(value);
    for (std::size_t i = 0; i < g.size(); i++) {
      if (multiline && br(g[i].text))
        out.emplace_back();
      else
        out.back().push_back({i, secret ? "*" : g[i].text});
    }
    return out;
  }

public:
  std::string value;
  std::size_t cursor = 0, anchor = 0;
  State state;
  bool secret = false, multiline = true;
  int scroll_x = 0, scroll_y = 0;
  explicit Text(std::string text = "") : value(std::move(text)) {
    cursor = anchor = graphemes(value).size();
  }
  std::string display() const {
    return secret ? std::string(graphemes(value).size(), '*') : value;
  }
  void select(std::size_t a, std::size_t c) {
    auto n = graphemes(value).size();
    anchor = std::min(a, n);
    cursor = std::min(c, n);
  }
  std::pair<std::size_t, std::size_t> selection_bytes() const {
    auto g = graphemes(value);
    return {byte(g, std::min(anchor, cursor)),
            byte(g, std::max(anchor, cursor))};
  }
  void select_bytes(std::size_t a, std::size_t c) {
    auto ai = index(a), ci = index(c);
    select(ai, ci);
  }
  Event replace_bytes(std::size_t a, std::size_t b, const std::string &s) {
    if (a > b)
      throw std::invalid_argument("reversed byte range");
    auto ai = index(a), bi = index(b);
    return replace(ai, bi, s);
  }
  Event handle(const std::string &action, const std::string &text = "") {
    if (state.disabled)
      return {};
    select(anchor, cursor);
    auto g = graphemes(value);
    auto lo = std::min(anchor, cursor), hi = std::max(anchor, cursor),
         at = cursor, start = at, end = at;
    while (start && !br(g[start - 1].text))
      start--;
    while (end < g.size() && !br(g[end].text))
      end++;
    bool extend = action.rfind("select_", 0) == 0;
    auto move = extend ? action.substr(7) : action;
    std::optional<std::size_t> target;
    if (extend && move == "all") {
      select(0, g.size());
      return {"select", "", ""};
    }
    if (move == "left")
      target = !extend && lo != hi ? lo : at ? at - 1 : 0;
    if (move == "right")
      target = !extend && lo != hi ? hi : std::min(g.size(), at + 1);
    if (move == "home")
      target = start;
    if (move == "end")
      target = end;
    if (move == "up") {
      auto p = start ? start - 1 : 0;
      while (p && !br(g[p - 1].text))
        p--;
      target = start ? std::min(p + at - start, start - 1) : at;
    }
    if (move == "down") {
      auto e = std::min(g.size(), end + 1);
      while (e < g.size() && !br(g[e].text))
        e++;
      target = end < g.size() ? std::min(end + 1 + at - start, e) : at;
    }
    if (target) {
      select(extend ? anchor : *target, *target);
      return {"select", "", ""};
    }
    if (action == "copy" || action == "cut") {
      if (secret || lo == hi || (action == "cut" && !state.editable()))
        return {};
      auto copied = value.substr(byte(g, lo), byte(g, hi) - byte(g, lo));
      if (action == "cut")
        replace(lo, hi, "");
      return {action, "", copied};
    }
    if (!state.editable())
      return {};
    if (action == "undo" || action == "redo") {
      auto &src = action == "undo" ? undo_ : redo_;
      auto &dst = action == "undo" ? redo_ : undo_;
      if (src.empty())
        return {};
      dst.push_back({value, cursor, anchor});
      auto previous = src.back();
      src.pop_back();
      value = previous.value;
      cursor = previous.cursor;
      anchor = previous.anchor;
      state.edited = true;
      return {"change", "", ""};
    }
    std::string add;
    if (action == "backspace") {
      if (lo == hi && lo)
        lo--;
    } else if (action == "delete") {
      if (lo == hi && hi < g.size())
        hi++;
    } else if (action == "insert" || action == "paste" || action == "newline")
      add = sanitize(action == "newline" ? "\n" : text);
    else
      return {};
    return replace(lo, hi, add);
  }
  void draw(Canvas &c, Rect r, bool focused = true) {
    auto role = state.disabled    ? "disabled"
                : state.read_only ? "body"
                                  : "field";
    c.fill(r, role);
    if (r.width <= 0 || r.height <= 0)
      return;
    auto rs = rows();
    auto raw = graphemes(value);
    int cy = 0, cx = 0, cw = 1;
    for (std::size_t i = 0; i < std::min(cursor, raw.size()); i++)
      if (multiline && br(raw[i].text))
        cy++;
    cy = std::min(cy, static_cast<int>(rs.size()) - 1);
    for (const auto &g : rs[cy]) {
      if (g.index < cursor)
        cx += cells(g.text);
      if (g.index == cursor)
        cw = std::max(1, cells(g.text));
    }
    scroll_y = std::max({0, std::min(scroll_y, cy), cy - r.height + 1});
    scroll_x = std::max(
        {0, std::min(scroll_x, cx), cx + std::min(cw, r.width) - r.width});
    auto lo = std::min(anchor, cursor), hi = std::max(anchor, cursor);
    for (int y = 0; y < r.height && y + scroll_y < static_cast<int>(rs.size());
         y++) {
      int x = 0;
      for (const auto &g : rs[y + scroll_y]) {
        int n = cells(g.text), local = x - scroll_x;
        if (local >= 0 && local + n <= r.width)
          c.write(r.x + local, r.y + y, g.text,
                  lo <= g.index && g.index < hi ? "selection" : role, false, n,
                  true);
        x += n;
      }
    }
    if (focused && state.editable() && cw <= r.width)
      c.set_cursor(r.x + cx - scroll_x, r.y + cy - scroll_y, cw);
  }
  Event click(int x, int y, int width, int height, bool extend = false) {
    if (state.disabled || x < 0 || y < 0 || x >= width || y >= height)
      return {};
    auto rs = rows();
    auto row = std::min(static_cast<std::size_t>(std::max(0, scroll_y + y)),
                        rs.size() - 1);
    std::size_t target = 0;
    for (std::size_t i = 0; i < row; i++)
      target += rs[i].size() + 1;
    if (!rs[row].empty())
      target = rs[row].back().index + 1;
    int cell = 0;
    for (const auto &g : rs[row]) {
      auto n = cells(g.text);
      if (x + scroll_x < cell + n) {
        target = g.index;
        break;
      }
      cell += n;
    }
    select(extend ? anchor : target, target);
    return {"select", "", ""};
  }
};
} // namespace tuivory
