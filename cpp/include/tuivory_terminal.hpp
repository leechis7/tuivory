#pragma once
#include <cerrno>
#include <chrono>
#include <cstring>
#include <string_view>
#if defined(__unix__) || defined(__APPLE__)
#include <poll.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>
#endif
namespace tuivory {
struct InputEvent {
  std::string key, text;
  int x = 0, y = 0, button = 0;
};
class InputDecoder {
  std::string buffer_, paste_;
  std::size_t offset_ = 0;
  bool pasting_ = false, rejected_ = false;
  static constexpr std::size_t limit_ = 16 * 1024 * 1024;
  void consume(std::size_t n) {
    offset_ += n;
    if (offset_ >= buffer_.size()) {
      buffer_.clear();
      offset_ = 0;
    } else if (offset_ > 4096 && offset_ > buffer_.size() / 2) {
      buffer_.erase(0, offset_);
      offset_ = 0;
    }
  }

public:
  void feed(const std::string &bytes) {
    if (bytes.size() > limit_ + 64 ||
        buffer_.size() - offset_ > limit_ + 64 - bytes.size()) {
      buffer_.clear();
      paste_.clear();
      offset_ = 0;
      pasting_ = false;
      rejected_ = true;
      return;
    }
    buffer_ += bytes;
  }
  bool waiting_escape() const {
    return !pasting_ && offset_ < buffer_.size() && buffer_[offset_] == 27;
  }
  std::optional<InputEvent> next(bool flush_escape = false) {
    if (rejected_) {
      rejected_ = false;
      return InputEvent{"paste_rejected", ""};
    }
    std::string_view b(buffer_.data() + offset_, buffer_.size() - offset_);
    if (pasting_) {
      auto end = b.find("\033[201~");
      auto count = end == b.npos ? (b.size() > 5 ? b.size() - 5 : 0) : end;
      if (paste_.size() + count > limit_) {
        buffer_.clear();
        offset_ = 0;
        paste_.clear();
        pasting_ = false;
        return InputEvent{"paste_rejected", ""};
      }
      paste_.append(b.data(), count);
      consume(count);
      if (end == b.npos)
        return std::nullopt;
      consume(6);
      pasting_ = false;
      auto raw = std::move(paste_);
      paste_.clear();
      std::string text;
      for (std::size_t pos = 0; pos < raw.size();) {
        auto start = pos;
        try {
          detail::decode(raw, pos);
          text.append(raw, start, pos - start);
        } catch (const std::invalid_argument &) {
          text += "\xef\xbf\xbd";
          pos = start + 1;
        }
      }
      return InputEvent{"paste", std::move(text)};
    }
    if (b.empty())
      return std::nullopt;
    if (b.substr(0, 6) == "\033[200~") {
      consume(6);
      pasting_ = true;
      paste_.clear();
      return next(flush_escape);
    }
    static const std::vector<std::pair<std::string_view, std::string_view>>
        keys{{"\033[A", "up"},       {"\033[B", "down"},
             {"\033[C", "right"},    {"\033[D", "left"},
             {"\033[H", "home"},     {"\033[F", "end"},
             {"\033[5~", "page_up"}, {"\033[6~", "page_down"},
             {"\033[3~", "delete"},  {"\033[Z", "shift_tab"},
             {"\033OP", "f1"},       {"\033OQ", "f2"},
             {"\033[21~", "f10"},    {"\033[21;2~", "shift_f10"}};
    if (b.substr(0, 3) == "\033[<") {
      auto end = b.find_first_of("Mm", 3);
      if (end != b.npos) {
        long long values[3] = {0, 0, 0};
        int field = 0;
        bool valid = true, digits = false;
        for (std::size_t i = 3; i < end; i++) {
          char c = b[i];
          if (c == ';' && field < 2 && digits) {
            field++;
            digits = false;
          } else if (c >= '0' && c <= '9') {
            digits = true;
            values[field] = values[field] * 10 + c - '0';
            if (values[field] > 1000000001) {
              valid = false;
              break;
            }
          } else {
            valid = false;
            break;
          }
        }
        bool release = b[end] == 'm';
        consume(end + 1);
        if (!valid || !digits || field != 2 || values[0] > 1000000000 ||
            values[1] < 1 || values[2] < 1)
          return InputEvent{"unknown", ""};
        int button = (int)values[0];
        return InputEvent{release       ? "mouse_release"
                          : button & 64 ? "wheel"
                          : button & 32 ? "mouse_move"
                                        : "mouse",
                          "", (int)values[1] - 1, (int)values[2] - 1, button};
      }
    }
    for (const auto &key : keys)
      if (b.substr(0, key.first.size()) == key.first) {
        auto event = InputEvent{std::string(key.second), ""};
        consume(key.first.size());
        return event;
      }
    if (b[0] == 27) {
      bool incomplete = std::string_view("\033[200~").substr(0, b.size()) == b;
      for (const auto &key : keys)
        incomplete = incomplete || key.first.substr(0, b.size()) == b;
      incomplete = incomplete || (b.substr(0, 3) == "\033[<" &&
                                  b.find_first_of("Mm") == b.npos);
      if (incomplete && !flush_escape)
        return std::nullopt;
      if (b.size() > 1 && b[1] == '[') {
        for (std::size_t i = 2; i < b.size(); i++)
          if (b[i] >= 0x40 && b[i] <= 0x7e) {
            consume(i + 1);
            return InputEvent{"unknown", ""};
          }
      }
      consume(1);
      return InputEvent{"escape", ""};
    }
    unsigned first = (unsigned char)b[0];
    if (first < 32 || first == 127) {
      std::string key = first == 9                   ? "tab"
                        : first == 10 || first == 13 ? "enter"
                        : first == 8 || first == 127
                            ? "backspace"
                            : std::string("ctrl_") + char(first + 96);
      consume(1);
      return InputEvent{key, ""};
    }
    int n = first < 128                      ? 1
            : first >= 0xc2 && first <= 0xdf ? 2
            : first >= 0xe0 && first <= 0xef ? 3
            : first >= 0xf0 && first <= 0xf4 ? 4
                                             : 0;
    if (!n) {
      consume(1);
      return InputEvent{"text", "\xef\xbf\xbd"};
    }
    if (b.size() < std::size_t(n))
      return std::nullopt;
    unsigned cp = first & (n == 1 ? 127 : n == 2 ? 31 : n == 3 ? 15 : 7);
    bool valid = true;
    for (int i = 1; i < n; i++) {
      unsigned c = (unsigned char)b[i];
      if ((c & 0xc0) != 0x80) {
        valid = false;
        break;
      }
      cp = (cp << 6) | (c & 63);
    }
    if (!valid || cp > 0x10ffff || (cp >= 0xd800 && cp <= 0xdfff) ||
        (n == 2 && cp < 128) || (n == 3 && cp < 2048) ||
        (n == 4 && cp < 65536)) {
      consume(1);
      return InputEvent{"text", "\xef\xbf\xbd"};
    }
    auto text = std::string(b.substr(0, n));
    consume(n);
    return InputEvent{"text", text};
  }
};
struct TerminalOptions {
  bool mouse = true, mouse_motion = false;
};
/** Optional POSIX session. Hosts own signals/global keys; read is bounded. */
class Terminal {
  int input_, output_;
  bool active_ = false, closed_ = false, eof_ = false;
  TerminalOptions options_;
  InputDecoder decoder_;
  std::pair<int, int> size_{80, 24};
  std::chrono::steady_clock::time_point escape_at_{};
#if defined(__unix__) || defined(__APPLE__)
  termios saved_{};
  void output(const std::string &s) {
    std::size_t i = 0;
    while (i < s.size()) {
      auto n = ::write(output_, s.data() + i, s.size() - i);
      if (n < 0 && errno == EINTR)
        continue;
      if (n <= 0)
        throw std::runtime_error("terminal output failed");
      i += std::size_t(n);
    }
  }
#endif
public:
  explicit Terminal(TerminalOptions options = {}, int input = 0, int output = 1)
      : input_(input), output_(output), options_(options) {}
  Terminal(const Terminal &) = delete;
  Terminal &operator=(const Terminal &) = delete;
  ~Terminal() {
    try {
      close();
    } catch (...) {
    }
  }
  std::pair<int, int> size() const {
#if defined(__unix__) || defined(__APPLE__)
    winsize ws{};
    if (ioctl(output_, TIOCGWINSZ, &ws) == 0 && ws.ws_col && ws.ws_row)
      return {ws.ws_col, ws.ws_row};
#endif
    return {80, 24};
  }
  void open() {
    if (active_ || closed_)
      throw std::runtime_error("Terminal session cannot be reopened");
#if defined(__unix__) || defined(__APPLE__)
    if (!isatty(input_) || !isatty(output_) || tcgetattr(input_, &saved_))
      throw std::runtime_error("interactive Terminal requires a POSIX TTY");
    auto raw = saved_;
    raw.c_iflag &=
        ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON);
    raw.c_oflag &= ~OPOST;
    raw.c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
    raw.c_cflag = (raw.c_cflag & ~(CSIZE | PARENB)) | CS8;
    raw.c_cc[VMIN] = 0;
    raw.c_cc[VTIME] = 0;
    if (tcsetattr(input_, TCSADRAIN, &raw))
      throw std::runtime_error("terminal raw mode failed");
    active_ = true;
    size_ = size();
    try {
      output(std::string("\033[?1049h\033[?2004h") +
             (options_.mouse
                  ? (options_.mouse_motion ? "\033[?1002h\033[?1006h"
                                           : "\033[?1000h\033[?1006h")
                  : ""));
    } catch (...) {
      try {
        close();
      } catch (...) {
      }
      throw;
    }
#else
    throw std::runtime_error("interactive Terminal requires POSIX");
#endif
  }
  void write(const std::string &s) {
    if (!active_)
      throw std::runtime_error("Terminal is closed");
#if defined(__unix__) || defined(__APPLE__)
    output(s);
#else
    (void)s;
#endif
  }
  void close() {
    if (!active_)
      return;
    active_ = false;
    closed_ = true;
#if defined(__unix__) || defined(__APPLE__)
    try {
      output("\033[0m\033[?1000l\033[?1002l\033[?1006l\033[?2004l\033[?25h\033["
             "?1049l");
    } catch (...) {
      tcsetattr(input_, TCSADRAIN, &saved_);
      throw;
    }
    if (tcsetattr(input_, TCSADRAIN, &saved_))
      throw std::runtime_error("terminal restoration failed");
#endif
  }
  std::optional<InputEvent> read(int timeout_ms = 100) {
    if (timeout_ms < 0 || timeout_ms > 3600000)
      throw std::invalid_argument("invalid terminal timeout");
    if (!active_)
      return InputEvent{"eof", ""};
#if defined(__unix__) || defined(__APPLE__)
    using Clock = std::chrono::steady_clock;
    auto deadline = Clock::now() + std::chrono::milliseconds(timeout_ms);
    for (;;) {
      auto current = size();
      if (current != size_) {
        size_ = current;
        return InputEvent{"resize", "", current.first, current.second};
      }
      auto now = Clock::now();
      bool flush = decoder_.waiting_escape() &&
                   now - escape_at_ >= std::chrono::milliseconds(100);
      auto event = decoder_.next(flush);
      if (event) {
        if (decoder_.waiting_escape())
          escape_at_ = now;
        return event;
      }
      if (eof_)
        return InputEvent{"eof", ""};
      int remaining = std::max(
          0, (int)std::chrono::duration_cast<std::chrono::milliseconds>(
                 deadline - now)
                 .count());
      if (decoder_.waiting_escape())
        remaining = std::min(
            remaining,
            std::max(
                1,
                100 -
                    (int)std::chrono::duration_cast<std::chrono::milliseconds>(
                        now - escape_at_)
                        .count()));
      pollfd fd{input_, POLLIN, 0};
      int ready = poll(&fd, 1, remaining);
      if (ready < 0) {
        if (errno == EINTR) {
          if (Clock::now() >= deadline)
            return std::nullopt;
          continue;
        }
        throw std::runtime_error("terminal poll failed");
      }
      if (!ready) {
        auto e = decoder_.next(decoder_.waiting_escape() &&
                               Clock::now() - escape_at_ >=
                                   std::chrono::milliseconds(100));
        return e;
      }
      char bytes[8192];
      auto n = ::read(input_, bytes, sizeof(bytes));
      if (n < 0) {
        if (errno == EINTR)
          continue;
        throw std::runtime_error("terminal input failed");
      }
      if (n == 0)
        eof_ = true;
      else {
        if (!decoder_.waiting_escape())
          escape_at_ = Clock::now();
        decoder_.feed(std::string(bytes, std::size_t(n)));
      }
    }
#endif
    return std::nullopt;
  }
};
} // namespace tuivory
