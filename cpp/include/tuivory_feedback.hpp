#pragma once
#include <cstdint>
#include <tuple>
namespace tuivory {
struct NoticeAction {
  std::string id, label;
  bool disabled = false;
};
struct Notice {
  std::string id, text, detail, severity = "info";
  int priority = 0;
  bool persistent = false;
  std::uint64_t expires_at = 0;
  std::vector<NoticeAction> actions;
};
struct NoticeEvent {
  std::string kind, id, action;
};
struct FeedbackSpan {
  int start = 0, width = 0;
  std::string text, role, action;
  bool disabled = false;
};
struct FeedbackRow {
  std::string id, text, role = "body";
  bool focused = false;
  std::vector<FeedbackSpan> spans;
};
inline void feedback_number(std::uint64_t n) {
  if (n > 9007199254740991ULL)
    throw std::invalid_argument("expected a nonnegative safe integer");
}
inline int notice_severity(const std::string &s) {
  return s == "info"      ? 0
         : s == "success" ? 1
         : s == "warning" ? 2
         : s == "error"   ? 3
                          : -1;
}
inline void feedback_draw(Canvas &c, Rect r,
                          const std::vector<FeedbackRow> &rows) {
  c.fill(r);
  for (int y = 0;
       y < std::max(0, r.height) && y < static_cast<int>(rows.size()); y++) {
    const auto &row = rows[y];
    c.write(r.x, r.y + y, row.text, row.role, false, r.width, true);
    for (const auto &s : row.spans)
      c.write(r.x + s.start, r.y + y, s.text, s.role, false, s.width, true);
  }
}
class NoticeQueue {
  std::size_t capacity_;
  std::vector<Notice> items_;
  std::vector<FeedbackRow> hits_;
  int width_ = 0;
  static bool pinned(const Notice &n) {
    return n.persistent || n.severity == "error" || !n.actions.empty();
  }
  static bool expired(const Notice &n, std::uint64_t now) {
    return !pinned(n) && n.expires_at > 0 && n.expires_at <= now;
  }
  static std::size_t limit(std::size_t count, int height) {
    height = std::max(0, std::min(4096, height));
    return count > static_cast<std::size_t>(height) && height > 0
               ? std::max(1, height - 1)
               : height;
  }

public:
  std::string focused;
  explicit NoticeQueue(std::size_t capacity = 10) : capacity_(capacity) {
    if (!capacity || capacity > 65536)
      throw std::invalid_argument("notice capacity must be 1..65536");
  }
  std::size_t capacity() const { return capacity_; }
  const std::vector<Notice> &items() const { return items_; }
  void push(Notice n) {
    if (n.id.empty() || notice_severity(n.severity) < 0)
      throw std::invalid_argument("invalid notice ID or severity");
    feedback_number(n.expires_at);
    std::map<std::string, bool> ids;
    if (n.actions.size() > 1024)
      throw std::invalid_argument("too many notice actions");
    for (const auto &a : n.actions)
      if (a.id.empty() || !ids.emplace(a.id, true).second)
        throw std::invalid_argument("invalid notice action");
    for (auto &old : items_)
      if (old.id == n.id) {
        old = std::move(n);
        hits_.clear();
        return;
      }
    std::optional<std::size_t> evict;
    if (items_.size() >= capacity_) {
      for (std::size_t i = 0; i < items_.size(); i++)
        if (!pinned(items_[i]) &&
            (!evict ||
             std::make_tuple(notice_severity(items_[i].severity),
                             items_[i].priority) <
                 std::make_tuple(notice_severity(items_[*evict].severity),
                                 items_[*evict].priority)))
          evict = i;
      if (!evict)
        throw std::invalid_argument(
            "notice queue full; important notices retained");
      const auto &old = items_[*evict];
      if (std::make_tuple(notice_severity(old.severity), old.priority) >
          std::make_tuple(notice_severity(n.severity), n.priority))
        throw std::invalid_argument("notice queue full");
    }
    items_.reserve(items_.size() + 1);
    if (evict) {
      if (focused == items_[*evict].id)
        focused.clear();
      items_.erase(items_.begin() + *evict);
    }
    if (focused.empty() || n.severity == "error")
      focused = n.id;
    items_.push_back(std::move(n));
    hits_.clear();
  }
  std::vector<Notice> visible(std::uint64_t now = 0) const {
    feedback_number(now);
    std::vector<Notice> out;
    for (const auto &n : items_)
      if (!expired(n, now))
        out.push_back(n);
    std::stable_sort(
        out.begin(), out.end(), [](const Notice &a, const Notice &b) {
          return std::make_tuple(notice_severity(a.severity), a.priority) >
                 std::make_tuple(notice_severity(b.severity), b.priority);
        });
    return out;
  }
  bool dismiss(const std::string &id) {
    auto it = std::find_if(items_.begin(), items_.end(),
                           [&](const Notice &n) { return n.id == id; });
    if (it == items_.end())
      return false;
    if (focused == id)
      focused.clear();
    items_.erase(it);
    hits_.clear();
    return true;
  }
  std::vector<NoticeEvent> expire(std::uint64_t now) {
    feedback_number(now);
    std::vector<NoticeEvent> out;
    for (const auto &n : items_)
      if (expired(n, now))
        out.push_back({"expired", n.id, ""});
    for (const auto &e : out)
      dismiss(e.id);
    return out;
  }
  NoticeEvent request_action(const std::string &id, const std::string &action,
                             std::uint64_t now = 0) const {
    for (const auto &n : visible(now))
      if (n.id == id)
        for (const auto &a : n.actions)
          if (a.id == action && !a.disabled)
            return {"action", id, action};
    return {};
  }
  NoticeEvent handle(std::string action, std::uint64_t now = 0,
                     int height = 10) {
    if (action == "down")
      action = "next";
    if (action == "up")
      action = "previous";
    auto entries = visible(now);
    entries.resize(std::min(entries.size(), limit(entries.size(), height)));
    if (entries.empty() || (action != "next" && action != "previous" &&
                            action != "activate" && action != "dismiss"))
      return {};
    std::size_t at = 0;
    for (std::size_t i = 0; i < entries.size(); i++)
      if (entries[i].id == focused)
        at = i;
    if (action == "next")
      at = std::min(at + 1, entries.size() - 1);
    else if (action == "previous" && at)
      at--;
    const auto &n = entries[at];
    focused = n.id;
    if (action == "dismiss")
      return {"dismiss", n.id, ""};
    if (action == "activate")
      for (const auto &a : n.actions)
        if (!a.disabled)
          return {"action", n.id, a.id};
    return {};
  }
  std::vector<FeedbackRow> layout(int width, int height,
                                  std::uint64_t now = 0) {
    width_ = width = std::max(0, std::min(65535, width));
    height = std::max(0, std::min(4096, height));
    auto entries = visible(now);
    auto count = limit(entries.size(), height);
    std::vector<FeedbackRow> rows;
    for (std::size_t i = 0; i < std::min(count, entries.size()); i++) {
      const auto &n = entries[i];
      std::string mark = n.severity == "error"     ? "[!]"
                         : n.severity == "warning" ? "[?]"
                         : n.severity == "success" ? "[+]"
                                                   : "[i]";
      std::string value =
          (focused == n.id ? "> " : "  ") + mark + " " + clean(n.text);
      if (!n.detail.empty())
        value += " / " + clean(n.detail);
      std::vector<FeedbackSpan> parts;
      for (const auto &a : n.actions) {
        std::string part = " [" + clean(a.label) + "]";
        parts.push_back({cells(value), 0, part,
                         a.disabled ? "disabled" : n.severity, a.id,
                         a.disabled});
        value += part;
      }
      int end = cells(value) > width ? std::max(0, width - 1) : width;
      std::vector<FeedbackSpan> spans;
      for (auto &part : parts) {
        part.text = clip(part.text, std::max(0, end - part.start));
        part.width = cells(part.text);
        if (part.width)
          spans.push_back(std::move(part));
      }
      rows.push_back({n.id, clip(value, width, true), n.severity,
                      focused == n.id, std::move(spans)});
    }
    if (entries.size() > count && height > static_cast<int>(rows.size()))
      rows.push_back(
          {"",
           clip("+" + std::to_string(entries.size() - count), width, true),
           "hint",
           false,
           {}});
    hits_ = rows;
    return rows;
  }
  NoticeEvent click(int x, int y, std::uint64_t now = 0) {
    feedback_number(now);
    if (x < 0 || x >= width_ || y < 0 ||
        static_cast<std::size_t>(y) >= hits_.size())
      return {};
    const auto row = hits_[y];
    auto entries = visible(now);
    if (row.id.empty() ||
        std::none_of(entries.begin(), entries.end(),
                     [&](const Notice &n) { return n.id == row.id; }))
      return {};
    for (const auto &s : row.spans)
      if (x >= s.start && x < s.start + s.width) {
        if (s.disabled)
          return {};
        focused = row.id;
        return request_action(row.id, s.action, now);
      }
    focused = row.id;
    return {"focus", row.id, ""};
  }
  void draw(Canvas &c, Rect r, std::uint64_t now = 0) {
    feedback_draw(c, r, layout(r.width, r.height, now));
  }
};
struct Progress {
  std::string id, label, status = "loading", message, cancel_label;
  std::uint64_t current = 0, total = 0;
  bool cancellable = false;
  NoticeEvent request_cancel() const {
    return !id.empty() && cancellable && (status.empty() || status == "loading")
               ? NoticeEvent{"cancel", id, ""}
               : NoticeEvent{};
  }
  std::vector<FeedbackRow> layout(int width, std::uint64_t frame = 0) const {
    feedback_number(current);
    feedback_number(total);
    feedback_number(frame);
    width = std::max(0, std::min(65535, width));
    auto state = status.empty() ? "loading" : status;
    std::string role = state == "error"                           ? "error"
                       : state == "success"                       ? "success"
                       : state == "empty" || state == "cancelled" ? "hint"
                       : state == "ready"                         ? "body"
                       : state == "loading"                       ? "info"
                                                                  : "error",
                value = state;
    if (state == "loading") {
      if (!total)
        value = std::string(1, "|/-\\"[frame % 4]);
      else {
        double ratio = static_cast<double>(std::min(current, total)) / total;
        int size = std::min(30, std::max(0, width - 10)),
            done = static_cast<int>(ratio * size);
        value = "[" + std::string(done, '#') + std::string(size - done, '-') +
                "] " + std::to_string(static_cast<int>(ratio * 100)) + "%";
      }
    }
    if (!message.empty())
      value += " " + message;
    std::vector<FeedbackRow> rows{
        {id, clip(label, width, true), role, false, {}},
        {id, clip(value, width, true), role, false, {}}};
    if (!request_cancel().kind.empty() && !cancel_label.empty())
      rows.push_back({id, clip(cancel_label, width, true), "hint", false, {}});
    return rows;
  }
  void draw(Canvas &c, Rect r, std::uint64_t frame = 0) const {
    feedback_draw(c, r, layout(r.width, frame));
  }
};
struct DataState {
  std::string kind = "empty", text, detail;
  std::vector<FeedbackRow> layout(int width) const {
    width = std::max(0, std::min(65535, width));
    return {{"",
             clip(text, width, true),
             kind == "ready"     ? "body"
             : kind == "loading" ? "info"
             : kind == "empty"   ? "hint"
                                 : "error",
             false,
             {}},
            {"", clip(detail, width, true), "hint", false, {}}};
  }
  void draw(Canvas &c, Rect r) const { feedback_draw(c, r, layout(r.width)); }
};
} // namespace tuivory
