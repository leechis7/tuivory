#pragma once
namespace tuivory {
struct DocumentRange {
  std::size_t start = 0, end = 0;
};
struct DocumentSpan {
  std::size_t start = 0, end = 0;
  std::string role = "body";
};
struct DocumentGlyph {
  int x = 0;
  std::string text;
  std::size_t index = 0;
  int width = 0;
  std::string role = "body";
  bool cursor = false;
};
struct DocumentLine {
  int number = 0;
  std::string prefix;
  std::vector<DocumentGlyph> glyphs;
  std::vector<std::pair<int, std::size_t>> hits;
};
namespace document_detail {
inline bool role(const std::string &r) {
  static const std::set<std::string> roles{"body",
                                           "hint",
                                           "info",
                                           "success",
                                           "warning",
                                           "error",
                                           "header",
                                           "field",
                                           "selection",
                                           "button",
                                           "disabled",
                                           "edited",
                                           "syntax.keyword",
                                           "syntax.function",
                                           "syntax.type",
                                           "syntax.string",
                                           "syntax.number",
                                           "syntax.comment",
                                           "syntax.parameter"};
  return roles.count(r);
}
inline std::string text(std::string value) {
  dialog_detail::text(value, 1000000);
  return value;
}
inline std::string family(const std::string &role) {
  static const std::map<std::string, std::string> m{
      {"keyword", "info"},   {"function", "success"}, {"type", "header"},
      {"string", "warning"}, {"number", "edited"},    {"comment", "hint"},
      {"parameter", "error"}};
  auto it = m.find(role.substr(7));
  return it == m.end() ? "body" : it->second;
}
inline bool br(const std::string &g) {
  return g == "\n" || g == "\r" || g == "\r\n";
}
inline std::string display(const std::string &g) {
  for (std::size_t i = 0; i < g.size();) {
    auto cp = detail::decode(g, i);
    if (cp < 32 || (cp >= 127 && cp < 160))
      return " ";
  }
  return g;
}
} // namespace document_detail
/** Explicit [role]text[/] markup; literal source setters never parse tags. */
inline std::pair<std::string, std::vector<DocumentSpan>>
parse_markup(const std::string &markup) {
  document_detail::text(markup);
  std::string source;
  std::vector<std::pair<std::size_t, std::string>> changes{{0, "body"}};
  std::vector<std::string> stack{"body"};
  std::size_t at = 0;
  while (at < markup.size()) {
    if (markup.compare(at, 2, "[[") == 0) {
      source += '[';
      at += 2;
      continue;
    }
    if (markup[at] == '[') {
      auto end = markup.find(']', at);
      if (end == std::string::npos)
        throw std::invalid_argument("unbalanced markup");
      auto tag = markup.substr(at + 1, end - at - 1);
      if (tag == "/") {
        if (stack.size() == 1)
          throw std::invalid_argument("unbalanced markup");
        stack.pop_back();
      } else {
        if (!document_detail::role(tag))
          throw std::invalid_argument("unknown markup role");
        stack.push_back(tag);
      }
      changes.emplace_back(source.size(), stack.back());
      at = end + 1;
      continue;
    }
    auto end = markup.find('[', at);
    if (end == std::string::npos)
      end = markup.size();
    source += markup.substr(at, end - at);
    at = end;
  }
  if (stack.size() != 1)
    throw std::invalid_argument("unbalanced markup");
  std::vector<DocumentSpan> spans;
  std::size_t offset = 0, which = 0, index = 0;
  for (const auto &g : graphemes(source)) {
    while (which + 1 < changes.size() && changes[which + 1].first <= offset)
      which++;
    auto role = changes[which].second;
    if (role != "body") {
      if (!spans.empty() && spans.back().end == index &&
          spans.back().role == role)
        spans.back().end++;
      else
        spans.push_back({index, index + 1, role});
    }
    offset += g.text.size();
    index++;
  }
  return {source, spans};
}
class TextDocument {
  std::optional<syntax_detail::Binding> binding_;
  std::string syntax_source_, search_source_;
  std::vector<DocumentSpan> styles_;
  std::vector<DocumentRange> matches_;
  std::vector<std::vector<std::pair<int, std::size_t>>> hits_;
  std::optional<std::tuple<std::string, std::size_t, std::size_t>> last_;
  int height_ = 0;
  bool reveal_;
  void validate_scroll() const {
    if (scroll_x < 0 || scroll_y < 0 || scroll_x > 1000000 ||
        scroll_y > 1000000)
      throw std::invalid_argument("invalid document scroll position");
  }
  template <class R> void validate(const std::vector<R> &ranges) const {
    if (ranges.size() > 1000000)
      throw std::invalid_argument("too many document ranges");
    auto n = graphemes(document_detail::text(buffer.value)).size();
    for (const auto &r : ranges)
      if (r.end < r.start || r.end > n)
        throw std::invalid_argument("invalid document grapheme range");
  }

