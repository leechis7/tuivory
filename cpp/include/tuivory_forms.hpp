#pragma once
namespace tuivory {
struct FormOption {
  std::string id, label;
  bool disabled = false;
};
struct Field {
  std::string id, kind = "text", label, value, help, error, choice, action,
                  pending;
  std::vector<FormOption> options;
  State state;
  bool required = false, checked = false, open = false;
  int height = 3;
};
struct FormEvent {
  std::string kind, id, text;
  std::vector<std::string> missing;
};
struct FormRow {
  std::string id, text, role = "body", option;
  bool input = false, focused = false;
  int source_row = 0;
};
class Form {
  std::vector<Field> fields_;
  std::map<std::string, Text> inputs_;
  std::vector<FormRow> hits_;
  int layout_width_ = 0;
  Field *field(const std::string &id) {
    for (auto &f : fields_)
      if (f.id == id)
        return &f;
    return nullptr;
  }
  std::vector<std::string> eligible() {
    std::vector<std::string> out;
    for (const auto &f : fields_)
      if (f.state.focusable())
        out.push_back(f.id);
    if (std::find(out.begin(), out.end(), focused) == out.end())
      focused = out.empty() ? "" : out.front();
    return out;
  }

public:
  std::string focused;
  int scroll = 0;
  explicit Form(std::vector<Field> fields) : fields_(std::move(fields)) {
    std::set<std::string> ids;
    for (auto &f : fields_) {
      if (f.id.empty() || !ids.insert(f.id).second)
        throw std::invalid_argument("invalid field ID");
      if (f.open || std::find(std::begin(kinds), std::end(kinds), f.kind) ==
                        std::end(kinds))
        throw std::invalid_argument("invalid kind/open select");
      std::set<std::string> options;
      for (const auto &o : f.options)
        if (o.id.empty() || !options.insert(o.id).second)
          throw std::invalid_argument("invalid option ID");
      if (!f.choice.empty() && !options.count(f.choice))
        throw std::invalid_argument("unknown choice");
      if (f.kind == "text" || f.kind == "textarea" || f.kind == "password") {
        Text t(f.value);
        t.secret = f.kind == "password";
        t.multiline = f.kind == "textarea";
        f.value = t.display();
        inputs_.emplace(f.id, std::move(t));
      }
    }
    eligible();
  }
  inline static const std::string kinds[] = {
      "text", "textarea", "password", "checkbox", "radio", "select", "button"};
  const std::vector<Field> &fields() const { return fields_; }
  std::string value(const std::string &id) const {
    auto t = inputs_.find(id);
    if (t != inputs_.end())
      return t->second.value;
    for (const auto &f : fields_)
      if (f.id == id)
        return f.value;
    throw std::invalid_argument("unknown field");
  }
  bool focus(const std::string &id) {
    auto *f = field(id);
    if (!f || !f->state.focusable())
      return false;
    for (auto &v : fields_)
      v.open = false;
    focused = id;
    return true;
  }
  bool at_tab_boundary(bool previous = false) {
    auto ids = eligible();
    return ids.empty() || focused == (previous ? ids.front() : ids.back());
  }
  bool set_state(const std::string &id, State state) {
    auto *f = field(id);
    if (!f)
      return false;
    f->state = state;
    if (!state.editable())
      f->open = false;
    eligible();
    return true;
  }
  bool set_feedback(const std::string &id, const std::string &help,
                    const std::string &error) {
    auto *f = field(id);
    if (!f)
      return false;
    f->help = help;
    f->error = error;
    f->state.invalid = !error.empty();
    return true;
  }
  bool select_text(const std::string &id, std::size_t a, std::size_t c) {
    auto t = inputs_.find(id);
    if (t == inputs_.end())
      return false;
    t->second.select(a, c);
    return true;
  }
  std::vector<std::string> missing() const {
    std::vector<std::string> out;
    for (const auto &f : fields_) {
      bool empty = false;
      if (inputs_.count(f.id)) {
        auto text = value(f.id);
        empty = true;
        for (std::size_t p = 0; p < text.size();) {
          auto cp = detail::decode(text, p);
          if (!((cp >= 9 && cp <= 13) || cp == 32 || cp == 0x85 || cp == 0xa0 ||
                cp == 0x1680 || (cp >= 0x2000 && cp <= 0x200a) ||
                cp == 0x2028 || cp == 0x2029 || cp == 0x202f || cp == 0x205f ||
                cp == 0x3000)) {
            empty = false;
            break;
          }
        }
      } else if (f.kind == "checkbox")
        empty = !f.checked;
      else if (f.kind == "radio" || f.kind == "select")
        empty = f.choice.empty();
      if (!f.state.disabled &&
          (f.state.invalid || !f.error.empty() || (f.required && empty)))
        out.push_back(f.id);
    }
    return out;
  }
  FormEvent handle(std::string action, const std::string &text = "") {
    auto ids = eligible();
    if (action == "next" || action == "previous") {
      if (!ids.empty()) {
        auto i = std::find(ids.begin(), ids.end(), focused) - ids.begin();
        focus(ids[(i + ids.size() + (action == "next" ? 1 : -1)) % ids.size()]);
      }
      return {};
    }
    if (action == "submit") {
      auto m = missing();
      return {m.empty() ? "submit" : "invalid", "", "", m};
    }
    auto *f = field(focused);
    if (!f)
      return {};
    if (action == "cancel") {
      if (f->open) {
        f->open = false;
        return {};
      }
      return {"cancel", f->id, "", {}};
    }
    if (action == "insert" && text == " " && !inputs_.count(f->id))
      action = "toggle";
    auto input = inputs_.find(f->id);
    if (input != inputs_.end()) {
      auto &t = input->second;
      t.state = f->state;
      if (action == "activate" && f->kind != "textarea")
        return f->state.activatable() ? handle("submit") : FormEvent{};
      auto e = t.handle(action == "activate" ? "newline" : action, text);
      f->value = t.display();
      f->state = t.state;
      return {e.kind, f->id, e.text, {}};
    }
    if (f->kind == "button" && (action == "left" || action == "right") &&
        !f->state.disabled) {
      handle(action == "left" ? "previous" : "next");
      return {};
    }
    if (!f->state.activatable())
      return {};
    if (f->kind == "button" && (action == "activate" || action == "toggle")) {
      if (f->action == "submit")
        return handle("submit");
      return {f->action == "cancel" ? "cancel" : "activate", f->id, "", {}};
    }
    if (!f->state.editable())
      return {};
    bool changed = false;
    if (f->kind == "checkbox" && (action == "activate" || action == "toggle")) {
      f->checked = !f->checked;
      changed = true;
    } else if (f->kind == "radio" || f->kind == "select") {
      if (f->kind == "select" && (action == "activate" || action == "toggle")) {
        if (f->open) {
          f->choice = f->pending;
          f->open = false;
          changed = true;
        } else {
          f->open = true;
          f->pending = f->choice;
          if (f->pending.empty())
            for (const auto &o : f->options)
              if (!o.disabled) {
                f->pending = o.id;
                break;
              }
          return {};
        }
      } else if (action == "left" || action == "right" || action == "up" ||
                 action == "down" || action == "activate" ||
                 action == "toggle") {
        if (f->kind == "select" && !f->open)
          return {};
        std::vector<std::string> choices;
        for (const auto &o : f->options)
          if (!o.disabled)
            choices.push_back(o.id);
        if (choices.empty())
          return {};
        auto current = f->open ? f->pending : f->choice;
        auto it = std::find(choices.begin(), choices.end(), current);
        std::size_t at = it == choices.end() ? 0 : it - choices.begin();
        std::size_t target = action == "left" || action == "up"
                                 ? (at + choices.size() - 1) % choices.size()
                             : it == choices.end() ? 0
                                                   : (at + 1) % choices.size();
        if (f->kind == "select")
          f->pending = choices[target];
        else {
          f->choice = choices[target];
          changed = true;
        }
      }
    }
    if (changed) {
      f->state.edited = true;
      return {"change", f->id, "", {}};
    }
    return {};
  }
  FormEvent click_field(const std::string &id, const std::string &option = "") {
    auto *f = field(id);
    if (!f || f->state.disabled)
      return {};
    for (const auto &o : f->options)
      if (o.id == option && o.disabled)
        return {};
    if (focused != id)
      focus(id);
    if (f->kind == "button")
      return handle("activate");
    if (!f->state.editable())
      return {};
    if (f->kind == "select" && !f->open)
      return handle("activate");
    if (!option.empty() && (f->kind == "radio" || f->kind == "select")) {
      for (const auto &o : f->options)
        if (o.id == option && !o.disabled) {
          f->choice = option;
          f->open = false;
          f->state.edited = true;
          return {"change", f->id, "", {}};
        }
      return {};
    }
    if (f->kind == "checkbox" || f->kind == "select")
      return handle("activate");
    return {};
  }
  std::vector<FormRow> layout(int width, int height) {
    std::vector<FormRow> rows;
    std::size_t anchor = 0;
    for (const auto &f : fields_) {
      bool current = f.id == focused;
      if (current)
        anchor = rows.size();
      auto role = f.state.disabled                      ? "disabled"
                  : !f.error.empty() || f.state.invalid ? "error"
                                                        : f.state.role();
      auto markers = f.state.markers();
      if (f.state.disabled && !markers.empty())
        markers.erase(0, 1);
      rows.push_back({f.id,
                      (current ? "> " : "  ") + f.label +
                          (f.required ? " *" : "") +
                          (markers.empty() ? "" : " " + markers),
                      role, "", false, current, 0});
      if (inputs_.count(f.id)) {
        auto text = inputs_.at(f.id).display();
        std::vector<std::string> lines;
        std::string line;
        for (const auto &g : graphemes(text)) {
          if (f.kind == "textarea" &&
              (g.text == "\r" || g.text == "\n" || g.text == "\r\n")) {
            lines.push_back(line);
            line.clear();
          } else
            line += g.text;
        }
        lines.push_back(line);
        int count = f.kind == "textarea" ? std::max(1, f.height) : 1;
        for (int i = 0; i < std::min(count, static_cast<int>(lines.size()));
             i++)
          rows.push_back({f.id, "  " + lines[i],
                          f.state.disabled ? "disabled" : "field", "", true,
                          false, i});
      } else if (f.kind == "checkbox")
        rows.push_back(
            {f.id, f.checked ? "  [x]" : "  [ ]", role, "", false, false, 0});
      else if (f.kind == "button")
        rows.push_back({f.id,
                        "  [ " + f.label + (f.state.busy ? " ~" : "") + " ]",
                        f.state.disabled ? "disabled"
                        : f.state.busy   ? "hint"
                                         : "button",
                        "", false, current, 0});
      else
        for (const auto &o : f.options) {
          if (f.kind == "select" && !f.open && o.id != f.choice)
            continue;
          rows.push_back(
              {f.id,
               "  (" +
                   std::string(o.id == (f.open ? f.pending : f.choice) ? "*"
                                                                       : " ") +
                   ") " + o.label,
               o.disabled || f.state.disabled ? "disabled" : role, o.id, false,
               false, 0});
        }
      if (!f.error.empty())
        rows.push_back({f.id, "! " + f.error, "error", "", false, false, 0});
      else if (!f.help.empty())
        rows.push_back({f.id, "  " + f.help, "hint", "", false, false, 0});
    }
    height = std::max(0, height);
    width = std::max(0, width);
    scroll = std::min(
        std::max(0, static_cast<int>(anchor) - std::max(0, height - 2)),
        std::max(0, static_cast<int>(rows.size()) - height));
    auto end = std::min(rows.size(), static_cast<std::size_t>(scroll + height));
    layout_width_ = width;
    hits_ = {rows.begin() + scroll, rows.begin() + end};
    for (auto &r : hits_)
      r.text = clip(r.text, width);
    return hits_;
  }
  FormEvent click(int x, int y, int height = 10) {
    if (x < 0 || x >= layout_width_ || y < 0 || y >= height ||
        static_cast<std::size_t>(y) >= hits_.size())
      return {};
    auto row = hits_[y];
    if (row.input && x >= 2) {
      auto *f = field(row.id);
      if (!f || f->state.disabled)
        return {};
      if (focused != row.id)
        focus(row.id);
      int first = -1, count = 0;
      for (std::size_t i = 0; i < hits_.size(); i++)
        if (hits_[i].id == row.id && hits_[i].input) {
          if (first < 0)
            first = static_cast<int>(i);
          count++;
        }
      auto e = inputs_.at(row.id).click(x - 2, y - first,
                                        std::max(0, layout_width_ - 2), count);
      return {e.kind, row.id, e.text, {}};
    }
    return click_field(row.id, row.option);
  }
  void draw(Canvas &c, Rect r, bool focused_view = true) {
    c.fill(r);
    auto rows = layout(r.width, r.height);
    for (std::size_t y = 0; y < rows.size(); y++)
      c.write(r.x, r.y + static_cast<int>(y), rows[y].text, rows[y].role,
              focused_view && rows[y].focused, r.width);
    for (auto &f : fields_) {
      int first = -1, count = 0;
      for (std::size_t i = 0; i < rows.size(); i++)
        if (rows[i].id == f.id && rows[i].input) {
          if (first < 0)
            first = static_cast<int>(i);
          count++;
        }
      if (first >= 0) {
        auto &t = inputs_.at(f.id);
        t.state = f.state;
        t.draw(c,
               {r.x + std::min(2, r.width), r.y + first,
                std::max(0, r.width - 2), count},
               focused_view && focused == f.id);
      }
    }
  }
};
class Control : public Form {
public:
  explicit Control(Field field) : Form({std::move(field)}) {}
};
} // namespace tuivory
