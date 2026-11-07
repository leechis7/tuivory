#pragma once
namespace tuivory {
namespace syntax_detail {
#include "tuivory_sql_words.h"
#include "tuivory_syntax_unicode.h"
inline bool alpha(unsigned cp) {
  return detail::range(cp, tui_syntax_alphabetic,
                       sizeof(tui_syntax_alphabetic) /
                           sizeof(*tui_syntax_alphabetic));
}
inline bool number(unsigned cp) {
  return detail::range(cp, tui_syntax_number,
                       sizeof(tui_syntax_number) / sizeof(*tui_syntax_number));
}
inline bool space(unsigned cp) {
  return detail::range(cp, tui_syntax_whitespace,
                       sizeof(tui_syntax_whitespace) /
                           sizeof(*tui_syntax_whitespace));
}
inline bool start(unsigned cp) { return cp == '_' || alpha(cp); }
inline bool part(unsigned cp) {
  return start(cp) || number(cp) || cp == '$' || cp == '#' ||
         (cp >= 0x300 && cp <= 0x36f) || (cp >= 0x1ab0 && cp <= 0x1aff) ||
         (cp >= 0x1dc0 && cp <= 0x1dff) || (cp >= 0x20d0 && cp <= 0x20ff) ||
         (cp >= 0xfe20 && cp <= 0xfe2f);
}
inline unsigned at(const std::string &s, std::size_t pos) {
  return detail::decode(s, pos);
}
inline bool digit(char c) { return c >= '0' && c <= '9'; }
template <std::size_t N>
bool word(const char *const (&words)[N], const std::string &value) {
  return std::find(words, words + N, value) != words + N;
}
inline std::size_t quoted(const std::string &s, std::size_t pos, char quote) {
  pos++;
  while (pos < s.size()) {
    if (s[pos] == quote) {
      pos++;
      if (pos < s.size() && s[pos] == quote) {
        pos++;
        continue;
      }
      return pos;
    }
    pos++;
  }
  return pos;
}
inline std::size_t qprefix(const std::string &s, std::size_t i) {
  auto n = s.size();
  if (i + 2 < n && (s[i] == 'q' || s[i] == 'Q') && s[i + 1] == '\'')
    return 2;
  if (i + 3 < n && (s[i] == 'n' || s[i] == 'N') &&
      (s[i + 1] == 'q' || s[i + 1] == 'Q') && s[i + 2] == '\'')
    return 3;
  return 0;
}
} // namespace syntax_detail
struct SyntaxToken {
  std::size_t start = 0, end = 0;
  std::string role;
};
struct SyntaxRequest {
  std::string language, dialect;
};
struct SyntaxAnalysis {
  std::string source, language, dialect;
  std::vector<SyntaxToken> tokens;
  void validate(const std::string &text) const {
    dialog_detail::text(source, 1000000);
    dialog_detail::text(language, 128);
    dialog_detail::text(dialect, 128);
    if (source != text)
      throw std::invalid_argument("stale syntax source");
    if (tokens.size() > 1000000)
      throw std::invalid_argument("too many syntax tokens");
    std::set<std::size_t> boundaries{0};
    for (std::size_t p = 0; p < text.size();) {
      detail::decode(text, p);
      boundaries.insert(p);
    }
    std::size_t end = 0;
    for (const auto &t : tokens) {
      dialog_detail::text(t.role, 128);
      if (t.start < end || t.end <= t.start || !boundaries.count(t.start) ||
          !boundaries.count(t.end))
        throw std::invalid_argument(
            "unordered, overlapping or invalid UTF-8 syntax range");
      end = t.end;
    }
  }
};
using SyntaxAnalyzer =
    std::function<SyntaxAnalysis(const std::string &, const SyntaxRequest &)>;
inline std::string syntax_role_style(const std::string &role) {
  static const std::map<std::string, std::string> families{
      {"keyword", "keyword"},   {"function", "function"},
      {"macro", "function"},    {"attribute", "function"},
      {"type", "type"},         {"string", "string"},
      {"character", "string"},  {"number", "number"},
      {"constant", "number"},   {"comment", "comment"},
      {"directive", "comment"}, {"parameter", "parameter"},
      {"lifetime", "parameter"}};
  auto it = families.find(role);
  return it == families.end() ? "body" : "syntax." + it->second;
}
inline std::string syntax_palette_role(std::string role) {
  if (role.rfind("syntax.", 0) == 0)
    role = role.substr(7);
  static const std::map<std::string, std::string> families{
      {"keyword", "info"},   {"function", "success"}, {"type", "header"},
      {"string", "warning"}, {"number", "edited"},    {"comment", "hint"},
      {"parameter", "error"}};
  auto it = families.find(role);
  return it == families.end() ? "body" : it->second;
}
inline Style syntax_style(const Palette &palette, std::string role,
                          const std::string &surface = "editor") {
  if (role.rfind("syntax.", 0) == 0)
    role = role.substr(7);
  auto mapped = syntax_palette_role(role);
  auto base = palette.text_on_surface(mapped, surface);
  if (mapped == "body")
    return base;
  auto one = [&](std::initializer_list<const char *> names) {
    return std::any_of(names.begin(), names.end(),
                       [&](const char *s) { return role == s; });
  };
  if (palette.theme() == "blackwhite") {
    base.bold = false;
    base.dim = false;
    base.underline = one({"keyword", "parameter"});
    base.italic = role == "comment";
    return base;
  }
  bool dark = palette.style("surface").background == 0 &&
              palette.style("warning").foreground == 3;
  for (const auto &r : detail::tui_roles) {
    auto s = palette.style(r);
    dark = dark && s.foreground <= 7 && s.background <= 7;
  }
  if (dark) {
    unsigned foreground =
        one({"keyword", "function", "string", "parameter"}) ? 3 : 7;
    if (color_contrast(foreground, base.background) < 4.5 &&
        color_contrast(base.foreground, base.background) >
            color_contrast(foreground, base.background))
      foreground = base.foreground;
    base.foreground = foreground;
    base.bold = one({"keyword", "number"});
    base.dim = false;
    base.underline = one({"keyword", "type", "parameter"});
    base.italic = one({"string", "comment"});
  }
  return base;
}
namespace syntax_detail {
struct Binding {
  SyntaxAnalyzer analyzer;
  SyntaxRequest request;
  std::string source;
  bool dirty = false;
  std::optional<std::string> error;
  bool refreshing = false;
};
} // namespace syntax_detail
/** Independent optional SQL/PLSQL highlighting classifier, never an SQL
 * executor. */
class SQLAnalyzer {
public:
  SyntaxAnalysis analyze_syntax(const std::string &text,
                                SyntaxRequest request = {}) const {
    dialog_detail::text(text, 1000000);
    dialog_detail::text(request.language, 128);
    dialog_detail::text(request.dialect, 128);
    auto lower = [](std::string s) {
      for (auto &c : s)
        if (c >= 'A' && c <= 'Z')
          c += 32;
      return s;
    };
    std::string language =
                    request.language.empty() ? "sql" : lower(request.language),
                dialect =
                    request.dialect.empty() ? "oracle" : lower(request.dialect);
    if ((language != "sql" && language != "plsql") || dialect != "oracle")
      throw std::invalid_argument("unsupported syntax language/dialect");
    std::vector<SyntaxToken> raw;
    std::size_t i = 0, n = text.size();
    while (i < n) {
      auto start = i;
      auto cp = syntax_detail::at(text, i);
      if (syntax_detail::space(cp)) {
        detail::decode(text, i);
        continue;
      }
      std::string role = "punctuation";
      auto prefix = syntax_detail::qprefix(text, i);
      if (text.compare(i, 2, "--") == 0) {
        role = "comment";
        i += 2;
        while (i < n && text[i] != '\r' && text[i] != '\n')
          i++;
      } else if (text.compare(i, 2, "/*") == 0) {
        role = "comment";
        auto end = text.find("*/", i + 2);
        i = end == std::string::npos ? n : end + 2;
      } else if (prefix) {
        role = "string";
        i += prefix;
        if (i < n) {
          auto after = i;
          auto open = detail::decode(text, after);
          if (!syntax_detail::space(open)) {
            std::string close = open == '['   ? "]"
                                : open == '{' ? "}"
                                : open == '(' ? ")"
                                : open == '<' ? ">"
                                              : text.substr(i, after - i);
            auto ending = close + "'";
            auto end = text.find(ending, after);
            i = end == std::string::npos ? n : end + ending.size();
          } else {
            i = start;
            detail::decode(text, i);
            role = "identifier";
          }
        }
      } else if (cp == '\'' || ((cp == 'n' || cp == 'N') && i + 1 < n &&
                                text[i + 1] == '\'')) {
        role = "string";
        i = syntax_detail::quoted(text, i + (cp == '\'' ? 0 : 1), '\'');
      } else if (cp == '"') {
        role = "identifier";
        i = syntax_detail::quoted(text, i, '"');
      } else if (cp == ':' && i + 1 < n &&
                 (syntax_detail::start(syntax_detail::at(text, i + 1)) ||
                  syntax_detail::digit(text[i + 1]) || text[i + 1] == '"')) {
        role = "parameter";
        i++;
        if (text[i] == '"')
          i = syntax_detail::quoted(text, i, '"');
        else
          while (i < n && syntax_detail::part(syntax_detail::at(text, i)))
            detail::decode(text, i);
      } else if (text.compare(i, 2, "..") == 0) {
        role = "operator";
        i += 2;
      } else if ((cp < 128 && syntax_detail::digit(static_cast<char>(cp))) ||
                 (cp == '.' && i + 1 < n &&
                  syntax_detail::digit(text[i + 1]))) {
        role = "number";
        while (i < n && syntax_detail::digit(text[i]))
          i++;
        if (i < n && text[i] == '.' && text.compare(i, 2, "..") != 0) {
          i++;
          while (i < n && syntax_detail::digit(text[i]))
            i++;
        }
        if (i < n && (text[i] == 'e' || text[i] == 'E')) {
          auto end = i + 1;
          if (end < n && (text[end] == '+' || text[end] == '-'))
            end++;
          auto first = end;
          while (end < n && syntax_detail::digit(text[end]))
            end++;
          if (end > first)
            i = end;
        }
        if (i < n && (text[i] == 'f' || text[i] == 'F' || text[i] == 'd' ||
                      text[i] == 'D'))
          i++;
      } else if (syntax_detail::start(cp)) {
        detail::decode(text, i);
        while (i < n && syntax_detail::part(syntax_detail::at(text, i)))
          detail::decode(text, i);
        auto word = text.substr(start, i - start);
        for (auto &c : word)
          if (c >= 'a' && c <= 'z')
            c -= 32;
        role = syntax_detail::word(syntax_detail::tui_sql_types, word) ? "type"
               : syntax_detail::word(syntax_detail::tui_sql_functions, word)
                   ? "function"
               : syntax_detail::word(syntax_detail::tui_sql_keywords, word)
                   ? "keyword"
                   : "identifier";
      } else {
        detail::decode(text, i);
        if (cp < 128 &&
            std::string("+-*/%=<>!|:^~").find(static_cast<char>(cp)) !=
                std::string::npos) {
          role = "operator";
          if (i < n) {
            auto pair = text.substr(start, i + 1 - start);
            if (pair == ":=" || pair == "=>" || pair == "<=" || pair == ">=" ||
                pair == "!=" || pair == "<>" || pair == "||" || pair == "**")
              i++;
          }
        }
      }
      raw.push_back({start, i, role});
    }
    std::vector<SyntaxToken> tokens;
    std::size_t offset = 0, which = 0, previous = static_cast<std::size_t>(-1);
    for (const auto &g : graphemes(text)) {
      auto end = offset + g.text.size();
      while (which < raw.size() && raw[which].end <= offset)
        which++;
      if (which < raw.size() && raw[which].start < end) {
        if (previous == which && !tokens.empty() && tokens.back().end == offset)
          tokens.back().end = end;
        else
          tokens.push_back({offset, end, raw[which].role});
        previous = which;
      } else
        previous = static_cast<std::size_t>(-1);
      offset = end;
    }
    return {text, language, dialect, tokens};
  }
  SyntaxAnalysis operator()(const std::string &text,
                            const SyntaxRequest &request) const {
    return analyze_syntax(text, request);
  }
};
} // namespace tuivory