  void apply_syntax(const SyntaxAnalysis &analysis) {
    if (buffer.secret)
      throw std::invalid_argument(
          "syntax analysis unavailable for secret buffers");
    analysis.validate(buffer.value);
    std::vector<DocumentSpan> spans;
    for (const auto &t : analysis.tokens)
      spans.push_back({t.start, t.end, syntax_role_style(t.role)});
    set_byte_syntax(spans);
  }
  void refresh_syntax_safe() {
    try {
      refresh_syntax();
    } catch (...) {
    }
  }

public:
  Text buffer;
  bool wrap = false, line_numbers = true;
  int scroll_x = 0, scroll_y = 0;
  explicit TextDocument(std::string text = "", bool read_only = false)
      : syntax_source_(text), search_source_(text), reveal_(!read_only),
        buffer(document_detail::text(std::move(text))),
        line_numbers(!read_only) {
    buffer.state.read_only = read_only;
  }
  static TextDocument editor(std::string text = "") {
    return TextDocument(std::move(text));
  }
  static TextDocument viewer(std::string text = "") {
    return TextDocument(std::move(text), true);
  }
  std::vector<DocumentSpan> syntax() const { return styles_; }
  std::vector<DocumentRange> search_matches() const { return matches_; }
  void set_text(std::string text) {
    document_detail::text(text);
    auto state = buffer.state;
    bool secret = buffer.secret;
    buffer = Text(text);
    buffer.state = state;
    buffer.secret = secret;
    styles_.clear();
    matches_.clear();
    syntax_source_ = search_source_ = text;
    scroll_x = scroll_y = 0;
    hits_.clear();
    last_.reset();
    reveal_ = !state.read_only;
    refresh_syntax_safe();
  }
  void set_syntax(std::vector<DocumentSpan> spans) {
    validate(spans);
    for (const auto &s : spans)
      if (!document_detail::role(s.role))
        throw std::invalid_argument("unknown document role");
    styles_ = std::move(spans);
    syntax_source_ = buffer.value;
  }
  void set_search_matches(std::vector<DocumentRange> matches) {
    validate(matches);
    matches_ = std::move(matches);
    search_source_ = buffer.value;
  }
  void set_byte_syntax(const std::vector<DocumentSpan> &spans) {
    std::map<std::size_t, std::size_t> offsets;
    std::size_t offset = 0, index = 0;
    for (const auto &g : graphemes(buffer.value)) {
      offsets[offset] = index++;
      offset += g.text.size();
    }
    offsets[offset] = index;
    std::vector<DocumentSpan> converted;
    for (const auto &s : spans) {
      auto a = offsets.find(s.start), b = offsets.find(s.end);
      if (a == offsets.end() || b == offsets.end())
        throw std::invalid_argument("offset splits grapheme or outside text");
      converted.push_back({a->second, b->second, s.role});
    }
    set_syntax(std::move(converted));
  }
  void set_markup(const std::string &markup) {
    auto parsed = parse_markup(markup);
    set_syntax_analyzer({});
    set_text(std::move(parsed.first));
    set_syntax(std::move(parsed.second));
  }
  void set_syntax_analysis(const SyntaxAnalysis &analysis) {
    if (binding_ && binding_->refreshing)
      throw std::invalid_argument("recursive syntax analysis");
    apply_syntax(analysis);
    binding_ = syntax_detail::Binding{{},    {},           buffer.value,
                                      false, std::nullopt, false};
  }
  void set_syntax_analyzer(SyntaxAnalyzer analyzer,
                           SyntaxRequest request = {}) {
    if (binding_ && binding_->refreshing)
      throw std::invalid_argument("recursive syntax analysis");
    if (!analyzer) {
      binding_.reset();
      styles_.clear();
      syntax_source_ = buffer.value;
      return;
    }
    if (buffer.secret)
      throw std::invalid_argument(
          "syntax analysis unavailable for secret buffers");
    dialog_detail::text(request.language, 128);
    dialog_detail::text(request.dialect, 128);
    auto analysis = analyzer(buffer.value, request);
    apply_syntax(analysis);
    binding_ = syntax_detail::Binding{std::move(analyzer), std::move(request),
                                      buffer.value,        false,
                                      std::nullopt,        false};
  }
  std::optional<std::string> syntax_error() const {
    return !buffer.secret && binding_ ? binding_->error : std::nullopt;
  }
  void refresh_syntax() {
    if (buffer.secret) {
      if (binding_) {
        binding_->source.clear();
        binding_->dirty = true;
      }
      styles_.clear();
      return;
    }
    if (!binding_)
      return;
    auto &b = *binding_;
    if (b.refreshing)
      throw std::invalid_argument("recursive syntax analysis");
    if (b.source == buffer.value && !b.dirty) {
      if (b.error)
        throw std::invalid_argument(*b.error);
      return;
    }
    auto source = buffer.value;
    b.refreshing = true;
    try {
      if (b.analyzer)
        apply_syntax(b.analyzer(source, b.request));
      else {
        styles_.clear();
        syntax_source_ = source;
      }
      b.error.reset();
      b.source = source;
      b.dirty = false;
      b.refreshing = false;
    } catch (const std::exception &error) {
      styles_.clear();
      syntax_source_ = buffer.value;
      b.error = error.what();
      b.source = source;
      b.dirty = false;
      b.refreshing = false;
      throw;
    } catch (...) {
      styles_.clear();
      syntax_source_ = buffer.value;
      b.error = "syntax analyzer failed";
      b.source = source;
      b.dirty = false;
      b.refreshing = false;
      throw;
    }
  }
  void reveal_cursor() { reveal_ = true; }
  Event handle(const std::string &action, const std::string &text = "") {
    validate_scroll();
    if (buffer.state.disabled)
      return {};
    int step = std::max(1, height_);
    if (action == "page_up")
      scroll_y = std::max(0, scroll_y - step);
    else if (action == "page_down")
      scroll_y = std::min(1000000, scroll_y + step);
    else if (action == "scroll_up")
      scroll_y = std::max(0, scroll_y - 1);
    else if (action == "scroll_down")
      scroll_y = std::min(1000000, scroll_y + 1);
    else if (action == "scroll_left")
      scroll_x = std::max(0, scroll_x - 4);
    else if (action == "scroll_right")
      scroll_x = std::min(1000000, scroll_x + 4);
    else {
      if ((action == "insert" || action == "paste" || action == "newline") &&
          buffer.state.editable()) {
        auto raw = document_detail::text(action == "newline" ? "\n" : text);
        std::string addition;
        for (std::size_t p = 0; p < raw.size();) {
          auto start = p;
          auto cp = detail::decode(raw, p);
          if (cp == '\r') {
            if (p < raw.size() && raw[p] == '\n')
              p++;
            if (buffer.multiline)
              addition += '\n';
          } else if (cp == '\n') {
            if (buffer.multiline)
              addition += '\n';
          } else if (cp == '\t')
            addition += ' ';
          else if (cp >= 32 && !(cp >= 127 && cp < 160))
            addition += raw.substr(start, p - start);
        }
        auto selected = buffer.selection_bytes();
        if (buffer.value.size() - (selected.second - selected.first) +
                addition.size() >
            1000000)
          throw std::invalid_argument("document source exceeds limit");
      }
      auto e = buffer.handle(action, text);
      if (e.kind == "select" || e.kind == "change" || e.kind == "cut")
        reveal_ = true;
      refresh_syntax_safe();
      return e;
    }
    reveal_ = false;
    return {"scroll", "", ""};
  }
  std::vector<DocumentLine> layout(int width, int height) {
    validate_scroll();
    if (width < 0 || height < 0 || width > 1000000 || height > 1000000)
      throw std::invalid_argument("invalid document dimensions");
    document_detail::text(buffer.value);
    refresh_syntax_safe();
    height_ = height;
    hits_.clear();
    if (!width || !height)
      return {};
    buffer.select(buffer.anchor, buffer.cursor);
    auto source = buffer.value;
    if (source != syntax_source_) {
      styles_.clear();
      syntax_source_ = source;
    }
    if (source != search_source_) {
      matches_.clear();
      search_source_ = source;
    }
    auto raw = graphemes(source);
    std::vector<std::string> shown, roles(raw.size(), "body");
    for (const auto &g : raw)
      shown.push_back(buffer.secret ? "*" : g.text);
    auto lo = std::min(buffer.anchor, buffer.cursor),
         hi = std::max(buffer.anchor, buffer.cursor);
    if (!buffer.secret) {
      for (const auto &s : styles_)
        for (auto i = s.start; i < std::min(s.end, roles.size()); i++)
          roles[i] = s.role;
      for (const auto &s : matches_)
        for (auto i = s.start; i < std::min(s.end, roles.size()); i++)
          roles[i] = "edited";
    }
    for (auto i = lo; i < hi; i++)
      roles[i] = "selection";
    if (buffer.state.disabled)
      std::fill(roles.begin(), roles.end(), "disabled");
    using Item = std::pair<std::size_t, std::string>;
    struct Logical {
      std::vector<Item> items;
      std::size_t end = 0;
    };
    std::vector<Logical> logical(1);
    for (std::size_t i = 0; i < shown.size(); i++) {
      if (document_detail::br(shown[i])) {
        logical.back().end = i;
        logical.push_back({{}, i + 1});
      } else {
        logical.back().items.emplace_back(i,
                                          document_detail::display(shown[i]));
        logical.back().end = i + 1;
      }
    }
    auto signature = std::make_tuple(source, buffer.cursor, buffer.anchor);
    bool reveal =
        reveal_ || ((!last_ || *last_ != signature) && !buffer.state.read_only);
    if (reveal && !wrap) {
      for (std::size_t number = 0; number < logical.size(); number++) {
        const auto &line = logical[number];
        auto start = line.items.empty() ? line.end : line.items.front().first;
        if (start <= buffer.cursor && buffer.cursor <= line.end) {
          int pw = line_numbers ? cells(std::to_string(number + 1) + " ") : 0,
              available = std::max(1, width - pw), col = 0, cw = 1;
          for (const auto &item : line.items) {
            if (item.first < buffer.cursor)
              col += cells(item.second);
            if (item.first == buffer.cursor)
              cw = std::max(1, cells(item.second));
          }
          scroll_x = std::max({0, std::min(scroll_x, col),
                               col + std::min(cw, available) - available});
          break;
        }
      }
    }
    int total = 0;
    for (const auto &g : shown)
      total += cells(g);
    scroll_x = std::max(0, std::min(scroll_x, total));
    std::vector<DocumentLine> rows;
    for (std::size_t number = 0; number < logical.size(); number++) {
      const auto &line = logical[number];
      auto prefix =
          line_numbers ? clip(std::to_string(number + 1) + " ", width) : "";
      int pw = cells(prefix), available = std::max(0, width - pw), used = 0;
      std::vector<std::vector<Item>> groups(1);
      for (const auto &item : line.items) {
        int w = cells(item.second);
        if (wrap && !groups.back().empty() && used + w > available) {
          groups.emplace_back();
          used = 0;
        }
        groups.back().push_back(item);
        used += w;
      }
      if (wrap && !groups.back().empty() && used >= available &&
          line.end == buffer.cursor && !buffer.state.read_only)
        groups.emplace_back();
      for (std::size_t segment = 0; segment < groups.size(); segment++) {
        const auto &group = groups[segment];
        int x = pw;
        DocumentLine row;
        row.number = static_cast<int>(number + 1);
        row.prefix = prefix;
        auto start = group.empty() ? line.end : group.front().first;
        row.hits.emplace_back(pw, start);
        for (const auto &item : group) {
          int w = cells(item.second), local = x - (wrap ? 0 : scroll_x);
          row.hits.emplace_back(local, item.first);
          if (local >= pw && local + w <= width)
            row.glyphs.push_back({local, item.second, item.first, w,
                                  roles[item.first],
                                  item.first == buffer.cursor});
          x += w;
        }
        auto finish = group.empty() ? line.end : group.back().first + 1;
        int local = x - (wrap ? 0 : scroll_x);
        row.hits.emplace_back(local, finish);
        if (finish == buffer.cursor && local >= pw && local < width &&
            (segment == groups.size() - 1 || buffer.cursor < line.end))
          row.glyphs.push_back({local, " ", finish, 1,
                                buffer.state.disabled ? "disabled" : "body",
                                true});
        rows.push_back(std::move(row));
      }
    }
    if (reveal)
      for (std::size_t i = 0; i < rows.size(); i++)
        if (std::any_of(rows[i].glyphs.begin(), rows[i].glyphs.end(),
                        [](const auto &g) { return g.cursor; }))
          scroll_y = std::max({0, std::min(scroll_y, static_cast<int>(i)),
                               static_cast<int>(i) - height + 1});
    scroll_y = std::max(
        0, std::min(scroll_y,
                    std::max(0, static_cast<int>(rows.size()) - height)));
    auto end =
        std::min(rows.size(), static_cast<std::size_t>(scroll_y) + height);
    std::vector<DocumentLine> visible(rows.begin() + scroll_y,
                                      rows.begin() + end);
    for (const auto &r : visible)
      hits_.push_back(r.hits);
    last_ = std::move(signature);
    reveal_ = false;
    return visible;
  }
  void draw(Canvas &canvas, Rect bounds, bool focused = true, bool = false) {
    popup_detail::rect(bounds);
    auto role = buffer.state.read_only ? canvas.surface_role : "editor";
    canvas.fill(bounds, role);
    auto rows = layout(bounds.width, bounds.height);
    std::optional<std::tuple<int, int, int>> cursor;
    for (std::size_t y = 0; y < rows.size(); y++) {
      const auto &row = rows[y];
      canvas.write_style(bounds.x, bounds.y + static_cast<int>(y), row.prefix,
                         canvas.palette.text_on_surface(
                             buffer.state.disabled ? "disabled" : "hint", role),
                         bounds.width);
      for (const auto &g : row.glyphs) {
        Style style;
        if (g.role.rfind("syntax.", 0) == 0)
          style = syntax_style(canvas.palette, g.role, role);
        else if (g.role == "selection" || g.role == "edited" ||
                 g.role == "field" || g.role == "button" || g.role == "header")
          style = canvas.palette.style(g.role);
        else
          style = canvas.palette.text_on_surface(g.role, role);
        canvas.write_style(bounds.x + g.x, bounds.y + static_cast<int>(y),
                           g.text, style, g.width);
        if (g.cursor)
          cursor = std::make_tuple(bounds.x + g.x,
                                   bounds.y + static_cast<int>(y), g.width);
      }
    }
    if (focused && !buffer.state.read_only && !buffer.state.disabled && cursor)
      canvas.set_cursor(std::get<0>(*cursor), std::get<1>(*cursor),
                        std::get<2>(*cursor));
  }
  Event click(int x, int y, int width, int height, bool extend = false) {
    if (buffer.state.disabled || x < 0 || y < 0 || x >= width || y >= height)
      return {};
    layout(width, height);
    if (hits_.empty())
      return {};
    const auto &row =
        hits_[std::min(static_cast<std::size_t>(y), hits_.size() - 1)];
    auto at = row.front().second;
    for (const auto &hit : row)
      if (hit.first <= x)
        at = hit.second;
    buffer.select(extend ? buffer.anchor : at, at);
    reveal_ = true;
    return {"select", "", ""};
  }
};
} // namespace tuivory
