#include "tuivory.hpp"
#include <csignal>
#include <iostream>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>
namespace {
volatile std::sig_atomic_t stopped = 0;
void stop(int) { stopped = 1; }
class Session {
  termios saved{};
  bool active = false;

public:
  Session() {
    if (!isatty(STDIN_FILENO) || !isatty(STDOUT_FILENO) ||
        tcgetattr(STDIN_FILENO, &saved))
      throw std::runtime_error(
          "Interactive demo requires a POSIX TTY; use --snapshot");
    auto raw = saved;
    raw.c_lflag &= ~(ICANON | ECHO | ISIG);
    raw.c_iflag &= ~(IXON | ICRNL);
    raw.c_cc[VMIN] = 1;
    raw.c_cc[VTIME] = 0;
    if (tcsetattr(STDIN_FILENO, TCSADRAIN, &raw))
      throw std::runtime_error("raw terminal failed");
    active = true;
    std::cout << "\033[?1049h";
    std::signal(SIGTERM, stop);
    std::signal(SIGINT, stop);
  }
  ~Session() {
    if (active) {
      std::cout << "\033[0m\033[?25h\033[?1049l" << std::flush;
      tcsetattr(STDIN_FILENO, TCSADRAIN, &saved);
    }
  }
  Session(const Session &) = delete;
  Session &operator=(const Session &) = delete;
};
} // namespace
int main(int argc, char **argv) {
  try {
    using namespace tuivory;
    std::string theme = "dark", colors = "256";
    bool en = false, ascii = false, snapshot = false, ansi_snapshot = false;
    for (int i = 1; i < argc; i++) {
      std::string arg = argv[i];
      if (arg == "--lang" && i + 1 < argc)
        en = std::string(argv[++i]) == "en";
      else if (arg == "--theme" && i + 1 < argc)
        theme = argv[++i];
      else if (arg == "--colors" && i + 1 < argc)
        colors = argv[++i];
      else if (arg == "--ascii")
        ascii = true;
      else if (arg == "--snapshot")
        snapshot = true;
      else if (arg == "--snapshot-ansi") {
        snapshot = true;
        ansi_snapshot = true;
      } else if (arg == "--demo" && i + 1 < argc) {
        if (std::string(argv[++i]) != "tree")
          throw std::invalid_argument("Only --demo tree is supported");
      } else {
        std::cout << "--demo tree --lang ko|en --theme dark|light|blackwhite "
                     "--colors 8|16|256|truecolor --ascii --snapshot\n";
        return arg == "--help" ? 0 : 2;
      }
    }
    Tree tree({{"root", en ? "Workspace" : "작업 공간"},
               {"src", en ? "Sources" : "소스", "root"},
               {"components", en ? "Components" : "컴포넌트", "src"},
               {"tree", en ? "Tree" : "트리", "components"},
               {"leaf", en ? "Fifth level" : "다섯 단계", "tree"},
               {"docs", en ? "Documentation" : "문서", "root"}});
    tree.expanded = {"root", "src", "components", "tree"};
    std::optional<Session> session;
    if (!snapshot)
      session.emplace();
    while (!stopped) {
      int width = 72, height = 18;
      winsize size{};
      if (!snapshot && ioctl(STDOUT_FILENO, TIOCGWINSZ, &size) == 0 &&
          size.ws_col && size.ws_row) {
        width = size.ws_col;
        height = size.ws_row;
      }
      Canvas canvas(width, height, Palette(theme, colors));
      auto area = canvas.panel({0, 0, width, std::max(0, height - 1)},
                               en ? "Tuivory C++ example" : "Tuivory C++ 예제",
                               true, ascii);
      tree.draw(canvas, area, true, ascii);
      canvas.write(0, height - 1,
                   en ? "Ctrl+Q quit | w/s/a/d navigate | Enter activate"
                      : "Ctrl+Q 종료 | w/s/a/d 탐색 | Enter 선택",
                   "hint", false, width);
      if (snapshot) {
        if (ansi_snapshot)
          std::cout << canvas.ansi();
        else
          for (const auto &line : canvas.lines())
            std::cout << line << '\n';
        break;
      }
      std::cout << canvas.ansi() << std::flush;
      unsigned char key;
      if (read(STDIN_FILENO, &key, 1) != 1)
        break;
      if (key == 17 || key == 3)
        break;
      const auto action = key == 'w'                   ? "up"
                          : key == 's'                 ? "down"
                          : key == 'a'                 ? "left"
                          : key == 'd'                 ? "right"
                          : key == '\r' || key == '\n' ? "activate"
                          : key == ' '                 ? "toggle"
                                                       : "";
      tree.handle(action, area.height);
    }
    return 0;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
