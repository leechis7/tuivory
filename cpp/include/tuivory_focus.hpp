#pragma once
namespace tuivory {
struct FocusTarget {
  std::string id;
  State state;
  bool hidden = false;
};
struct InputRoute {
  std::string scope_id;
  bool blocked = false;
};
struct PopupCloseRequest {
  std::string id, reason = "escape";
};
class Focus {
  struct Scope {
    std::string id, focused, restore;
    std::vector<FocusTarget> targets;
    bool dismissible = false;
  };
  std::vector<Scope> scopes_;
  static void validate(const std::vector<FocusTarget> &targets) {
    std::set<std::string> seen;
    for (const auto &t : targets)
      if (t.id.empty() || !seen.insert(t.id).second)
        throw std::invalid_argument("invalid target ID");
  }
  static std::vector<std::string> ids(const Scope &s) {
    std::vector<std::string> out;
    for (const auto &t : s.targets)
      if (!t.hidden && t.state.focusable())
        out.push_back(t.id);
    return out;
  }
  static bool set(Scope &s, const std::string &id) {
    auto list = ids(s);
    if (std::find(list.begin(), list.end(), id) == list.end())
      return false;
    s.focused = id;
    return true;
  }
  static void reconcile(Scope &s) {
    if (!set(s, s.focused)) {
      auto list = ids(s);
      s.focused = list.empty() ? "" : list.front();
    }
  }

public:
  Focus(std::string id, std::vector<FocusTarget> targets) {
    if (id.empty())
      throw std::invalid_argument("empty root scope");
    validate(targets);
    Scope s{std::move(id), "", "", std::move(targets), false};
    reconcile(s);
    scopes_.push_back(std::move(s));
  }
  std::string focused() const { return scopes_.back().focused; }
  std::string scope_id() const { return scopes_.back().id; }
  std::size_t depth() const { return scopes_.size() - 1; }
  const std::vector<FocusTarget> &targets() const {
    return scopes_.back().targets;
  }
  bool focus(const std::string &id) { return set(scopes_.back(), id); }
  std::string move(bool previous = false) {
    auto &s = scopes_.back();
    auto list = ids(s);
    if (list.empty()) {
      s.focused.clear();
      return "";
    }
    auto it = std::find(list.begin(), list.end(), s.focused);
    std::size_t at = it == list.end() ? 0 : it - list.begin();
    auto target = previous           ? (at + list.size() - 1) % list.size()
                  : it == list.end() ? 0
                                     : (at + 1) % list.size();
    s.focused = list[target];
    return s.focused;
  }
  void open(std::string id, std::vector<FocusTarget> targets,
            const std::string &initial = "", bool dismissible = true) {
    if (id.empty() || scopes_.size() >= 65 ||
        std::any_of(scopes_.begin(), scopes_.end(),
                    [&](const Scope &s) { return s.id == id; }))
      throw std::invalid_argument("invalid scope or depth");
    validate(targets);
    Scope s{std::move(id), "", focused(), std::move(targets), dismissible};
    reconcile(s);
    if (!initial.empty() && !set(s, initial))
      throw std::invalid_argument("initial target not focusable");
    scopes_.push_back(std::move(s));
  }
  void update(const std::string &id, std::vector<FocusTarget> targets) {
    validate(targets);
    for (auto &s : scopes_)
      if (s.id == id) {
        s.targets = std::move(targets);
        reconcile(s);
        return;
      }
    throw std::invalid_argument("unknown scope");
  }
  Event close(const std::string &id) {
    if (!depth() || scope_id() != id)
      throw std::invalid_argument("only top popup can close");
    auto restore = scopes_.back().restore;
    scopes_.pop_back();
    if (!set(scopes_.back(), restore))
      reconcile(scopes_.back());
    return {"focus", focused(), ""};
  }
  std::optional<PopupCloseRequest> request_close() const {
    if (depth() && scopes_.back().dismissible)
      return PopupCloseRequest{scope_id(), "escape"};
    return std::nullopt;
  }
  InputRoute route(const std::string &target = "") const {
    return {scope_id(), !target.empty() && target != scope_id()};
  }
  bool blocked(const std::string &scope) const { return route(scope).blocked; }
};
} // namespace tuivory
