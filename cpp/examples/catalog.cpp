#include "container_host.hpp"
#include "dialog_host.hpp"
#include "document_host.hpp"
#include "feedback_host.hpp"
#include "layout_host.hpp"
#include "menu_host.hpp"
#include "surface_host.hpp"
#include "tuivory.hpp"
#include <csignal>
#include <cstdio>
#include <iostream>
#include <poll.h>
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
  explicit Session(bool mouse = false) {
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
    if (mouse)
      std::cout << "\033[?1000h\033[?1006h";
    std::signal(SIGTERM, stop);
    std::signal(SIGINT, stop);
  }
  ~Session() {
    if (active) {
      std::cout << "\033[0m\033[?1000l\033[?1006l\033[?25h\033[?1049l"
                << std::flush;
      tcsetattr(STDIN_FILENO, TCSADRAIN, &saved);
    }
  }
  Session(const Session &) = delete;
  Session &operator=(const Session &) = delete;
};
} // namespace
static void workspace_draw(tuivory::Tree &tree, tuivory::Tabs &tabs,
                           tuivory::Split split, tuivory::Canvas &canvas,
                           tuivory::Rect area, bool tab_focus, bool en,
                           bool ascii) {
  using namespace tuivory;
  tabs.draw(canvas, {area.x, area.y, area.width, 1}, tab_focus, ascii);
  breadcrumbs({{"root", en ? "Workspace" : "작업 공간"},
               {"current", en ? "Components" : "컴포넌트"}},
              area.width)
      .draw(canvas, {area.x, area.y + 1, area.width, 1});
  const int body = std::max(0, area.height - 3);
  auto layout = split.layout(area.width);
  Rect right{area.x, area.y + 2, area.width, body};
  if (!layout.compact) {
    auto left = canvas.panel({area.x, area.y + 2, layout.first, body},
                             en ? "Explorer" : "탐색", !tab_focus, ascii);
    tree.draw(canvas, left, !tab_focus, ascii);
    for (int y = 0; y < body; y++)
      canvas.write(area.x + layout.first, area.y + 2 + y, ascii ? "|" : "│",
                   "focus.border");
    right.x += layout.first + 1;
    right.width = layout.second;
  }
  right = canvas.panel(right, en ? "Content" : "내용", false, ascii);
  canvas.write(right.x, right.y, en ? "Selected tab" : "선택한 탭", "hint",
               false, right.width);
  canvas.write(right.x, right.y + 1,
               (tabs.active == "draft" ? (en ? "Draft" : "초안")
                                       : (en ? "Overview" : "개요")),
               "body", false, right.width);
  status_line({{"ready", en ? "Ready" : "준비", "success", 10},
               {"keys", en ? "Tab focus | < > resize" : "Tab 포커스 | < > 크기",
                "hint", 1}},
              area.width)
      .draw(canvas, {area.x, area.y + area.height - 1, area.width, 1});
}
int main(int argc, char **argv) {
  try {
    using namespace tuivory;
    std::string theme = "dark", colors = "256";
    bool en = false, ascii = false, snapshot = false, ansi_snapshot = false,
         workspace = false, tab_focus = false, text_demo = false,
         form_demo = false, list_demo = false, picker_demo = false,
         menu_demo = false, context_demo = false, feedback_demo = false,
         layout_demo = false, container_demo = false, surface_demo = false,
         shadow_demo = false, dialog_demo = false, document_demo = false;
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
        std::string demo = argv[++i];
        workspace = demo == "workspace";
        text_demo = demo == "text";
        form_demo = demo == "form";
        list_demo = demo == "list";
        picker_demo = demo == "picker";
        context_demo = demo == "context-menu";
        feedback_demo = demo == "feedback";
        layout_demo = demo == "layout";
        container_demo = demo == "container";
        surface_demo = demo == "surface";
        shadow_demo = demo == "shadow";
        dialog_demo = demo == "dialog";
        document_demo = demo == "document";
        if (shadow_demo)
          menu_demo = context_demo = true;
        menu_demo = context_demo || demo == "menu";
        if (demo != "tree" && !workspace && !text_demo && !form_demo &&
            !list_demo && !picker_demo && !menu_demo && !feedback_demo &&
            !layout_demo && !container_demo && !surface_demo && !dialog_demo &&
            !document_demo)
          throw std::invalid_argument(
              "Supported demos: tree, workspace, text, "
              "form, list, picker, menu, context-menu, "
              "feedback, layout, container, surface, shadow, dialog, document");
      } else {
        std::cout << "--demo "
                     "tree|workspace|text|form|list|picker|menu|context-menu|"
                     "feedback|layout|container|surface|shadow|dialog|document "
                     "--lang ko|en "
                     "--theme "
                     "dark|light|blackwhite "
                     "--colors 8|16|256|truecolor --ascii --snapshot\n";
        return arg == "--help" ? 0 : 2;
      }
    }
    MenuDemo menu_host(en, context_demo, shadow_demo);
    FeedbackDemo feedback_host(en);
    LayoutDemo layout_host(en);
    ContainerDemo container_host(en, ascii);
    DocumentDemo document_host(en, ascii);
    DialogDemo dialog_host(en);
    SurfaceDemo surface_host(en);
    Tree tree({{"root", en ? "Workspace" : "작업 공간"},
               {"src", en ? "Sources" : "소스", "root"},
               {"components", en ? "Components" : "컴포넌트", "src"},
               {"tree", en ? "Tree" : "트리", "components"},
               {"leaf", en ? "Fifth level" : "다섯 단계", "tree"},
               {"docs", en ? "Documentation" : "문서", "root"}});
    tree.expanded = {"root", "src", "components", "tree"};
    Tabs tabs(
        {{"overview", en ? "Overview" : "개요"},
         {"draft", en ? "Draft document" : "초안 문서", true, true, false},
         {"disabled", en ? "Disabled" : "비활성", false, false, true}});
    Split split(16, 20, 24);
    Text text(en ? (ascii ? "Grapheme text\nEdit with real cursor."
                          : "Unicode é 界\nEdit with real cursor.")
                 : "한글 é 界\n여러 줄을 편집합니다.");
    Field name;
    name.id = "name";
    name.kind = "text";
    name.label = en ? "Name" : "이름";
    name.value = en ? "Input" : "한글 입력";
    name.required = true;
    Field password;
    password.id = "password";
    password.kind = "password";
    password.label = en ? "Password" : "비밀번호";
    password.value = "example";
    Field off;
    off.id = "off";
    off.kind = "checkbox";
    off.label = en ? "Disabled" : "비활성";
    off.state.disabled = true;
    Field mode;
    mode.id = "mode";
    mode.kind = "select";
    mode.label = en ? "Mode" : "모드";
    mode.choice = "a";
    mode.options = {{"a", en ? "Default" : "기본", false},
                    {"off", en ? "Unavailable" : "사용 불가", true},
                    {"b", en ? "Alternative" : "다른 값", false}};
    Field apply;
    apply.id = "apply";
    apply.kind = "button";
    apply.label = en ? "Apply" : "적용";
    apply.action = "submit";
    Form form({name, password, off, mode, apply});
    std::vector<Item> collection_items;
    Item group;
    group.id = "group";
    group.label = en ? "Languages" : "지원 언어";
    group.separator = true;
    collection_items.push_back(group);
    Item go;
    go.id = "go";
    go.label = "Go";
    go.secondary = en ? "Static package" : "정적 패키지";
    go.icon = "◆";
    go.ascii_icon = "G";
    go.shortcut = "G";
    collection_items.push_back(go);
    Item inactive;
    inactive.id = "off";
    inactive.label = en ? "Disabled" : "비활성";
    inactive.disabled = true;
    collection_items.push_back(inactive);
    Item rs;
    rs.id = "rust";
    rs.label = "Rust";
    rs.secondary = en ? "Independent implementation" : "독립 구현";
    rs.icon = "◆";
    rs.ascii_icon = "R";
    rs.shortcut = "R";
    collection_items.push_back(rs);
    Item doc;
    doc.id = "docs";
    doc.label = en ? "Documentation" : "문서";
    doc.secondary = en ? "Korean and English" : "한글·영어";
    doc.icon = "◇";
    doc.ascii_icon = "D";
    collection_items.push_back(doc);
    List list(collection_items);
    SearchPicker picker(collection_items);
    picker.handle("open");
    list.empty = picker.list.empty = en ? "(empty)" : "항목 없음";
    std::optional<Session> session;
    if (!snapshot)
      session.emplace(menu_demo || feedback_demo || layout_demo ||
                      container_demo || surface_demo || dialog_demo ||
                      document_demo);
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
      if (document_demo)
        document_host.draw(canvas, area, ascii);
      else if (dialog_demo)
        dialog_host.draw(canvas, area, ascii);
      else if (surface_demo)
        surface_host.draw(canvas, area, ascii);
      else if (container_demo)
        container_host.draw(canvas, area, ascii);
      else if (layout_demo)
        layout_host.draw(canvas, area, ascii);
      else if (feedback_demo)
        feedback_host.draw(canvas, area, ascii);
      else if (menu_demo)
        menu_host.draw(canvas, area, ascii);
      else if (list_demo)
        list.draw(canvas, area, true, ascii);
      else if (picker_demo)
        picker.draw(canvas, area, true, ascii);
      else if (form_demo)
        form.draw(canvas, area);
      else if (text_demo)
        text.draw(canvas, area);
      else if (workspace)
        workspace_draw(tree, tabs, split, canvas, area, tab_focus, en, ascii);
      else
        tree.draw(canvas, area, true, ascii);
      const auto hint =
          surface_demo
              ? (en ? "Ctrl+Q quit | s surface" : "Ctrl+Q 종료 | s 바탕 변경")
          : container_demo
              ? (en ? "Ctrl+Q quit | m popup | h/l scroll | Tab focus"
                    : "Ctrl+Q 종료 | m 팝업 | h/l 스크롤 | Tab 포커스")
          : layout_demo
              ? (en ? "Ctrl+Q quit | x/Enter remove filter | d density | click "
                      "x"
                    : "Ctrl+Q 종료 | x/Enter 필터 제거 | d 간격 | x 클릭")
          : feedback_demo
              ? (en ? "Ctrl+Q quit | Enter retry | Del dismiss | t expire | c "
                      "cancel"
                    : "Ctrl+Q 종료 | Enter 재시도 | Del 닫기 | t 만료 | c 취소")
          : menu_demo ? (en ? "Ctrl+Q quit | F10 menu | arrows | Enter | Esc"
                            : "Ctrl+Q 종료 | F10 메뉴 | 방향키 | Enter | Esc")
          : picker_demo
              ? (en ? "Ctrl+Q quit | type to filter | Enter select | Esc cancel"
                    : "Ctrl+Q 종료 | 문자로 검색 | Enter 선택 | Esc 취소")
          : form_demo ? (en ? "Ctrl+Q quit | Tab next | Enter activate | arrows"
                            : "Ctrl+Q 종료 | Tab 이동 | Enter 실행 | 방향키")
          : text_demo ? (en ? "Ctrl+Q quit | type, arrows | Ctrl+Z/Y history"
                            : "Ctrl+Q 종료 | 문자·방향키 | Ctrl+Z/Y 기록")
          : list_demo
              ? (en ? "Ctrl+Q quit | arrows | Enter activate | Space select"
                    : "Ctrl+Q 종료 | 방향키 | Enter 실행 | Space 선택")
          : en ? "Ctrl+Q quit | w/s/a/d navigate | Enter activate"
               : "Ctrl+Q 종료 | w/s/a/d 탐색 | Enter 선택";
      canvas.write(0, height - 1, hint, "hint", false, width);
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
      if (text_demo || form_demo || list_demo || picker_demo || menu_demo ||
          feedback_demo || layout_demo || container_demo || surface_demo ||
          dialog_demo || document_demo) {
        std::string input, edit_action;
        if (key == 27) {
          std::string seq;
          pollfd fd{STDIN_FILENO, POLLIN, 0};
          char next;
          while (seq.size() < 23 && poll(&fd, 1, 30) > 0 &&
                 read(STDIN_FILENO, &next, 1) == 1) {
            seq += next;
            if (next == 17 || next == 3) {
              stopped = 1;
              break;
            }
            if (seq.size() > 1 &&
                ((next >= 'A' && next <= 'Z') || next == 'm' || next == '~'))
              break;
          }
          int button = 0, x = 0, y = 0;
          char ending = 0;
          if ((menu_demo || feedback_demo || layout_demo || container_demo ||
               surface_demo || dialog_demo || document_demo) &&
              std::sscanf(seq.c_str(), "[<%d;%d;%d%c", &button, &x, &y,
                          &ending) == 4) {
            if (ending == 'M' && x > 0 && y > 0) {
              if (document_demo)
                document_host.pointer(x - 1, y - 1, button);
              else if (dialog_demo)
                dialog_host.pointer(x - 1, y - 1, button);
              else if (surface_demo)
                surface_host.pointer(x - 1, y - 1, button);
              else if (container_demo)
                container_host.pointer(x - 1, y - 1, button);
              else if (layout_demo)
                layout_host.pointer(x - 1, y - 1, button);
              else if (feedback_demo)
                feedback_host.pointer(x - 1, y - 1, button);
              else
                menu_host.pointer(x - 1, y - 1, button);
            }
            continue;
          }
          edit_action = seq == "[21~"     ? "f10"
                        : seq == "[21;2~" ? "shift_f10"
                        : seq == "[A"     ? "up"
                        : seq == "[B"     ? "down"
                        : seq == "[C"     ? "right"
                        : seq == "[D"     ? "left"
                        : seq == "[H"     ? "home"
                        : seq == "[F"     ? "end"
                        : seq == "[3~"    ? "delete"
                        : seq.empty()     ? "cancel"
                                          : "";
        } else if (key == 127 || key == 8)
          edit_action = "backspace";
        else if (key == 13 || key == 10)
          edit_action = "newline";
        else if (key == 1)
          edit_action = "select_all";
        else if (key == 26)
          edit_action = "undo";
        else if (key == 25)
          edit_action = "redo";
        else if (key >= 32) {
          input += static_cast<char>(key);
          int n = key < 128 ? 1 : key < 224 ? 2 : key < 240 ? 3 : 4;
          for (int i = 1; i < n; i++) {
            char next;
            if (read(STDIN_FILENO, &next, 1) != 1)
              break;
            input += next;
          }
          edit_action = "insert";
        }
        if (document_demo)
          document_host.handle(
              edit_action == "newline" ? "activate" : edit_action, input);
        else if (dialog_demo)
          dialog_host.handle(key == 9                   ? "next"
                             : edit_action == "newline" ? "activate"
                                                        : edit_action,
                             input);
        else if (surface_demo)
          surface_host.handle(
              edit_action == "newline" ? "activate" : edit_action, input);
        else if (container_demo)
          container_host.handle(key == 9                   ? "next"
                                : edit_action == "newline" ? "activate"
                                                           : edit_action,
                                input);
        else if (layout_demo)
          layout_host.handle(
              edit_action == "newline" ? "activate" : edit_action, input);
        else if (feedback_demo)
          feedback_host.handle(
              edit_action == "newline" ? "activate" : edit_action, input);
        else if (menu_demo)
          menu_host.handle(edit_action == "newline" ? "activate" : edit_action,
                           input);
        else if (list_demo)
          list.handle(key == 27   ? edit_action
                      : key == 32 ? "select"
                                  : action,
                      area.height);
        else if (picker_demo)
          picker.handle(key == 13 || key == 10 ? "activate" : edit_action,
                        input, area.height);
        else if (form_demo)
          form.handle(key == 9                   ? "next"
                      : edit_action == "newline" ? "activate"
                                                 : edit_action,
                      input);
        else
          text.handle(edit_action, input);
      } else if (workspace && key == 9)
        tab_focus = !tab_focus;
      else if (workspace && (key == '<' || key == '>'))
        split.resize(area.width, split.preferred + (key == '<' ? -1 : 1));
      else if (workspace && tab_focus)
        tabs.handle(std::string(action) == "left"    ? "previous"
                    : std::string(action) == "right" ? "next"
                                                     : action);
      else
        tree.handle(action, area.height);
    }
    return 0;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
