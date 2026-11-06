#pragma once
// Independent C++17 Tuivory implementation. No Tuivory C/Rust/Go dependency.
#include <algorithm>
#include <cstdint>
#include <functional>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace tuivory {
namespace detail {
#include "tuivory_data.h"
#include "tuivory_fold.h"
inline bool range(unsigned cp, const unsigned int (*table)[2],
                  std::size_t count) {
  std::size_t lo = 0, hi = count;
  while (lo < hi) {
    const auto m = (lo + hi) / 2;
    if (cp < table[m][0])
      hi = m;
    else if (cp > table[m][1])
      lo = m + 1;
    else
      return true;
  }
  return false;
}
inline unsigned decode(const std::string &s, std::size_t &pos) {
  const auto first = static_cast<unsigned char>(s[pos++]);
  if (first < 128) {
    return first;
  }
  if (first >= 0xf5)
    throw std::invalid_argument("invalid UTF-8");
  int n = first >= 0xf0 ? 3 : first >= 0xe0 ? 2 : first >= 0xc2 ? 1 : 0;
  if (!n) {
    throw std::invalid_argument("invalid UTF-8");
  }
  unsigned cp = first & ((1u << (6 - n)) - 1);
  if (pos + static_cast<std::size_t>(n) > s.size())
    throw std::invalid_argument("invalid UTF-8");
  for (int i = 0; i < n; i++) {
    const auto c = static_cast<unsigned char>(s[pos]);
    if ((c & 0xc0) != 0x80)
      throw std::invalid_argument("invalid UTF-8");
    pos++;
    cp = (cp << 6) | (c & 63);
  }
  if (cp > 0x10ffff || (cp >= 0xd800 && cp <= 0xdfff) || (n == 1 && cp < 128) ||
      (n == 2 && cp < 0x800) || (n == 3 && cp < 0x10000))
    throw std::invalid_argument("invalid UTF-8");
  return cp;
}
inline bool zero(unsigned cp) {
  return range(cp, tui_zero, sizeof(tui_zero) / sizeof(tui_zero[0]));
}
inline int code_width(unsigned cp) {
  return zero(cp)                                                      ? 0
         : range(cp, tui_wide, sizeof(tui_wide) / sizeof(tui_wide[0])) ? 2
                                                                       : 1;
}
inline bool regional(unsigned cp) { return cp >= 0x1f1e6 && cp <= 0x1f1ff; }
} // namespace detail
namespace detail {
inline int cluster_width(const std::string &text) {
  std::vector<unsigned> points;
  for (std::size_t pos = 0; pos < text.size();)
    points.push_back(decode(text, pos));
  int total = 0, cluster = 0, last_width = 0;
  unsigned base = 0;
  bool available = false, virama = false;
#define IN(name, cp)                                                           \
  range(cp, tui_##name, sizeof(tui_##name) / sizeof(tui_##name[0]))
  for (std::size_t i = 0; i < points.size(); i++) {
    const unsigned cp = points[i];
    if (cp == 0x200d) {
      if (!virama && i + 1 < points.size()) {
        i++;
        last_width = 0;
      }
      continue;
    }
    if (cp == 0xfe0f && available) {
      if (IN(vs16, base))
        cluster = 2;
      available = false;
      continue;
    }
    if (cp == 0xfe0e && available) {
      if (last_width == 2 && IN(vs15, base))
        total--;
      available = false;
      continue;
    }
    if (regional(cp)) {
      int count = 0;
      for (auto j = i; j > 0 && regional(points[j - 1]); j--)
        count++;
      if (count % 2 == 1) {
        base = cp;
        continue;
      }
    } else if (cp >= 0x1f3fb && cp <= 0x1f3ff && IN(pictographic, base))
      continue;
    const int w = code_width(cp);
    if (w > 0) {
      if (virama)
        cluster = 2;
      else {
        total += cluster;
        cluster = w;
      }
      base = cp;
      last_width = w;
      available = true;
      virama = false;
    } else if (IN(virama, cp))
      virama = true;
    else if (available && IN(spacing_mc, cp)) {
      cluster = 2;
      available = false;
      virama = false;
    } else
      virama = false;
  }
#undef IN
  return total + cluster;
}
} // namespace detail
struct Grapheme {
  std::string text;
  int width = 0;
};
namespace detail {
enum class Break {
  Other,
  CR,
  LF,
  Control,
  Extend,
  ZWJ,
  Regional,
  Prepend,
  Spacing,
  L,
  V,
  T,
  LV,
  LVT
};
inline Break property(unsigned cp) {
#define PROPERTY(name, value)                                                  \
  if (range(cp, tui_##name, sizeof(tui_##name) / sizeof(tui_##name[0])))       \
    return Break::value;
  PROPERTY(grapheme_cr, CR)
  PROPERTY(grapheme_lf, LF)
  PROPERTY(grapheme_control, Control)
  PROPERTY(grapheme_extend, Extend)
  PROPERTY(grapheme_zwj, ZWJ)
  PROPERTY(grapheme_regional_indicator, Regional)
  PROPERTY(grapheme_prepend, Prepend)
  PROPERTY(grapheme_spacingmark, Spacing)
  PROPERTY(grapheme_l, L)
  PROPERTY(grapheme_v, V)
  PROPERTY(grapheme_t, T)
  PROPERTY(grapheme_lv, LV)
  PROPERTY(grapheme_lvt, LVT)
#undef PROPERTY
      return Break::Other;
}
inline bool pictographic(unsigned c) {
  return range(c, tui_extended_pictographic,
               sizeof(tui_extended_pictographic) /
                   sizeof(tui_extended_pictographic[0]));
}
inline bool consonant(unsigned c) {
  return range(c, tui_incb_consonant,
               sizeof(tui_incb_consonant) / sizeof(tui_incb_consonant[0]));
}
inline bool linker(unsigned c) {
  return range(c, tui_incb_linker,
               sizeof(tui_incb_linker) / sizeof(tui_incb_linker[0]));
}
inline bool incb_extend(unsigned c) {
  return range(c, tui_incb_extend,
               sizeof(tui_incb_extend) / sizeof(tui_incb_extend[0]));
}
} // namespace detail
inline std::vector<Grapheme> graphemes(const std::string &text) {
  using B = detail::Break;
  std::vector<Grapheme> out;
  B previous = B::Other;
  int ri = 0;
  bool ep_tail = false, ep_zwj = false, incb_base = false, incb_linker = false;
  for (std::size_t p = 0; p < text.size();) {
    const auto start = p;
    const auto cp = detail::decode(text, p);
    auto value = text.substr(start, p - start);
    const bool control = cp < 32 || (cp >= 127 && cp < 160);
    const auto current = detail::property(cp);
    const bool stop_previous =
        previous == B::CR || previous == B::LF || previous == B::Control;
    const bool stop_current =
        current == B::CR || current == B::LF || current == B::Control;
    bool join = false;
    if (!out.empty()) {
      if (previous == B::CR && current == B::LF)
        join = true;
      else if (stop_previous || stop_current)
        join = false;
      else if (previous == B::L && (current == B::L || current == B::V ||
                                    current == B::LV || current == B::LVT))
        join = true;
      else if ((previous == B::LV || previous == B::V) &&
               (current == B::V || current == B::T))
        join = true;
      else if ((previous == B::LVT || previous == B::T) && current == B::T)
        join = true;
      else if (current == B::Extend || current == B::ZWJ ||
               current == B::Spacing || previous == B::Prepend)
        join = true;
      else if (detail::consonant(cp) && incb_base && incb_linker)
        join = true;
      else if (previous == B::ZWJ && ep_zwj && detail::pictographic(cp))
        join = true;
      else if (previous == B::Regional && current == B::Regional && ri % 2 == 1)
        join = true;
    }
    const int width = control ? 1 : detail::code_width(cp);
    if (join) {
      out.back().text += value;
      out.back().width = std::max(out.back().width, width);
      if (cp == 0xfe0f ||
          (previous == B::ZWJ && ep_zwj && detail::pictographic(cp)) ||
          (previous == B::Regional && current == B::Regional))
        out.back().width = std::max(2, out.back().width);
    } else {
      out.push_back({value, width});
      ep_tail = false;
      ep_zwj = false;
      incb_base = false;
      incb_linker = false;
    }
    const bool tail = ep_tail;
    ep_zwj = current == B::ZWJ && tail;
    if (current != B::Extend)
      ep_tail = detail::pictographic(cp);
    if (detail::consonant(cp)) {
      incb_base = true;
      incb_linker = false;
    } else if (detail::linker(cp)) {
      if (incb_base)
        incb_linker = true;
    } else if (!detail::incb_extend(cp)) {
      incb_base = false;
      incb_linker = false;
    }
    ri = current == B::Regional ? (previous == B::Regional ? ri + 1 : 1) : 0;
    previous = current;
  }
  for (auto &g : out)
    g.width = detail::cluster_width(g.text);
  return out;
}
inline std::string clean(const std::string &text) {
  std::string out;
  for (std::size_t p = 0; p < text.size();) {
    auto start = p;
    auto cp = detail::decode(text, p);
    out += cp < 32 || (cp >= 127 && cp < 160) ? " "
                                              : text.substr(start, p - start);
  }
  return out;
}
inline int cells(const std::string &text) {
  int n = 0;
  for (const auto &g : graphemes(clean(text)))
    n += g.width;
  return n;
}
inline std::string clip(const std::string &text, int width,
                        bool ellipsis = false) {
  if (width <= 0)
    return "";
  const auto parts = graphemes(clean(text));
  int total = 0;
  for (const auto &g : parts)
    total += g.width;
  std::string out;
  int used = 0;
  for (const auto &g : parts) {
    if (used + g.width > width - (ellipsis && total > width ? 1 : 0))
      break;
    out += g.text;
    used += g.width;
  }
  if (ellipsis && total > width)
    out += '~';
  return out;
}
struct Rect {
  int x = 0, y = 0, width = 0, height = 0;
  bool contains(int px, int py) const {
    return px >= x && py >= y && px < x + width && py < y + height;
  }
};
struct Event {
  std::string kind, id, text;
};
struct State {
  bool disabled = false, read_only = false, busy = false, selected = false,
       edited = false, invalid = false;
  bool focusable() const { return !disabled; }
  bool activatable() const { return !disabled && !busy; }
  bool editable() const { return activatable() && !read_only; }
  std::string role() const {
    return disabled   ? "disabled"
           : invalid  ? "error"
           : selected ? "selection"
           : edited   ? "edited"
                      : "body";
  }
  std::string markers() const {
    return std::string(disabled ? "-" : "") + (invalid ? "!" : "") +
           (selected ? ">" : "") + (edited ? "*" : "") + (busy ? "~" : "") +
           (read_only ? "=" : "");
  }
};
struct Style {
  unsigned foreground = 7, background = 0;
  bool bold = false, dim = false, underline = false;
  std::string sgr() const {
    auto color = [](unsigned c, bool bg) {
      std::string prefix = bg ? "48" : "38";
      if (c & 0x1000000)
        return prefix + ";2;" + std::to_string((c >> 16) & 255) + ";" +
               std::to_string((c >> 8) & 255) + ";" + std::to_string(c & 255);
      return c < 8    ? std::to_string((bg ? 40 : 30) + c)
             : c < 16 ? std::to_string((bg ? 100 : 90) + c - 8)
                      : prefix + ";5;" + std::to_string(c);
    };
    return "\033[0;" + color(foreground, false) + ";" +
           color(background, true) + (bold ? ";1" : "") + (dim ? ";2" : "") +
           (underline ? ";4" : "") + "m";
  }
};
class Palette {
  int theme_, profile_;

public:
  explicit Palette(std::string theme = "dark", std::string profile = "256") {
    theme_ = theme == "dark"         ? 0
             : theme == "light"      ? 1
             : theme == "blackwhite" ? 2
                                     : -1;
    profile_ = profile == "8"           ? 0
               : profile == "16"        ? 1
               : profile == "256"       ? 2
               : profile == "truecolor" ? 3
                                        : -1;
    if (theme_ < 0 || profile_ < 0)
      throw std::invalid_argument("unknown palette");
  }
  Style style(const std::string &role = "body", bool focused = false) const {
    int i = 0;
    for (; i < 16; i++)
      if (role == detail::tui_roles[i])
        break;
    if (i == 16)
      throw std::invalid_argument("unknown role");
    const auto &p = detail::tui_palette_data[(theme_ * 4 + profile_) * 16 + i];
    return {p[0], p[1], p[2] != 0, role == "disabled", focused};
  }
};
class Canvas {
public:
  struct Cell {
    std::string text = " ";
    Style style;
    int owner = -1;
  };
  int width, height;
  Palette palette;
  std::vector<std::vector<Cell>> data;
  std::optional<std::pair<int, int>> cursor;
  Canvas(int w, int h, Palette p = Palette())
      : width(w), height(h), palette(std::move(p)) {
    if (w < 0 || h < 0 || static_cast<long long>(w) * h > 1000000)
      throw std::invalid_argument("invalid dimensions");
    data.resize(h, std::vector<Cell>(w));
    for (auto &row : data)
      for (auto &c : row)
        c.style = palette.style("surface");
  }
  void erase(int x, int y) {
    auto &row = data[y];
    const int start = row[x].owner >= 0 ? row[x].owner : x;
    int end = start + 1;
    while (end < width && row[end].owner == start)
      end++;
    for (int i = start; i < end; i++) {
      row[i].text = " ";
      row[i].owner = -1;
    }
  }
  void write(int x, int y, const std::string &text,
             const std::string &role = "body", bool focused = false,
             int extent = -1, bool preserve = false) {
    if (y < 0 || y >= height)
      return;
    const int limit = std::min(width, extent < 0 ? width : x + extent);
    auto style = palette.style(role, focused);
    if (!preserve && (role == "body" || role == "hint" || role == "info" ||
                      role == "success" || role == "warning" ||
                      role == "error" || role == "header"))
      style.background = palette.style("surface").background;
    for (const auto &g : graphemes(clean(text))) {
      if (g.width <= 0)
        continue;
      if (x >= limit)
        break;
      if (x < 0 || x + g.width > limit) {
        for (int i = std::max(0, x); i < std::min(limit, x + g.width); i++) {
          erase(i, y);
          data[y][i].style = style;
        }
        x += g.width;
        continue;
      }
      for (int i = x; i < x + g.width; i++)
        erase(i, y);
      data[y][x] = {g.text, style, -1};
      for (int i = x + 1; i < x + g.width; i++)
        data[y][i] = {"", style, x};
      x += g.width;
    }
  }
  void fill(Rect r, const std::string &role = "surface") {
    for (int y = std::max(0, r.y); y < std::min(height, r.y + r.height); y++)
      write(r.x, y, std::string(std::max(0, r.width), ' '), role, false,
            r.width, true);
  }
  Rect panel(Rect r, const std::string &title = "", bool focused = false,
             bool ascii = false) {
    fill(r);
    if (r.width < 2 || r.height < 2)
      return {r.x, r.y, 0, 0};
    const auto role = focused ? "focus.border" : "hint";
    const std::vector<std::string> b =
        ascii     ? std::vector<std::string>{"+", "+", "+", "+", "-", "|"}
        : focused ? std::vector<std::string>{"╔", "╗", "╚", "╝", "═", "║"}
                  : std::vector<std::string>{"┌", "┐", "└", "┘", "─", "│"};
    std::string h;
    for (int i = 0; i < r.width - 2; i++)
      h += b[4];
    write(r.x, r.y, b[0] + h + b[1], role);
    write(r.x, r.y + r.height - 1, b[2] + h + b[3], role);
    for (int y = r.y + 1; y < r.y + r.height - 1; y++) {
      write(r.x, y, b[5], role);
      write(r.x + r.width - 1, y, b[5], role);
    }
    write(r.x + 2, r.y, clip(title, r.width - 4), role);
    return {r.x + 1, r.y + 1, r.width - 2, r.height - 2};
  }
  void set_cursor(int x, int y, int glyph_width = 1) {
    if (x >= 0 && x + std::max(1, glyph_width) <= width && y >= 0 && y < height)
      cursor = {{x, y}};
    else
      cursor.reset();
  }
  std::vector<std::string> lines() const {
    std::vector<std::string> out;
    for (const auto &row : data) {
      std::string line;
      for (const auto &c : row)
        line += c.text;
      out.push_back(line);
    }
    return out;
  }
  std::string ansi() const {
    std::string out = "\033[?25l";
    for (int y = 0; y < height; y++) {
      out += "\033[" + std::to_string(y + 1) + ";1H";
      std::string previous;
      for (const auto &c : data[y]) {
        if (c.owner >= 0)
          continue;
        const auto style = c.style.sgr();
        if (style != previous) {
          out += style;
          previous = style;
        }
        out += c.text;
      }
    }
    out += "\033[0m";
    if (cursor)
      out += "\033[" + std::to_string(cursor->second + 1) + ";" +
             std::to_string(cursor->first + 1) + "H\033[?25h";
    return out;
  }
};
struct Node {
  std::string id, name, parent, secondary, icon, ascii_icon;
  std::optional<unsigned long long> count;
  bool branch = false;
};
class Tree {
private:
  std::vector<Node> nodes;
  std::map<std::string, int> depth;
  std::set<std::string> branches;

public:
  std::set<std::string> expanded;
  std::string selected;
  int scroll = 0, horizontal = 0;
  explicit Tree(std::vector<Node> input) : nodes(std::move(input)) {
    std::set<std::string> ids;
    std::vector<std::string> stack;
    for (const auto &n : nodes) {
      if (n.id.empty() || !ids.insert(n.id).second)
        throw std::invalid_argument("invalid node ID");
      if (n.parent.empty())
        stack.clear();
      else {
        const auto p = std::find(stack.begin(), stack.end(), n.parent);
        if (p == stack.end())
          throw std::invalid_argument("tree requires contiguous preorder");
        stack.erase(p + 1, stack.end());
        branches.insert(n.parent);
      }
      if (stack.size() > 128)
        throw std::invalid_argument("tree depth exceeds 128");
      depth[n.id] = static_cast<int>(stack.size());
      stack.push_back(n.id);
      if (n.branch)
        branches.insert(n.id);
    }
    reconcile(1);
  }
  std::vector<Node> visible() const {
    std::vector<Node> out;
    std::set<std::string> seen;
    for (const auto &n : nodes)
      if (n.parent.empty() ||
          (seen.count(n.parent) && expanded.count(n.parent))) {
        out.push_back(n);
        seen.insert(n.id);
      }
    return out;
  }
  std::vector<Node> reconcile(int height) {
    for (auto i = expanded.begin(); i != expanded.end();)
      if (!branches.count(*i))
        i = expanded.erase(i);
      else
        ++i;
    auto rows = visible();
    auto index = [&]() {
      for (std::size_t i = 0; i < rows.size(); i++)
        if (rows[i].id == selected)
          return static_cast<int>(i);
      return -1;
    };
    while (!selected.empty() && index() < 0) {
      const auto n =
          std::find_if(nodes.begin(), nodes.end(),
                       [&](const auto &n) { return n.id == selected; });
      selected = n == nodes.end() ? "" : n->parent;
    }
    if (selected.empty() && !rows.empty())
      selected = rows[0].id;
    const int h = std::max(1, height), i = index();
    scroll = std::max(0, std::min(scroll, static_cast<int>(rows.size()) - h));
    if (i >= 0) {
      if (i < scroll)
        scroll = i;
      if (i >= scroll + h)
        scroll = i - h + 1;
    }
    return rows;
  }
  Event handle(const std::string &action, int height = 10) {
    const auto rows = reconcile(height);
    if (rows.empty())
      return {};
    int i = 0;
    for (; rows[i].id != selected; i++) {
    }
    const auto old = selected;
    const auto node = rows[i];
    int target = i;
    if (action == "up")
      target = i - 1;
    else if (action == "down")
      target = i + 1;
    else if (action == "home")
      target = 0;
    else if (action == "end")
      target = static_cast<int>(rows.size()) - 1;
    else if (action == "page_up")
      target = i - std::max(1, height);
    else if (action == "page_down")
      target = i + std::max(1, height);
    else if (action == "pan_left")
      horizontal = std::max(0, horizontal - 4);
    else if (action == "pan_right")
      horizontal = std::min(65535, horizontal + 4);
    else if (action == "activate")
      return {"activate", old, {}};
    else if (action == "left") {
      if (expanded.erase(old)) {
        reconcile(height);
        return {"collapse", old, {}};
      }
      if (!node.parent.empty())
        selected = node.parent;
    } else if ((action == "right" || action == "toggle") &&
               branches.count(old)) {
      if (action == "toggle" && expanded.erase(old)) {
        reconcile(height);
        return {"collapse", old, {}};
      }
      if (expanded.insert(old).second) {
        reconcile(height);
        return {"expand", old, {}};
      }
      if (i + 1 < static_cast<int>(rows.size()) && rows[i + 1].parent == old)
        target++;
    }
    target = std::clamp(target, 0, static_cast<int>(rows.size()) - 1);
    if (target != i)
      selected = rows[target].id;
    reconcile(height);
    return selected != old ? Event{"select", selected, {}} : Event{};
  }
  Event click(int x, int y, int height = 10) {
    auto rows = reconcile(height);
    if (y < 0 || y >= height || scroll + y >= static_cast<int>(rows.size()))
      return {};
    auto old = selected;
    const auto &n = rows[scroll + y];
    selected = n.id;
    if (x >= 2 && x + horizontal == 2 + 2 * depth[n.id]) {
      auto e = handle("toggle", height);
      if (!e.kind.empty())
        return e;
    }
    return old != selected ? Event{"select", selected, {}} : Event{};
  }
  void draw(Canvas &c, Rect r, bool focused = true, bool ascii = false) {
    c.fill(r);
    const auto rows = reconcile(r.height);
    for (int y = 0; y < r.height && scroll + y < static_cast<int>(rows.size());
         y++) {
      const auto &n = rows[scroll + y];
      const bool current = n.id == selected;
      const std::string arrow = branches.count(n.id) ? expanded.count(n.id)
                                                           ? ascii ? "v" : "▾"
                                                       : ascii ? ">"
                                                               : "▸"
                                                     : " ";
      const auto icon = ascii ? n.ascii_icon : n.icon;
      auto text = std::string(depth[n.id] * 2, ' ') + arrow + " " +
                  (icon.empty() ? "" : icon + " ") + n.name +
                  (n.secondary.empty() ? "" : "  " + n.secondary) +
                  (n.count ? " (" + std::to_string(*n.count) + ")" : "");
      auto gs = graphemes(text);
      int skipped = 0;
      std::size_t start = 0;
      while (start < gs.size() && skipped < horizontal)
        skipped += gs[start++].width;
      text.clear();
      for (; start < gs.size(); start++)
        text += gs[start].text;
      c.write(r.x, r.y + y,
              std::string(current ? "> " : "  ") +
                  clip(text, std::max(0, r.width - 2), true),
              current ? "selection" : "body", focused && current, r.width);
    }
  }
};
} // namespace tuivory
#include "tuivory_workspace.hpp"

#include "tuivory_text.hpp"

#include "tuivory_forms.hpp"

#include "tuivory_focus.hpp"

namespace tuivory {
inline std::string fold(const std::string &text) {
  std::string out;
  for (std::size_t p = 0; p < text.size();) {
    auto start = p;
    auto cp = detail::decode(text, p);
    std::size_t left = 0, right = sizeof(detail::tui_fold_data) /
                                  sizeof(detail::tui_fold_data[0]);
    while (left < right) {
      auto m = (left + right) / 2;
      if (detail::tui_fold_data[m].cp < cp)
        left = m + 1;
      else
        right = m;
    }
    if (left <
            sizeof(detail::tui_fold_data) / sizeof(detail::tui_fold_data[0]) &&
        detail::tui_fold_data[left].cp == cp)
      out += detail::tui_fold_data[left].text;
    else
      out += text.substr(start, p - start);
  }
  return out;
}
} // namespace tuivory

#include "tuivory_collections.hpp"

#include "tuivory_menu.hpp"
