#pragma once
namespace tuivory {
namespace dialog_detail {
inline void text(const std::string &value, std::size_t limit) {
  if (value.size() > limit)
    throw std::invalid_argument("dialog text/ID exceeds limit");
  for (std::size_t p = 0; p < value.size();) {
    auto start = p;
    auto cp = detail::decode(value, p);
    if (cp == 0xfffd && value.substr(start, p - start) != "\xef\xbf\xbd")
      throw std::invalid_argument("invalid dialog UTF-8");
  }
}
inline std::pair<std::vector<std::string>, bool> wrap(const std::string &text,
                                                      int width, int limit) {
  if (text.empty())
    return {{}, false};
  if (width <= 0 || limit <= 0)
    return {{}, true};
  std::vector<std::string> rows;
  std::string line;
  int used = 0;
  bool last_break = false, truncated = false;
  for (auto g : graphemes(text)) {
    if (g.text == "\r" || g.text == "\n" || g.text == "\r\n") {
      if ((int)rows.size() >= limit) {
        truncated = true;
        break;
      }
      rows.push_back(line);
      line.clear();
      used = 0;
      last_break = true;
      continue;
    }
    last_break = false;
    g.text = clean(g.text);
    int n = cells(g.text);
    if (n > width) {
      g.text = clip(g.text, width, true);
      n = cells(g.text);
    }
    if (used + n > width && !line.empty()) {
      if ((int)rows.size() >= limit) {
        truncated = true;
        break;
      }
      rows.push_back(line);
      line.clear();
      used = 0;
    }
    if ((int)rows.size() >= limit) {
      truncated = true;
      break;
    }
    line += g.text;
    used += n;
  }
  if (!truncated && (!line.empty() || rows.empty() || last_break)) {
    if ((int)rows.size() < limit)
      rows.push_back(line);
    else
      truncated = true;
  }
  if (truncated && !rows.empty())
    rows.back() = clip(rows.back(), std::max(0, width - 1)) + "~";
  return {rows, truncated};
}
} // namespace dialog_detail
struct DialogButton {
  std::string id, label;
  bool disabled = false;
};
struct DialogButtonCell {
  std::string id;
  Rect rect;
  std::string text;
  bool disabled = false, focused = false;
};
struct DialogLayout {
  std::vector<std::string> body;
  std::vector<DialogButtonCell> buttons;
  std::size_t hidden_buttons = 0;
  bool body_truncated = false;
};
class Dialog {
  std::string title_, message_, cancel_, focused_;
  std::vector<DialogButton> buttons_;
  struct Hit {
    Rect rect;
    std::string id;
    bool disabled;
  };
  std::vector<Hit> hits_;

public:
  explicit Dialog(std::string title = "", std::string message = "",
                  std::vector<DialogButton> buttons = {},
                  std::string cancel_id = "") {
    set_text(std::move(title), std::move(message));
    set_buttons(std::move(buttons), std::move(cancel_id));
  }
  const std::string &title() const { return title_; }
  const std::string &message() const { return message_; }
  const std::string &cancel_id() const { return cancel_; }
  const std::string &focused() const { return focused_; }
  std::vector<DialogButton> buttons() const { return buttons_; }
  void set_text(std::optional<std::string> title = std::nullopt,
                std::optional<std::string> message = std::nullopt) {
    auto heading = title ? *title : title_,
         content = message ? *message : message_;
    dialog_detail::text(heading, 4096);
    dialog_detail::text(content, 1000000);
    title_ = std::move(heading);
    message_ = std::move(content);
    hits_.clear();
  }
  void set_buttons(std::vector<DialogButton> buttons,
                   std::optional<std::string> cancel_id = std::nullopt) {
    if (buttons.size() > 1024)
      throw std::invalid_argument("too many dialog buttons");
    std::set<std::string> ids;
    std::vector<std::string> eligible;
    for (const auto &b : buttons) {
      dialog_detail::text(b.id, 1024);
      dialog_detail::text(b.label, 4096);
      if (b.id.empty() || !ids.insert(b.id).second)
        throw std::invalid_argument("empty/duplicate dialog button ID");
      if (!b.disabled)
        eligible.push_back(b.id);
    }
    auto cancel = cancel_id ? *cancel_id : cancel_;
    dialog_detail::text(cancel, 1024);
    if (!cancel.empty() && !ids.count(cancel))
      throw std::invalid_argument("unknown dialog cancel ID");
    auto has = [&](const std::string &id) {
      return std::find(eligible.begin(), eligible.end(), id) != eligible.end();
    };
    auto focus = has(focused_)      ? focused_
                 : has(cancel)      ? cancel
                 : eligible.empty() ? ""
                                    : eligible.front();
    buttons_ = std::move(buttons);
    cancel_ = std::move(cancel);
    focused_ = std::move(focus);
    hits_.clear();
  }
  bool focus(const std::string &id) {
    for (const auto &b : buttons_)
      if (b.id == id && !b.disabled) {
        if (focused_ != id) {
          focused_ = id;
          hits_.clear();
        }
        return true;
      }
    return false;
  }
  Event handle(const std::string &action) {
    std::vector<std::string> eligible;
    for (const auto &b : buttons_)
      if (!b.disabled)
        eligible.push_back(b.id);
    auto has = [&](const std::string &id) {
      return std::find(eligible.begin(), eligible.end(), id) != eligible.end();
    };
    if (action == "cancel")
      return cancel_.empty() ? Event{"cancel", "", ""}
             : has(cancel_)  ? Event{"cancel", cancel_, ""}
                             : Event{};
    if (action == "activate")
      return has(focused_) ? Event{"activate", focused_, ""} : Event{};
    if (eligible.empty())
      return {};
    auto it = std::find(eligible.begin(), eligible.end(), focused_);
    std::size_t at = it == eligible.end() ? 0 : it - eligible.begin();
    if (action == "next" || action == "right" || action == "down")
      at = (at + 1) % eligible.size();
    else if (action == "previous" || action == "left" || action == "up")
      at = (at + eligible.size() - 1) % eligible.size();
    else if (action == "home")
      at = 0;
    else if (action == "end")
      at = eligible.size() - 1;
    else
      return {};
    auto id = eligible[at];
    if (id == focused_)
      return {};
    focus(id);
    return {"focus", id, ""};
  }
  DialogLayout layout(int width, int height) const {
    popup_detail::number(width);
    popup_detail::number(height);
    if (!width || !height)
      return {{}, {}, buttons_.size(), !message_.empty()};
    struct Position {
      DialogButton button;
      Rect rect;
    };
    std::vector<Position> positions;
    int x = 0, y = 0, focus_row = 0;
    for (const auto &b : buttons_) {
      auto label = clean(b.label.empty() ? b.id : b.label);
      int w = std::min(width, std::max(1, cells(label) + 4));
      if (x && x + 1 + w > width) {
        x = 0;
        y++;
      }
      if (x)
        x++;
      positions.push_back({b, {x, y, w, 1}});
      if (b.id == focused_)
        focus_row = y;
      x += w;
    }
    int total_rows = positions.empty() ? 0 : y + 1,
        visible = std::min(height, total_rows),
        start = std::max(0, focus_row + 1 - visible),
        available = height - visible,
        gap = !message_.empty() && visible && available >= 2 ? 1 : 0;
    auto body = dialog_detail::wrap(message_, width, available - gap);
    DialogLayout out;
    out.body = std::move(body.first);
    out.body_truncated = body.second;
    for (const auto &p : positions) {
      auto r = p.rect;
      const auto &b = p.button;
      if (r.y < start || r.y >= start + visible)
        continue;
      auto label = clean(b.label.empty() ? b.id : b.label),
           text =
               r.width >= 6
                   ? "[ " + clip(label, std::max(0, r.width - 4), true) + " ]"
                   : clip(label, r.width, true);
      out.buttons.push_back({b.id,
                             {r.x, height - visible + r.y - start, r.width, 1},
                             text,
                             b.disabled,
                             b.id == focused_});
    }
    out.hidden_buttons = buttons_.size() - out.buttons.size();
    return out;
  }
  DialogLayout draw(Canvas &canvas, Rect bounds, bool focused = true,
                    bool ascii = false) {
    popup_detail::rect(bounds);
    hits_.clear();
    int x = std::min(bounds.x, canvas.width),
        y = std::min(bounds.y, canvas.height);
    Rect r{x, y,
           std::max(0, std::min(canvas.width, bounds.x + bounds.width) - x),
           std::max(0, std::min(canvas.height, bounds.y + bounds.height) - y)};
    auto inner = inset_rect(canvas.panel(r, title_, focused, ascii), 1);
    auto result = layout(inner.width, inner.height);
    for (std::size_t y = 0; y < result.body.size(); y++)
      canvas.write(inner.x, inner.y + (int)y, result.body[y], "body", false,
                   inner.width);
    for (const auto &b : result.buttons) {
      Rect r{inner.x + b.rect.x, inner.y + b.rect.y, b.rect.width, 1};
      std::string role = b.disabled             ? "disabled"
                         : focused && b.focused ? "button.focus"
                                                : "button";
      canvas.fill(r, role);
      canvas.write(r.x + std::max(0, (r.width - cells(b.text)) / 2), r.y,
                   b.text, role, false, r.width);
      hits_.push_back({r, b.id, b.disabled});
    }
    return result;
  }
  Event click(int x, int y) {
    for (const auto &h : hits_)
      if (h.rect.contains(x, y)) {
        if (h.disabled)
          return {};
        auto id = h.id;
        focus(id);
        return {"activate", id, ""};
      }
    return {};
  }
};
} // namespace tuivory
