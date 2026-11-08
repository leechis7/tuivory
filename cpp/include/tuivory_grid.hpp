#pragma once
// Independent C++ grid: source data and approval transactions belong to the
// host.
#include <array>
#include <memory>
#include <tuple>
namespace tuivory {
struct GridColumn {
  std::string id, label;
  int width = 12;
  bool editable = false, hidden = false;
  std::string pin;
};
struct GridRecord {
  std::string id;
  std::map<std::string, std::optional<std::string>> cells;
  State state;
  std::map<std::string, State> cell_states;
};
struct GridValue {
  std::string text;
  bool null = false;
};
class GridSource {
public:
  virtual ~GridSource() = default;
  virtual std::size_t size() const = 0;
  virtual GridRecord row(std::size_t index) const = 0;
  virtual std::optional<std::size_t> index_of(const std::string &id) const = 0;
};
class MemoryRows : public GridSource {
  std::vector<GridRecord> rows_;
  std::map<std::string, std::size_t> indices_;

public:
  explicit MemoryRows(std::vector<GridRecord> rows) : rows_(std::move(rows)) {
    for (std::size_t i = 0; i < rows_.size(); i++) {
      if (rows_[i].id.empty() || !indices_.emplace(rows_[i].id, i).second)
        throw std::invalid_argument("nonempty unique row IDs required");
      dialog_detail::text(rows_[i].id, 1000000);
      if (rows_[i].cells.size() > 65536)
        throw std::invalid_argument("too many grid cells");
      for (const auto &entry : rows_[i].cells)
        if (entry.second)
          dialog_detail::text(*entry.second, 16 * 1024 * 1024);
    }
  }
  std::size_t size() const override { return rows_.size(); }
  GridRecord row(std::size_t i) const override { return rows_.at(i); }
  std::optional<std::size_t> index_of(const std::string &id) const override {
    auto p = indices_.find(id);
    return p == indices_.end() ? std::nullopt
                               : std::optional<std::size_t>(p->second);
  }
};
struct GridOptions {
  bool row_numbers = false, vertical_lines = false, horizontal_lines = false,
       striped = false, use_surface = false, hide_header = false,
       status_bar = false, ascii = false;
  bool highlight_cell = true, highlight_row = false, preserve_edited = true,
       show_cell_markers = false;
  bool disable_keyboard = false, disable_mouse = false, disable_editing = false,
       disable_copy = false, disable_resize = false,
       disable_header_sort = false;
  int padding = 0, row_spacing = 0, gutter_width = 0, max_copy_cells = 10000;
  std::string selection = "cell";
  std::vector<std::string> status_fields{"position", "column", "selection",
                                         "sort",     "filter", "loading",
                                         "more",     "meta",   "error"};
  GridOptions with_density(const std::string &density) const {
    if (density != "compact" && density != "normal" && density != "comfortable")
      throw std::invalid_argument("invalid grid density");
    auto o = *this;
    o.padding = density != "compact";
    o.row_spacing = density == "comfortable";
    return o;
  }
};
inline GridOptions grid_preset(const std::string &name = "simple") {
  GridOptions o;
  if (name.empty() || name == "simple")
    return o;
  if (name != "data")
    throw std::invalid_argument("unknown grid preset");
  o.row_numbers = o.vertical_lines = o.use_surface = o.status_bar =
      o.highlight_row = o.show_cell_markers = true;
  o.padding = 1;
  return o;
}
struct GridColumnOptions {
  std::string align = "left";
  int min_width = 1, max_width = 4096;
  bool auto_fit = false;
  int expand = 0;
  std::string overflow = "ellipsis";
};
struct GridCellInfo {
  std::string display;
  bool has_display = false, null = false, numeric = false;
  State state;
  std::string metadata;
};
struct GridRange {
  std::string anchor_row, anchor_column, end_row, end_column;
};
struct GridLabels {
  std::string null_text = "NULL", loading = "loading", empty = "empty",
              range = "range", more = "more";
};
struct GridDataStatus {
  std::size_t total_rows = 0;
  std::string metadata, filter, error;
  bool loading = false, has_more = false;
};
struct GridSpan {
  std::string id;
  int x = 0, width = 0;
};
struct GridGeometry {
  std::size_t top = 0;
  int left = 0, gutter = 0, header_rows = 0, footer_rows = 0, body_rows = 0,
      stride = 1;
  std::vector<GridSpan> columns;
};
struct GridEditOptions {
  bool enabled = false, start_typing = false, allow_null = false;
  std::function<std::optional<GridValue>(const GridRecord &,
                                         const GridColumn &)>
      prepare;
};
struct GridChange {
  std::string row_id, column_id;
  GridValue value;
};
struct GridPasteRequest {
  std::uint64_t id = 0, revision = 0;
  std::vector<GridChange> changes;
};
struct GridEvent {
  std::string kind, row_id, column_id, text;
  std::uint64_t id = 0, revision = 0;
  GridValue value;
  GridEvent(std::string kind = "", std::string row_id = "",
            std::string column_id = "", std::string text = "",
            std::uint64_t id = 0, std::uint64_t revision = 0,
            GridValue value = {})
      : kind(std::move(kind)), row_id(std::move(row_id)),
        column_id(std::move(column_id)), text(std::move(text)), id(id),
        revision(revision), value(std::move(value)) {}
};
struct GridEditSession {
  std::uint64_t id = 0, revision = 0;
  std::string row_id, column_id;
  GridValue original;
  Text buffer;
  bool null = false, pending = false;
  std::string error, move;
};
struct GridViewState {
  std::vector<GridColumn> columns;
  std::map<std::string, GridColumnOptions> column_options;
  std::string row_id, column_id, top_row_id, left_column_id, sort_column,
      sort_direction;
  std::optional<GridRange> selection;
  std::string mode = "cell", filter;
};
namespace grid_detail {
inline void number(std::int64_t n, std::int64_t lo, std::int64_t hi,
                   const char *name) {
  if (n < lo || n > hi)
    throw std::invalid_argument(name);
}
inline State combine(State a, State b) {
  return {a.disabled || b.disabled, a.read_only || b.read_only,
          a.busy || b.busy,         a.selected || b.selected,
          a.edited || b.edited,     a.invalid || b.invalid};
}
inline std::string raw(const GridRecord &r, const std::string &id) {
  auto p = r.cells.find(id);
  return p != r.cells.end() && p->second ? *p->second : "";
}
inline bool is_null(const GridRecord &r, const std::string &id) {
  auto p = r.cells.find(id);
  return p != r.cells.end() && !p->second;
}
inline std::string fit(const std::string &s, int width,
                       const std::string &align = "left",
                       bool ellipsis = false) {
  auto t = clip(s, width, ellipsis);
  int space = std::max(0, width - cells(t));
  return align == "right"    ? std::string(space, ' ') + t
         : align == "center" ? std::string(space / 2, ' ') + t +
                                   std::string(space - space / 2, ' ')
                             : t + std::string(space, ' ');
}
inline std::tuple<std::string, int, int, std::size_t>
window(const std::string &value, std::size_t cursor, int width) {
  auto gs = graphemes(value);
  auto at = std::min(cursor, gs.size()), start = at;
  int x = 0,
      reserve = std::min(
          width, std::max(1, at < gs.size() ? cells(clean(gs[at].text)) : 1));
  while (start) {
    int w = cells(clean(gs[start - 1].text));
    if (x + w > width - reserve)
      break;
    --start;
    x += w;
  }
  std::string text;
  int used = 0;
  for (auto i = start; i < gs.size(); i++) {
    auto g = clean(gs[i].text);
    int w = cells(g);
    if (used + w > width)
      break;
    text += g;
    used += w;
  }
  int glyph = std::max(1, at < gs.size() ? cells(clean(gs[at].text)) : 1);
  return {text, x, glyph > width ? 1 : glyph, start};
}
} // namespace grid_detail
inline std::vector<std::vector<std::string>>
parse_grid_tsv(const std::string &text, int max_cells = 10000) {
  grid_detail::number(max_cells, 1, 1000000, "invalid cell limit");
  dialog_detail::text(text, 16 * 1024 * 1024);
  std::vector<std::vector<std::string>> rows;
  std::vector<std::string> row;
  std::string value;
  bool quoted = false, closed = false, started = false;
  int count = 0;
  auto finish = [&] {
    if (++count > max_cells)
      throw std::invalid_argument("paste exceeds cell limit");
    row.push_back(value);
    value.clear();
    closed = started = false;
  };
  for (std::size_t i = 0; i < text.size(); i++) {
    char c = text[i];
    if (quoted) {
      if (c == '"') {
        if (i + 1 < text.size() && text[i + 1] == '"') {
          value += '"';
          ++i;
          continue;
        }
        quoted = false;
        closed = true;
      } else
        value += c;
      continue;
    }
    bool nl =
        c == '\n' || (c == '\r' && i + 1 < text.size() && text[i + 1] == '\n');
    if (c == '\t' || nl) {
      if (c == '\t' || !row.empty() || started || closed || !value.empty())
        finish();
      if (nl) {
        if (!row.empty()) {
          rows.push_back(row);
          row.clear();
        }
        if (c == '\r')
          ++i;
      }
    } else if (closed)
      throw std::invalid_argument("characters after closing quote");
    else if (c == '"') {
      if (started || !value.empty())
        throw std::invalid_argument("quote inside unquoted field");
      quoted = started = true;
    } else {
      value += c;
      started = true;
    }
  }
  if (quoted)
    throw std::invalid_argument("unterminated quoted field");
  if (!row.empty() || started || closed || !value.empty()) {
    finish();
    rows.push_back(row);
  }
  if (rows.empty())
    throw std::invalid_argument("empty paste");
  for (const auto &r : rows)
    if (r.size() != rows.front().size())
      throw std::invalid_argument("ragged paste");
  return rows;
}
inline std::string
format_grid_tsv(const std::vector<std::vector<std::string>> &rows) {
  std::string out;
  for (std::size_t i = 0; i < rows.size(); i++) {
    if (i)
      out += '\n';
    for (std::size_t j = 0; j < rows[i].size(); j++) {
      if (j)
        out += '\t';
      const auto &s = rows[i][j];
      if (s.empty() || s.find_first_of("\t\n\r\"") != std::string::npos) {
        out += '"';
        for (char c : s) {
          out += c;
          if (c == '"')
            out += '"';
        }
        out += '"';
      } else
        out += s;
    }
  }
  return out;
}
class Grid {
  std::shared_ptr<const GridSource> source_;
  GridOptions options_;
  GridLabels labels_;
  GridEditOptions edit_options_;
  std::map<std::string, GridColumnOptions> column_options_;
  std::map<std::string, int> cell_pan_;
  std::function<GridCellInfo(const GridRecord &, const GridColumn &)>
      cell_info_;
  std::optional<GridPasteRequest> paste_;
  std::uint64_t serial_ = 0, revision_ = 0, applied_revision_ = 0;
  mutable bool callback_ = false;
  struct Hits {
    int width, height;
    GridGeometry geometry;
    std::map<std::size_t, std::string> rows;
    std::vector<std::string> signature;
  };
  std::optional<Hits> hits_;
  struct GridCapture {
    std::string kind, column, anchor_row, anchor_column;
    int width = 0, height = 0, start_x = 0, start_width = 0;
    std::uint64_t revision = 0, edit_id = 0;
    std::optional<std::size_t> anchor_index;
    std::vector<std::string> signature;
    bool moved = false, whole = false;
  };
  std::optional<GridCapture> capture_;
  std::string paint_key_;

  void mutation() const {
    if (callback_)
      throw std::invalid_argument("grid mutation inside callback");
  }
  template <class F>
  auto invoke(F f, const GridRecord &r, const GridColumn &c) const
      -> decltype(f(r, c)) {
    if (callback_)
      throw std::invalid_argument("recursive grid callback");
    callback_ = true;
    try {
      auto value = f(r, c);
      callback_ = false;
      return value;
    } catch (...) {
      callback_ = false;
      throw;
    }
  }
  template <class F> auto source_call(F fn) const -> decltype(fn()) {
    if (callback_)
      throw std::invalid_argument("recursive grid source callback");
    callback_ = true;
    try {
      auto value = fn();
      callback_ = false;
      return value;
    } catch (...) {
      callback_ = false;
      throw;
    }
  }
  std::size_t source_size() const {
    auto n = source_call([&] { return source_->size(); });
    if (n > 1000000000)
      throw std::invalid_argument("invalid row count");
    return n;
  }
  std::optional<std::size_t> source_index(const std::string &id) const {
    auto i = source_call([&] { return source_->index_of(id); });
    if (i && *i >= source_size())
      throw std::invalid_argument("invalid source index");
    return i;
  }
  GridRecord record(std::size_t i) const {
    if (i >= source_size())
      throw std::invalid_argument("row outside source");
    auto r = source_call([&] { return source_->row(i); });
    if (r.id.empty() || source_index(r.id) != std::optional<std::size_t>(i))
      throw std::invalid_argument("inconsistent grid source IDs");
    return r;
  }
  void invalidate() {
    mutation();
    ++revision_;
    edit.reset();
    paste_.reset();
    hits_.reset();
    capture_.reset();
  }
  std::optional<std::pair<GridRecord, GridColumn>> current() {
    auto cs = visible_columns();
    if (cs.empty() || !source_size())
      return std::nullopt;
    row = std::min(row, source_size() - 1);
    column = std::min(column, cs.size() - 1);
    auto r = record(row);
    if (r.state.disabled) {
      bool found = false;
      int scanned = 0;
      for (auto i = row + 1; i < source_size() && scanned < 100000;
           i++, scanned++) {
        r = record(i);
        if (!r.state.disabled) {
          row = i;
          found = true;
          break;
        }
      }
      if (!found)
        for (auto i = row; i > 0 && scanned < 100000; scanned++) {
          --i;
          r = record(i);
          if (!r.state.disabled) {
            row = i;
            found = true;
            break;
          }
        }
      if (!found)
        return std::nullopt;
    }
    return std::make_pair(r, cs[column]);
  }
  GridCellInfo info(const GridRecord &r, const GridColumn &c) const {
    auto result = cell_info_ ? invoke(cell_info_, r, c) : GridCellInfo{};
    auto p = r.cell_states.find(c.id);
    result.state = grid_detail::combine(result.state, r.state);
    if (p != r.cell_states.end())
      result.state = grid_detail::combine(result.state, p->second);
    result.null = result.null || grid_detail::is_null(r, c.id);
    return result;
  }
  std::optional<GridValue> prepared(const GridRecord &r,
                                    const GridColumn &c) const {
    auto value = edit_options_.prepare
                     ? invoke(edit_options_.prepare, r, c)
                     : std::optional<GridValue>(GridValue{
                           grid_detail::raw(r, c.id), info(r, c).null});
    if (value)
      dialog_detail::text(value->text, 16 * 1024 * 1024);
    return value;
  }
  bool editable(const GridRecord &r, const GridColumn &c) const {
    return !options_.disable_editing && !c.hidden && c.editable &&
           info(r, c).state.editable() && prepared(r, c).has_value();
  }
  bool work_valid(const std::string &rid, const std::string &cid,
                  std::uint64_t revision) const {
    if (revision != revision_)
      return false;
    auto i = source_index(rid);
    auto cs = visible_columns();
    auto c = std::find_if(cs.begin(), cs.end(),
                          [&](const auto &c) { return c.id == cid; });
    if (!i || *i >= source_size() || c == cs.end())
      return false;
    auto r = record(*i);
    return r.id == rid && editable(r, *c);
  }
  std::optional<std::array<std::size_t, 4>> selection_bounds() const {
    auto cs = visible_columns();
    if (cs.empty() || !source_size())
      return std::nullopt;
    if (selected) {
      auto a = source_index(selected->anchor_row),
           b = source_index(selected->end_row);
      auto c = std::find_if(
               cs.begin(), cs.end(),
               [&](const auto &c) { return c.id == selected->anchor_column; }),
           d = std::find_if(cs.begin(), cs.end(), [&](const auto &c) {
             return c.id == selected->end_column;
           });
      if (!a || !b || c == cs.end() || d == cs.end())
        return std::nullopt;
      auto ci = std::size_t(c - cs.begin()), di = std::size_t(d - cs.begin());
      return std::array<std::size_t, 4>{std::min(*a, *b), std::min(ci, di),
                                        std::max(*a, *b), std::max(ci, di)};
    }
    return std::array<std::size_t, 4>{
        row, options_.selection == "row" ? 0 : column, row,
        options_.selection == "row" ? cs.size() - 1 : column};
  }
  bool move_editable(bool previous) {
    auto cs = visible_columns();
    if (cs.empty())
      return false;
    std::int64_t start = std::int64_t(row * cs.size() + column),
                 n = std::int64_t(source_size() * cs.size()),
                 step = previous ? -1 : 1;
    for (std::int64_t at = start + step, scanned = 0;
         at >= 0 && at < n && scanned < 100000; at += step, scanned++) {
      auto i = std::size_t(at) / cs.size(), j = std::size_t(at) % cs.size();
      auto r = record(i);
      if (editable(r, cs[j]))
        return focus(r.id, cs[j].id);
    }
    return false;
  }

public:
  std::vector<GridColumn> columns;
  std::size_t row = 0, column = 0, top = 0;
  int left = 0;
  std::optional<GridEditSession> edit;
  std::optional<GridRange> selected;
  bool case_sensitive = false, use_display = false;
  std::string query, sort_column, sort_direction;
  GridDataStatus status;
  Grid(std::vector<GridColumn> columns,
       std::shared_ptr<const GridSource> source)
      : source_(std::move(source)), columns(std::move(columns)) {
    if (!source_ || source_size() > 1000000000)
      throw std::invalid_argument("invalid grid source");
    if (this->columns.size() > 65536)
      throw std::invalid_argument("too many grid columns");
    std::set<std::string> ids;
    for (const auto &c : this->columns) {
      if (c.id.empty() || !ids.insert(c.id).second ||
          (c.pin != "" && c.pin != "left" && c.pin != "right"))
        throw std::invalid_argument("invalid grid column");
      dialog_detail::text(c.id, 1000000);
      dialog_detail::text(c.label, 1000000);
      grid_detail::number(c.width, 1, 4096, "invalid column width");
    }
  }
  Grid(std::vector<GridColumn> columns, std::vector<GridRecord> rows)
      : Grid(std::move(columns),
             std::make_shared<MemoryRows>(std::move(rows))) {}
  std::vector<GridColumn> visible_columns() const {
    auto cs = columns;
    cs.erase(std::remove_if(cs.begin(), cs.end(),
                            [](const auto &c) { return c.hidden; }),
             cs.end());
    auto rank = [](const auto &c) {
      return c.pin == "left" ? 0 : c.pin == "right" ? 2 : 1;
    };
    std::stable_sort(cs.begin(), cs.end(), [&](const auto &a, const auto &b) {
      return rank(a) < rank(b);
    });
    return cs;
  }
  std::string row_id() {
    auto p = current();
    return p ? p->first.id : "";
  }
  std::string column_id() {
    auto p = current();
    return p ? p->second.id : "";
  }
  std::uint64_t revision() const { return revision_; }
  GridLabels labels() const { return labels_; }
  void set_labels(GridLabels labels) {
    mutation();
    for (const auto &s : {labels.null_text, labels.loading, labels.empty,
                          labels.range, labels.more})
      dialog_detail::text(s, 1000000);
    labels_ = std::move(labels);
  }
  GridOptions options() const { return options_; }
  std::optional<GridPasteRequest> pending_paste() const { return paste_; }

private:
  struct PreparedSource {
    std::shared_ptr<const GridSource> source;
    std::size_t row;
    std::optional<GridRange> selected;
  };
  PreparedSource prepare_source(std::shared_ptr<const GridSource> source) {
    mutation();
    auto id = row_id();
    auto range = selected;
    return source_call([&] {
      Grid probe(columns, source);
      auto i = probe.source_index(id);
      if (i && probe.record(*i).id != id)
        throw std::invalid_argument("inconsistent grid source IDs");
      if (range) {
        auto cs = probe.visible_columns();
        bool valid = true;
        const std::pair<std::string, std::string> endpoints[] = {
            {range->anchor_row, range->anchor_column},
            {range->end_row, range->end_column}};
        for (const auto &pair : endpoints) {
          auto at = probe.source_index(pair.first);
          if (!at || std::none_of(cs.begin(), cs.end(),
                                  [&](auto c) { return c.id == pair.second; }))
            valid = false;
          else if (probe.record(*at).id != pair.first)
            throw std::invalid_argument("inconsistent grid source IDs");
        }
        if (!valid)
          range.reset();
      }
      return PreparedSource{std::move(source), i.value_or(0), range};
    });
  }
  void install_source(PreparedSource prepared) {
    source_ = std::move(prepared.source);
    row = prepared.row;
    selected = std::move(prepared.selected);
    invalidate();
  }

public:
  void set_source(std::shared_ptr<const GridSource> source) {
    install_source(prepare_source(std::move(source)));
  }
  void set_rows(std::vector<GridRecord> rows) {
    set_source(std::make_shared<MemoryRows>(std::move(rows)));
  }
  bool focus(const std::string &rid, const std::string &cid) {
    mutation();
    auto i = source_index(rid);
    auto cs = visible_columns();
    auto j = std::find_if(cs.begin(), cs.end(),
                          [&](const auto &c) { return c.id == cid; });
    if (!i || *i >= source_size() || j == cs.end())
      return false;
    auto r = record(*i);
    if (r.id != rid || r.state.disabled)
      return false;
    if (edit && (rid != edit->row_id || cid != edit->column_id))
      edit.reset();
    row = *i;
    column = j - cs.begin();
    return true;
  }
  void set_options(GridOptions o) {
    grid_detail::number(o.padding, 0, 8, "invalid padding");
    grid_detail::number(o.row_spacing, 0, 4, "invalid row spacing");
    grid_detail::number(o.gutter_width, 0, 128, "invalid gutter width");
    grid_detail::number(o.max_copy_cells, 1, 1000000, "invalid copy limit");
    const std::set<std::string> allowed{"position", "column", "selection",
                                        "sort",     "filter", "loading",
                                        "more",     "meta",   "error"};
    std::set<std::string> seen;
    if (o.selection != "cell" && o.selection != "row" && o.selection != "range")
      throw std::invalid_argument("invalid grid selection mode");
    for (const auto &f : o.status_fields)
      if (!allowed.count(f) || !seen.insert(f).second)
        throw std::invalid_argument("invalid grid status field");
    invalidate();
    options_ = std::move(o);
  }
  void set_edit_options(GridEditOptions options) {
    invalidate();
    edit_options_ = std::move(options);
  }
  void set_cell_info(
      std::function<GridCellInfo(const GridRecord &, const GridColumn &)> fn) {
    invalidate();
    cell_info_ = std::move(fn);
  }
  void set_column_options(const std::string &id, GridColumnOptions o) {
    auto c = std::find_if(columns.begin(), columns.end(),
                          [&](const auto &c) { return c.id == id; });
    if (c == columns.end())
      throw std::invalid_argument("unknown column");
    grid_detail::number(o.min_width, 1, 4096, "invalid minimum width");
    grid_detail::number(o.max_width, o.min_width, 4096,
                        "invalid maximum width");
    grid_detail::number(o.expand, 0, 4096, "invalid expansion");
    if ((o.align != "left" && o.align != "right" && o.align != "center" &&
         o.align != "auto") ||
        (o.overflow != "clip" && o.overflow != "ellipsis" &&
         o.overflow != "scroll"))
      throw std::invalid_argument("invalid column options");
    invalidate();
    column_options_[id] = o;
    c->width = std::clamp(c->width, o.min_width, o.max_width);
  }
  void set_column_layout(const std::vector<GridColumn> &layout) {
    if (layout.size() != columns.size())
      throw std::invalid_argument("incompatible column layout");
    std::vector<GridColumn> next;
    std::set<std::string> seen;
    for (const auto &item : layout) {
      auto p = std::find_if(columns.begin(), columns.end(),
                            [&](const auto &c) { return c.id == item.id; });
      if (p == columns.end() || !seen.insert(item.id).second ||
          (item.pin != "" && item.pin != "left" && item.pin != "right"))
        throw std::invalid_argument("invalid column layout");
      auto c = *p;
      c.pin = item.pin;
      c.hidden = item.hidden;
      next.push_back(c);
    }
    auto p = current();
    invalidate();
    columns = std::move(next);
    if (p)
      focus(p->first.id, p->second.id);
  }
  bool begin_edit(std::optional<std::string> first = std::nullopt) {
    mutation();
    auto p = current();
    if (!p || edit || paste_ || !edit_options_.enabled ||
        !editable(p->first, p->second))
      return false;
    auto v = prepared(p->first, p->second);
    if (!v)
      return false;
    GridEditSession e;
    e.id = ++serial_;
    e.revision = revision_;
    e.row_id = p->first.id;
    e.column_id = p->second.id;
    e.original = *v;
    e.null = first ? false : v->null;
    e.buffer = Text(first ? *first : v->text);
    e.buffer.multiline = false;
    edit = std::move(e);
    hits_.reset();
    return true;
  }
  bool resolve_edit(std::uint64_t id, const std::string &error = "",
                    std::shared_ptr<const GridSource> source = nullptr) {
    mutation();
    if (!edit || !edit->pending || edit->id != id ||
        edit->revision != revision_)
      return false;
    if (!work_valid(edit->row_id, edit->column_id, edit->revision)) {
      edit.reset();
      return false;
    }
    if (!error.empty()) {
      edit->pending = false;
      edit->error = error;
      return true;
    }
    auto e = *edit;
    std::optional<PreparedSource> prepared;
    if (source)
      prepared = prepare_source(std::move(source));
    edit.reset();
    if (prepared)
      install_source(std::move(*prepared));
    focus(e.row_id, e.column_id);
    if (!e.move.empty() && move_editable(e.move == "previous"))
      begin_edit();
    return true;
  }
  GridEvent handle(const std::string &action, int height = 10,
                   const std::string &text = "") {
    mutation();
    grid_detail::number(height, 0, 4096, "invalid height");
    if (options_.disable_keyboard)
      return {};
    capture_.reset();
    if (!edit && (action == "select_up" || action == "select_down" ||
                  action == "select_left" || action == "select_right" ||
                  action == "select_home" || action == "select_end" ||
                  action == "select_page_up" || action == "select_page_down"))
      return extend_navigation(action.substr(7), height);
    if (edit) {
      auto &e = *edit;
      if (action == "cancel") {
        auto id = e.row_id;
        edit.reset();
        return {"edit_cancel", id};
      }
      if (!work_valid(e.row_id, e.column_id, e.revision)) {
        edit.reset();
        return {"edit_stale"};
      }
      if (e.pending)
        return {};
      if (action == "null") {
        if (!edit_options_.allow_null)
          return {};
        e.null = !e.null;
        e.error.clear();
      } else if (action == "submit" || action == "activate" ||
                 action == "next" || action == "previous") {
        e.id = ++serial_;
        e.pending = true;
        e.error.clear();
        e.move = action == "next" || action == "previous" ? action : "";
        return {"edit_submit",
                e.row_id,
                e.column_id,
                "",
                e.id,
                e.revision,
                {e.buffer.value, e.null}};
      } else {
        if (action == "insert" || action == "paste" || action == "backspace" ||
            action == "delete") {
          e.null = false;
          e.error.clear();
        }
        auto out = !e.null ? e.buffer.handle(action, text) : Event{};
        if (out.kind == "copy" || out.kind == "cut")
          return {out.kind, e.row_id, e.column_id, out.text};
      }
      return {"edit_change", e.row_id, e.column_id};
    }
    auto p = current();
    if (!p)
      return {};
    auto r = p->first;
    auto c = p->second;
    if (action == "activate" || action == "edit")
      return {begin_edit() ? "edit_begin" : "edit_denied", r.id, c.id};
    if (action == "insert" && !text.empty() && edit_options_.start_typing)
      return {begin_edit(text) ? "edit_begin" : "edit_denied", r.id, c.id};
    if (action == "copy")
      return copy_selection();
    if (action == "details")
      return info(r, c).state.disabled
                 ? GridEvent{}
                 : GridEvent{"details", r.id, c.id, grid_detail::raw(r, c.id)};
    if (action == "sort" || action == "filter" || action == "search" ||
        action == "page_next" || action == "page_previous")
      return request(action == "page_next"       ? "next"
                     : action == "page_previous" ? "previous"
                                                 : action,
                     text);
    std::map<std::string, std::int64_t> moves{
        {"up", std::int64_t(row) - 1},
        {"down", std::int64_t(row) + 1},
        {"home", 0},
        {"end", std::int64_t(source_size()) - 1},
        {"page_up", std::int64_t(row) - std::max(1, height - 1)},
        {"page_down", std::int64_t(row) + std::max(1, height - 1)}};
    if (moves.count(action)) {
      int direction =
          action == "up" || action == "home" || action == "page_up" ? -1 : 1;
      auto at =
          std::clamp<std::int64_t>(moves.at(action), 0, source_size() - 1);
      while (at >= 0 && at < std::int64_t(source_size())) {
        if (!record(at).state.disabled) {
          row = at;
          break;
        }
        at += direction;
      }
    } else if (action == "left" || action == "right")
      column = std::clamp<std::int64_t>(std::int64_t(column) +
                                            (action == "left" ? -1 : 1),
                                        0, visible_columns().size() - 1);
    else if (action != "select")
      return {};
    p = current();
    return p ? GridEvent{"select", p->first.id, p->second.id} : GridEvent{};
  }
  std::optional<GridPasteRequest>
  request_paste(const std::string &text, int max_cells = 10000,
                std::optional<std::string> null_text = std::nullopt) {
    mutation();
    if (edit || paste_)
      return std::nullopt;
    std::vector<std::vector<std::string>> values;
    try {
      values = parse_grid_tsv(text, max_cells);
    } catch (const std::invalid_argument &) {
      return std::nullopt;
    }
    auto cs = visible_columns();
    if (cs.empty() || row + values.size() > source_size() ||
        column + values[0].size() > cs.size())
      return std::nullopt;
    GridPasteRequest request;
    for (std::size_t dy = 0; dy < values.size(); dy++) {
      auto r = record(row + dy);
      for (std::size_t dx = 0; dx < values[dy].size(); dx++) {
        auto c = cs[column + dx];
        auto value = values[dy][dx];
        if (!editable(r, c))
          return std::nullopt;
        request.changes.push_back(
            {r.id, c.id, {value, null_text && value == *null_text}});
      }
    }
    request.id = ++serial_;
    request.revision = revision_;
    paste_ = request;
    return request;
  }
  bool resolve_paste(std::uint64_t id,
                     std::shared_ptr<const GridSource> source = nullptr) {
    mutation();
    if (!paste_ || paste_->id != id || paste_->revision != revision_)
      return false;
    for (const auto &c : paste_->changes)
      if (!work_valid(c.row_id, c.column_id, paste_->revision)) {
        paste_.reset();
        return false;
      }
    std::optional<PreparedSource> prepared;
    if (source)
      prepared = prepare_source(std::move(source));
    paste_.reset();
    if (prepared)
      install_source(std::move(*prepared));
    return true;
  }
  void cancel_paste() {
    mutation();
    paste_.reset();
  }
  bool find(const std::string &value, bool previous = false,
            int max_cells = 100000) {
    mutation();
    grid_detail::number(max_cells, 1, 1000000, "invalid find limit");
    auto cs = visible_columns();
    std::size_t total = cs.size() * source_size();
    if (value.empty() || !total || edit || paste_)
      return false;
    query = value;
    auto needle = case_sensitive ? value : fold(value);
    auto start = row * cs.size() + column;
    for (std::size_t step = 1; step <= std::min<std::size_t>(total, max_cells);
         step++) {
      auto pos =
          previous ? (start + total - step) % total : (start + step) % total;
      auto i = pos / cs.size(), j = pos % cs.size();
      auto r = record(i);
      auto inf = info(r, cs[j]);
      if (inf.state.disabled)
        continue;
      auto text = use_display && inf.has_display ? inf.display
                  : use_display && inf.null ? labels_.null_text
                                            : grid_detail::raw(r, cs[j].id);
      if ((case_sensitive ? text : fold(text)).find(needle) !=
          std::string::npos) {
        row = i;
        column = j;
        return true;
      }
    }
    return false;
  }
  GridEvent request(const std::string &kind, const std::string &text = "") {
    mutation();
    if (kind != "sort" && kind != "filter" && kind != "search" &&
        kind != "next" && kind != "previous")
      throw std::invalid_argument("unknown grid request");
    if (kind == "sort" && options_.disable_header_sort)
      return {};
    auto p = current();
    invalidate();
    return {
        kind + "_request", p ? p->first.id : "", p ? p->second.id : "", text, 0,
        revision_};
  }
  bool apply_source(std::uint64_t revision,
                    std::shared_ptr<const GridSource> source) {
    if (revision != revision_ || revision <= applied_revision_)
      return false;
    set_source(std::move(source));
    applied_revision_ = revision;
    return true;
  }
  void set_selection(std::optional<GridRange> selection) {
    mutation();
    if (!selection) {
      selected.reset();
      return;
    }
    auto cs = visible_columns();
    for (const auto &pair : std::vector<std::pair<std::string, std::string>>{
             {selection->anchor_row, selection->anchor_column},
             {selection->end_row, selection->end_column}}) {
      auto i = source_index(pair.first);
      if (!i || *i >= source_size() || record(*i).id != pair.first ||
          std::none_of(cs.begin(), cs.end(),
                       [&](const auto &c) { return c.id == pair.second; }))
        throw std::invalid_argument("unknown range ID");
    }
    selected = std::move(selection);
  }
  GridEvent copy_selection(bool display = false,
                           const std::string &null_text = "NULL") const {
    if (options_.disable_copy)
      return {};
    auto bounds = selection_bounds();
    if (!bounds)
      return {};
    auto a = (*bounds)[0], b = (*bounds)[1], c = (*bounds)[2], d = (*bounds)[3];
    auto cs = visible_columns();
    if (c >= source_size() || d >= cs.size() ||
        (c - a + 1) * (d - b + 1) > std::size_t(options_.max_copy_cells))
      return {"copy_rejected"};
    std::vector<std::vector<std::string>> values;
    std::size_t bytes = 0;
    for (auto i = a; i <= c; i++) {
      auto r = record(i);
      std::vector<std::string> line;
      for (auto j = b; j <= d; j++) {
        auto inf = info(r, cs[j]);
        if (inf.state.disabled)
          return {"copy_rejected"};
        auto value = display && inf.has_display ? inf.display
                     : inf.null                 ? null_text
                                                : grid_detail::raw(r, cs[j].id);
        bytes += value.size();
        if (bytes > 16 * 1024 * 1024)
          return {"copy_rejected"};
        line.push_back(std::move(value));
      }
      values.push_back(std::move(line));
    }
    return {"copy", "", "", format_grid_tsv(values)};
  }
  bool resize_column(const std::string &id, int width) {
    if (options_.disable_resize)
      return false;
    auto c = std::find_if(columns.begin(), columns.end(),
                          [&](const auto &c) { return c.id == id; });
    if (c == columns.end())
      return false;
    grid_detail::number(width, 1, 4096, "invalid column width");
    auto co = column_options_.count(id) ? column_options_.at(id)
                                        : GridColumnOptions{};
    invalidate();
    c->width = std::clamp(width, co.min_width, co.max_width);
    return true;
  }
  bool auto_fit_column(const std::string &id, int height = 20) {
    grid_detail::number(height, 0, 4096, "invalid height");
    auto c = std::find_if(columns.begin(), columns.end(),
                          [&](const auto &c) { return c.id == id; });
    if (c == columns.end() || options_.disable_resize)
      return false;
    int w = cells(c->label.empty() ? c->id : c->label);
    for (auto i = top; i < std::min(source_size(), top + height); i++) {
      auto r = record(i);
      auto inf = info(r, *c);
      w = std::max(
          w, cells(inf.has_display ? inf.display
                   : inf.null      ? labels_.null_text
                                   : grid_detail::raw(r, id)) +
                 (inf.state.edited && options_.show_cell_markers ? 2 : 0));
    }
    return resize_column(id, std::clamp(w + 2 * options_.padding, 1, 4096));
  }
  void pan_cell(const std::string &id, int offset) {
    mutation();
    grid_detail::number(offset, 0, 1000000, "invalid cell pan");
    if (std::none_of(columns.begin(), columns.end(),
                     [&](const auto &c) { return c.id == id; }))
      throw std::invalid_argument("unknown column");
    cell_pan_[id] = offset;
  }
  GridGeometry geometry(int width, int height) {
    grid_detail::number(width, 0, 65535, "invalid width");
    grid_detail::number(height, 0, 4096, "invalid height");
    grid_detail::number(top, 0, 1000000000, "invalid top row");
    grid_detail::number(left, 0, 1000000, "invalid left column");
    GridGeometry g;
    g.header_rows = !options_.hide_header && height > 0;
    g.footer_rows = options_.status_bar && height > g.header_rows;
    g.stride = 1 + options_.row_spacing + int(options_.horizontal_lines);
    g.body_rows =
        (std::max(0, height - g.header_rows - g.footer_rows) + g.stride - 1) /
        g.stride;
    auto p = current();
    if (p && g.body_rows) {
      top = std::min(top, row);
      if (row >= top + g.body_rows)
        top = row - g.body_rows + 1;
    }
    g.top = top;
    g.gutter =
        std::min(width, std::max(options_.gutter_width,
                                 options_.row_numbers
                                     ? int(std::to_string(std::max<std::size_t>(
                                                              1, source_size()))
                                               .size()) +
                                           1
                                     : 0));
    auto cs = visible_columns();
    bool automatic = std::any_of(cs.begin(), cs.end(), [&](const auto &c) {
      auto co = column_options_.find(c.id);
      return co != column_options_.end() && co->second.auto_fit;
    });
    if (automatic) {
      std::vector<GridRecord> records;
      for (auto i = top;
           i < std::min(source_size(),
                        top + std::size_t(std::min(g.body_rows, 256)));
           i++)
        records.push_back(record(i));
      int sampled = 0;
      for (auto &c : cs) {
        auto it = column_options_.find(c.id);
        if (it == column_options_.end() || !it->second.auto_fit)
          continue;
        auto co = it->second;
        int w = cells(c.label.empty() ? c.id : c.label) + 2 * options_.padding;
        for (const auto &r : records) {
          if (sampled >= 100000)
            break;
          ++sampled;
          auto inf = info(r, c);
          auto value = inf.has_display ? inf.display
                       : inf.null      ? labels_.null_text
                                       : grid_detail::raw(r, c.id);
          w = std::max(
              w, cells(value) + 2 * options_.padding +
                     (inf.state.edited && options_.show_cell_markers ? 2 : 0));
        }
        c.width = std::clamp(w, co.min_width, co.max_width);
      }
    }

    int sep = options_.vertical_lines;
    std::vector<GridColumn> pins_left, pins_right, normal;
    for (auto c : cs)
      (c.pin == "left"    ? pins_left
       : c.pin == "right" ? pins_right
                          : normal)
          .push_back(c);
    left = std::min(left, std::max(0, int(normal.size()) - 1));
    auto sum = [&](const std::vector<GridColumn> &cols) {
      int n = 0;
      for (auto c : cols)
        n += c.width + sep;
      return n;
    };
    if (p) {
      auto ci = std::find_if(normal.begin(), normal.end(), [&](const auto &c) {
        return c.id == p->second.id;
      });
      if (ci != normal.end()) {
        int at = ci - normal.begin(),
            capacity = std::max(0, width - g.gutter - sum(pins_left) -
                                       sum(pins_right));
        left = std::min(left, at);
        while (left < at) {
          int need = 0;
          for (int i = left; i <= at; i++)
            need += normal[i].width + sep;
          if (need <= capacity)
            break;
          ++left;
        }
      }
    }
    g.left = left;
    int end = width - std::min(std::max(0, width - g.gutter), sum(pins_right)),
        x = g.gutter;
    std::vector<GridColumn> scrolling = pins_left;
    scrolling.insert(scrolling.end(), normal.begin() + left, normal.end());
    for (auto c : scrolling) {
      int w = std::min(c.width, std::max(0, end - x));
      if (w)
        g.columns.push_back({c.id, x, w});
      x += w + sep;
      if (x >= end)
        break;
    }
    x = std::max(g.gutter, end);
    for (auto c : pins_right) {
      int w = std::min(c.width, std::max(0, width - x));
      if (w)
        g.columns.push_back({c.id, x, w});
      x += w + sep;
      if (x >= width)
        break;
    }
    int used = g.gutter, total = 0;
    for (auto s : g.columns)
      if (s.x < end) {
        used = std::max(used, s.x + s.width + sep);
        auto it = column_options_.find(s.id);
        if (it != column_options_.end())
          total += it->second.expand;
      }
    int room = std::max(0, end - used), remaining = room, shift = 0;
    if (room && total)
      for (auto &s : g.columns)
        if (s.x < end) {
          auto co = column_options_.count(s.id) ? column_options_.at(s.id)
                                                : GridColumnOptions{};
          int extra = std::min(
              {remaining, co.max_width - s.width, room * co.expand / total});
          s.x += shift;
          s.width += extra;
          shift += extra;
          remaining -= extra;
        }
    return g;
  }
  std::optional<std::array<int, 3>> edit_cursor(int width, int height) {
    if (!edit || edit->pending || edit->null ||
        !work_valid(edit->row_id, edit->column_id, edit->revision))
      return std::nullopt;
    auto g = geometry(width, height);
    auto i = source_index(edit->row_id);
    auto span = std::find_if(g.columns.begin(), g.columns.end(),
                             [&](auto s) { return s.id == edit->column_id; });
    if (!i || span == g.columns.end() || *i < g.top ||
        *i >= g.top + g.body_rows)
      return std::nullopt;
    auto c = std::find_if(columns.begin(), columns.end(),
                          [&](auto c) { return c.id == span->id; });
    auto inf = info(record(*i), *c);
    int extra = inf.state.edited && options_.show_cell_markers ? 2 : 0,
        room = span->width - 2 * options_.padding - extra,
        y = g.header_rows + int(*i - g.top) * g.stride;
    if (room <= 0 || y >= height - g.footer_rows)
      return std::nullopt;
    auto [text, x, glyph, start] =
        grid_detail::window(edit->buffer.value, edit->buffer.cursor, room);
    (void)text;
    (void)start;
    return std::array<int, 3>{span->x + options_.padding + extra + x, y, glyph};
  }
  std::optional<TextDocument> details() {
    auto p = current();
    if (!p || info(p->first, p->second).state.disabled)
      return std::nullopt;
    return TextDocument::viewer(grid_detail::raw(p->first, p->second.id));
  }
  std::string status_text() {
    auto p = current();
    if (status.total_rows > 1000000000)
      throw std::invalid_argument("invalid total rows");
    std::map<std::string, std::string> fields{
        {"position", std::to_string(p ? row + 1 : 0) + "/" +
                         std::to_string(status.total_rows ? status.total_rows
                                                          : source_size())},
        {"column",
         p ? (p->second.label.empty() ? p->second.id : p->second.label) : ""},
        {"selection", selected ? labels_.range : ""},
        {"sort",
         sort_column + (sort_direction.empty() ? "" : " " + sort_direction)},
        {"filter", status.filter},
        {"loading", status.loading ? labels_.loading : ""},
        {"more", status.has_more ? labels_.more : ""},
        {"meta", status.metadata},
        {"error", edit && !edit->error.empty() ? edit->error : status.error}};
    if (!fields["error"].empty())
      return fields["error"];
    std::string text;
    for (auto key : options_.status_fields)
      if (!fields[key].empty()) {
        if (!text.empty())
          text += " | ";
        text += fields[key];
      }
    return text;
  }
  std::vector<std::string> column_signature() const {
    std::vector<std::string> out;
    for (const auto &c : columns) {
      out.push_back(c.id);
      out.push_back(std::to_string(c.width));
      out.push_back(c.pin);
      out.push_back(c.hidden ? "1" : "0");
      out.push_back(c.editable ? "1" : "0");
    }
    return out;
  }
  void draw(Canvas &canvas, Rect r, bool focused = true, bool ascii = false) {
    grid_detail::number(r.x, 0, 1000000000, "invalid x");
    grid_detail::number(r.y, 0, 1000000000, "invalid y");
    auto g = geometry(r.width, r.height);
    auto o = options_;
    Canvas child(r.width, r.height, canvas.palette,
                 o.use_surface ? "surface" : canvas.surface_role);
    auto current_id = column_id();
    std::map<std::size_t, std::string> hit_rows;
    auto signature = column_signature();
    auto bounds = selection_bounds();
    auto cs = visible_columns();
    auto col = [&](const std::string &id) -> const GridColumn & {
      return *std::find_if(columns.begin(), columns.end(),
                           [&](auto c) { return c.id == id; });
    };
    if (g.header_rows) {
      child.fill({0, 0, r.width, 1}, "grid.header");
      for (auto span : g.columns) {
        auto c = col(span.id);
        auto title = c.label.empty() ? c.id : c.label;
        if (sort_column == c.id)
          title += sort_direction == "desc" ? " v" : " ^";
        child.write(span.x, 0,
                    grid_detail::fit(title, span.width, "left", true),
                    "grid.header", false, span.width);
      }
    }
    for (int dy = 0; dy < g.body_rows; dy++) {
      auto i = g.top + dy;
      int y = g.header_rows + dy * g.stride;
      if (y >= r.height - g.footer_rows || i >= source_size())
        break;
      auto row_data = record(i);
      hit_rows[i] = row_data.id;
      if (g.gutter)
        child.write(0, y,
                    grid_detail::fit(o.row_numbers ? std::to_string(i + 1) : "",
                                     std::max(0, g.gutter - 1), "right") +
                        " ",
                    row_data.state.disabled ? "disabled" : "hint", false,
                    g.gutter);
      for (auto span : g.columns) {
        auto c = col(span.id);
        auto inf = info(row_data, c);
        auto state = inf.state;
        bool active = i == row && c.id == current_id;
        auto j =
            std::size_t(std::find_if(cs.begin(), cs.end(),
                                     [&](auto c) { return c.id == span.id; }) -
                        cs.begin());
        bool in_range = bounds && (*bounds)[0] <= i && i <= (*bounds)[2] &&
                        (*bounds)[1] <= j && j <= (*bounds)[3];
        bool editing =
            edit && row_data.id == edit->row_id && c.id == edit->column_id &&
            work_valid(edit->row_id, edit->column_id, edit->revision);
        std::string role =
            state.disabled                      ? "disabled"
            : state.invalid                     ? "error"
            : state.edited && o.preserve_edited ? "edited"
            : ((active && o.highlight_cell) || (o.highlight_row && i == row) ||
               (in_range && selected))
                ? "selection"
            : o.striped && i % 2 ? "surface"
                                 : "body";
        if (editing)
          role = edit->pending          ? "hint"
                 : !edit->error.empty() ? "error"
                                        : "field";
        int pad = std::min(o.padding, span.width / 2);
        std::string marker = state.edited && o.show_cell_markers ? "* " : "";
        int room = std::max(0, span.width - 2 * pad - int(marker.size()));
        std::string text;
        if (editing)
          text = edit->null
                     ? labels_.null_text
                     : std::get<0>(grid_detail::window(
                           edit->buffer.value, edit->buffer.cursor, room));
        else {
          auto value = inf.has_display ? inf.display
                       : inf.null      ? labels_.null_text
                                       : grid_detail::raw(row_data, c.id);
          auto co = column_options_.count(c.id) ? column_options_.at(c.id)
                                                : GridColumnOptions{};
          if (co.overflow == "scroll") {
            int offset = cell_pan_.count(c.id) ? cell_pan_.at(c.id) : 0,
                used = 0;
            std::string out;
            for (auto gg : graphemes(value)) {
              int n = cells(gg.text);
              if (used >= offset)
                out += gg.text;
              else if (used + n > offset)
                out += std::string(used + n - offset, ' ');
              used += n;
            }
            value = out;
          }
          text = grid_detail::fit(value, room,
                                  co.align == "auto" && inf.numeric ? "right"
                                                                    : co.align,
                                  co.overflow != "clip");
        }
        auto value = std::string(pad, ' ') + marker + text;
        value += std::string(std::max(0, span.width - cells(value)), ' ');
        child.write(span.x, y, value, role,
                    focused && active && !state.disabled, span.width);
        if (editing && edit && !edit->pending && !edit->null) {
          const auto &buf = edit->buffer;
          auto lo = std::min(buf.anchor, buf.cursor),
               hi = std::max(buf.anchor, buf.cursor);
          if (lo < hi) {
            auto start =
                std::get<3>(grid_detail::window(buf.value, buf.cursor, room));
            auto gs = graphemes(buf.value);
            int x = 0;
            for (auto i = start; i < gs.size(); i++) {
              auto glyph = clean(gs[i].text);
              int w = cells(glyph);
              if (x + w > room)
                break;
              if (lo <= i && i < hi)
                child.write(span.x + pad + int(marker.size()) + x, y, glyph,
                            "selection", false, w);
              x += w;
            }
          }
        }
      }
      if (o.horizontal_lines) {
        int yy = y + 1 + o.row_spacing;
        if (yy < r.height - g.footer_rows) {
          std::string line;
          for (int k = g.gutter; k < r.width; k++)
            line += ascii || o.ascii ? "-" : "─";
          child.write(g.gutter, yy, line, "hint", false, r.width - g.gutter);
        }
      }
    }
    if (!source_size() && g.header_rows < r.height - g.footer_rows)
      child.write(g.gutter, g.header_rows,
                  clip(!status.error.empty() ? status.error
                       : status.loading      ? labels_.loading
                                             : labels_.empty,
                       std::max(0, r.width - g.gutter)),
                  !status.error.empty() ? "error" : "hint", false,
                  r.width - g.gutter);
    if (o.vertical_lines)
      for (auto s : g.columns) {
        int x = s.x + s.width;
        if (x < r.width)
          for (int y = 0; y < r.height - g.footer_rows; y++)
            child.write(x, y, ascii || o.ascii ? "|" : "│",
                        y < g.header_rows ? "grid.header" : "hint", false, 1);
      }
    if (g.footer_rows)
      child.write(0, r.height - 1, clip(status_text(), r.width, true),
                  !status.error.empty() || (edit && !edit->error.empty())
                      ? "error"
                      : "hint",
                  false, r.width);
    if (focused) {
      auto cursor = edit_cursor(r.width, r.height);
      if (cursor)
        child.set_cursor((*cursor)[0], (*cursor)[1], (*cursor)[2]);
    }
    canvas.blit(child, {0, 0, r.width, r.height}, r.x, r.y);
    auto key = std::to_string(r.x) + "|" + std::to_string(r.y) + "|" +
               std::to_string(r.width) + "|" + std::to_string(r.height) + "|" +
               canvas.palette.theme() + "|" + canvas.palette.colors() + "|" +
               canvas.surface_role + "|" + (ascii ? "1" : "0") + "|" +
               (focused ? "1" : "0");
    if (!focused || (!paint_key_.empty() && paint_key_ != key))
      capture_.reset();
    paint_key_ = std::move(key);
    hits_ = Hits{r.width, r.height, g, hit_rows, signature};
  }
  GridEvent click(int x, int y, int width, int height) {
    mutation();
    if (options_.disable_mouse || edit || paste_ || !hits_ ||
        hits_->width != width || hits_->height != height ||
        hits_->signature != column_signature() || x < 0 || x >= width ||
        y < 0 || y >= height)
      return {};
    auto g = hits_->geometry;
    auto s = std::find_if(g.columns.begin(), g.columns.end(), [&](auto s) {
      return s.x <= x && x < s.x + s.width;
    });
    if (s == g.columns.end())
      return {};
    if (y < g.header_rows) {
      if (options_.disable_header_sort)
        return {};
      auto cs = visible_columns();
      column = std::find_if(cs.begin(), cs.end(),
                            [&](auto c) { return c.id == s->id; }) -
               cs.begin();
      return request("sort");
    }
    int dy = y - g.header_rows;
    if (dy % g.stride || y >= height - g.footer_rows)
      return {};
    auto i = g.top + dy / g.stride;
    if (i >= source_size())
      return {};
    auto r = record(i);
    auto hit = hits_->rows.find(i);
    if (hit == hits_->rows.end() || hit->second != r.id)
      return {};
    auto c = std::find_if(columns.begin(), columns.end(),
                          [&](auto c) { return c.id == s->id; });
    if (info(r, *c).state.disabled || !focus(r.id, c->id))
      return {};
    return {"select", r.id, c->id};
  }

private:
  void arm_grid(GridCapture capture, int width, int height) {
    capture.width = width;
    capture.height = height;
    capture.revision = revision_;
    capture.signature = column_signature();
    capture_ = std::move(capture);
  }
  std::pair<std::string, std::string>
  range_anchor(const std::pair<GridRecord, GridColumn> &p) {
    return selected && selection_bounds()
               ? std::make_pair(selected->anchor_row, selected->anchor_column)
               : std::make_pair(p.first.id, p.second.id);
  }
  GridEvent extend_navigation(const std::string &action, int height) {
    auto p = current();
    if (!p)
      return {};
    auto anchor = range_anchor(*p);
    auto previous_row = row, previous_column = column;
    auto result = handle(action, height);
    auto after = current();
    if (result.kind != "select" || !after)
      return result;
    if (info(after->first, after->second).state.disabled) {
      row = previous_row;
      column = previous_column;
      return {};
    }
    set_selection(GridRange{anchor.first, anchor.second, after->first.id,
                            after->second.id});
    return result;
  }
  struct GridHit {
    const GridGeometry *geo;
    std::optional<GridSpan> span;
    std::optional<GridRecord> row;
    bool gutter = false;
  };
  std::optional<GridHit> grid_hit(int x, int y, int width, int height) {
    if (!hits_ || hits_->width != width || hits_->height != height ||
        hits_->signature != column_signature() || x < 0 || x >= width ||
        y < 0 || y >= height)
      return std::nullopt;
    const auto &geo = hits_->geometry;
    auto item = std::find_if(
        geo.columns.begin(), geo.columns.end(),
        [&](const auto &s) { return s.x <= x && x < s.x + s.width; });
    std::optional<GridSpan> span;
    if (item != geo.columns.end())
      span = *item;
    if (y < geo.header_rows)
      return GridHit{&geo, span, std::nullopt, false};
    int dy = y - geo.header_rows;
    if (dy % geo.stride || y >= height - geo.footer_rows)
      return std::nullopt;
    auto index = geo.top + dy / geo.stride;
    auto seen = hits_->rows.find(index);
    if (seen == hits_->rows.end())
      return std::nullopt;
    std::optional<GridRecord> r;
    if (index < source_size())
      r = record(index);
    if (!r || r->id != seen->second) {
      if (capture_ && (capture_->kind == "range" || capture_->kind == "edit"))
        capture_.reset();
      return std::nullopt;
    }
    bool gutter = !span && x < geo.gutter && options_.row_numbers;
    if (!span && !gutter)
      return std::nullopt;
    return GridHit{&geo, span, std::move(r), gutter};
  }
  GridEvent edit_pointer(const std::string &action, int x, int y, int width,
                         int height, bool extend) {
    if (!edit || edit->pending || edit->null ||
        !work_valid(edit->row_id, edit->column_id, edit->revision)) {
      capture_.reset();
      return {};
    }
    if (action == "move" && (!capture_ || capture_->kind != "edit"))
      return {};
    if (action != "down" && action != "move" && action != "click" &&
        action != "double")
      return {};
    auto hit = grid_hit(x, y, width, height);
    if (!hit || !hit->span || !hit->row || hit->row->id != edit->row_id ||
        hit->span->id != edit->column_id)
      return action == "move" ? GridEvent{} : GridEvent{"edit_blocked"};
    auto col = std::find_if(columns.begin(), columns.end(),
                            [&](auto &c) { return c.id == hit->span->id; });
    int extra = options_.show_cell_markers && info(*hit->row, *col).state.edited
                    ? 2
                    : 0;
    int pad = options_.padding + extra,
        room = hit->span->width - 2 * options_.padding - extra;
    if (room <= 0)
      return {};
    auto &buf = edit->buffer;
    auto start = std::get<3>(grid_detail::window(buf.value, buf.cursor, room));
    int offset = std::clamp(x - hit->span->x - pad, 0, room), used = 0;
    auto pos = start;
    auto gs = graphemes(buf.value);
    for (auto i = start; i < gs.size(); i++) {
      int w = cells(clean(gs[i].text));
      if (used + w > offset)
        break;
      used += w;
      pos++;
    }
    buf.select(extend || action == "move" ? buf.anchor : pos, pos);
    if (action == "down") {
      GridCapture next;
      next.kind = "edit";
      next.edit_id = edit->id;
      arm_grid(std::move(next), width, height);
    }
    return {"edit_select", edit->row_id, edit->column_id};
  }

public:
  bool pointer_captured() const { return capture_.has_value(); }
  GridEvent pointer(const std::string &action, int x, int y, int width,
                    int height, bool extend = false) {
    mutation();
    if (action != "down" && action != "move" && action != "up" &&
        action != "cancel" && action != "click" && action != "double" &&
        action != "wheel_up" && action != "wheel_down" &&
        action != "wheel_left" && action != "wheel_right")
      return {};
    grid_detail::number(x, -1000000000, 1000000000, "pointer x");
    grid_detail::number(y, -1000000000, 1000000000, "pointer y");
    grid_detail::number(width, 0, 65535, "width");
    grid_detail::number(height, 0, 4096, "height");
    if (capture_ && (capture_->width != width || capture_->height != height ||
                     capture_->revision != revision_ ||
                     capture_->signature != column_signature()))
      capture_.reset();
    if (options_.disable_mouse || paste_ || action == "cancel") {
      capture_.reset();
      return {};
    }
    if (action == "up") {
      auto previous = std::move(capture_);
      capture_.reset();
      if (previous && previous->kind == "column" && !previous->moved) {
        auto hit = grid_hit(x, y, width, height);
        if (hit && !hit->row && hit->span && hit->span->id == previous->column)
          return click(x, y, width, height);
      }
      return {};
    }
    if (action == "down")
      capture_.reset();
    if (edit) {
      if (capture_ && capture_->kind == "edit" && capture_->edit_id != edit->id)
        capture_.reset();
      return edit_pointer(action, x, y, width, height, extend);
    }
    if (action.rfind("wheel_", 0) == 0) {
      capture_.reset();
      return handle(action.substr(6), height);
    }
    if (action == "move" && !capture_)
      return {};
    if (action == "move" && capture_->kind == "resize") {
      const auto id = capture_->column;
      auto col = std::find_if(columns.begin(), columns.end(),
                              [&](auto &c) { return c.id == id; });
      auto o = column_options_.count(id) ? column_options_.at(id)
                                         : GridColumnOptions{};
      int value = std::clamp(capture_->start_width + x - capture_->start_x,
                             o.min_width, o.max_width);
      if (col != columns.end() && value != col->width) {
        auto next = *capture_;
        if (resize_column(id, value)) {
          arm_grid(std::move(next), width, height);
          return {"resize", "", id};
        }
      }
      return {};
    }
    if (action == "move" && capture_->kind == "column") {
      auto geo = geometry(width, height);
      const auto id = capture_->column;
      auto span =
          std::find_if(geo.columns.begin(), geo.columns.end(),
                       [&](auto &s) { return s.x <= x && x < s.x + s.width; });
      if (span != geo.columns.end() && span->id != id) {
        auto source = std::find_if(columns.begin(), columns.end(),
                                   [&](auto &c) { return c.id == id; }),
             target = std::find_if(columns.begin(), columns.end(),
                                   [&](auto &c) { return c.id == span->id; });
        if (source != columns.end() && target != columns.end() &&
            source->pin == target->pin) {
          auto order = columns;
          auto item = *source;
          auto at = target - columns.begin();
          order.erase(order.begin() + (source - columns.begin()));
          order.insert(order.begin() + at, std::move(item));
          auto next = *capture_;
          next.moved = true;
          set_column_layout(order);
          arm_grid(std::move(next), width, height);
          return {"columns", "", id};
        }
      }
      return {};
    }
    auto hit = grid_hit(x, y, width, height);
    if (!hit)
      return {};
    if (!hit->row) {
      if (action == "down") {
        if (options_.vertical_lines && !options_.disable_resize) {
          for (const auto &s : hit->geo->columns)
            if (s.x + s.width == x) {
              auto col = std::find_if(columns.begin(), columns.end(),
                                      [&](auto &c) { return c.id == s.id; });
              GridCapture next;
              next.kind = "resize";
              next.column = s.id;
              next.start_x = x;
              next.start_width = col->width;
              arm_grid(std::move(next), width, height);
              return {"resize_start", "", s.id};
            }
        }
        if (hit->span) {
          GridCapture next;
          next.kind = "column";
          next.column = hit->span->id;
          arm_grid(std::move(next), width, height);
        }
        return {};
      }
      return action == "click" || action == "double"
                 ? click(x, y, width, height)
                 : GridEvent{};
    }
    if (action == "move" && (!capture_ || capture_->kind != "range"))
      return {};
    auto p = current();
    auto cs = visible_columns();
    auto id = hit->span ? hit->span->id : p ? p->second.id : "";
    auto col =
        std::find_if(cs.begin(), cs.end(), [&](auto &c) { return c.id == id; });
    if (col == cs.end() || info(*hit->row, *col).state.disabled)
      return {};
    auto anchor =
        extend && p ? range_anchor(*p) : std::make_pair(hit->row->id, id);
    bool whole = hit->gutter || options_.selection == "row";
    if (action == "move") {
      auto index = source_index(capture_->anchor_row);
      if (!index || index != capture_->anchor_index ||
          record(*index).id != capture_->anchor_row) {
        capture_.reset();
        return {};
      }
      anchor = {capture_->anchor_row, capture_->anchor_column};
      whole = capture_->whole;
    }
    if (!focus(hit->row->id, id))
      return {};
    if (action == "double")
      return handle("activate", height);
    if (whole || extend || action == "move")
      set_selection(GridRange{anchor.first,
                              whole ? cs.front().id : anchor.second,
                              hit->row->id, whole ? cs.back().id : id});
    else if (action == "down" || action == "click")
      selected.reset();
    if (action == "down") {
      GridCapture next;
      next.kind = "range";
      next.anchor_row = anchor.first;
      next.anchor_column = anchor.second;
      next.anchor_index = source_index(anchor.first);
      next.whole = whole;
      arm_grid(std::move(next), width, height);
    }
    return {"select", hit->row->id, id};
  }
  GridViewState save_view() {
    auto p = current();
    GridViewState s;
    s.columns = columns;
    s.column_options = column_options_;
    s.row_id = p ? p->first.id : "";
    s.column_id = p ? p->second.id : "";
    s.top_row_id = top < source_size() ? record(top).id : "";
    auto cs = visible_columns();
    cs.erase(std::remove_if(cs.begin(), cs.end(),
                            [](auto c) { return !c.pin.empty(); }),
             cs.end());
    s.left_column_id = left < int(cs.size()) ? cs[left].id : "";
    s.sort_column = sort_column;
    s.sort_direction = sort_direction;
    s.selection = selected;
    s.mode = options_.selection;
    s.filter = status.filter;
    return s;
  }
  void restore_view(GridViewState s) {
    mutation();
    Grid temporary(columns, std::vector<GridRecord>{});
    temporary.set_column_layout(s.columns);
    for (auto c : s.columns) {
      grid_detail::number(c.width, 1, 4096, "invalid column width");
      auto it = std::find_if(temporary.columns.begin(), temporary.columns.end(),
                             [&](auto x) { return x.id == c.id; });
      it->width = c.width;
    }
    for (auto entry : s.column_options)
      temporary.set_column_options(entry.first, entry.second);
    if ((s.mode != "cell" && s.mode != "row" && s.mode != "range") ||
        (!s.sort_direction.empty() && s.sort_direction != "asc" &&
         s.sort_direction != "desc") ||
        (!s.sort_column.empty() &&
         std::none_of(columns.begin(), columns.end(),
                      [&](auto c) { return c.id == s.sort_column; })))
      throw std::invalid_argument("invalid grid view state");
    auto at = source_index(s.top_row_id);
    if (at)
      record(*at);
    if (s.selection) {
      auto cs = temporary.visible_columns();
      for (auto pair : std::vector<std::pair<std::string, std::string>>{
               {s.selection->anchor_row, s.selection->anchor_column},
               {s.selection->end_row, s.selection->end_column}}) {
        auto i = source_index(pair.first);
        if (!i || record(*i).id != pair.first ||
            std::none_of(cs.begin(), cs.end(),
                         [&](auto c) { return c.id == pair.second; }))
          throw std::invalid_argument("unknown view range ID");
      }
    }
    invalidate();
    columns = std::move(temporary.columns);
    column_options_ = std::move(temporary.column_options_);
    options_.selection = s.mode;
    top = at.value_or(0);
    left = 0;
    auto cs = visible_columns();
    for (auto c : cs)
      if (c.pin.empty()) {
        if (c.id == s.left_column_id)
          break;
        ++left;
      }
    sort_column = s.sort_column;
    sort_direction = s.sort_direction;
    status.filter = s.filter;
    selected = s.selection;
    focus(s.row_id, s.column_id);
  }
};
} // namespace tuivory
