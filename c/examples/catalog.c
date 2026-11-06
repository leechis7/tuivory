#define _POSIX_C_SOURCE 200809L
#include "menu_host.h"
#include "tuivory.h"
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>

static struct termios saved;
static int active;
static volatile sig_atomic_t stopped;
static void stop_signal(int signal_number) {
  (void)signal_number;
  stopped = 1;
}
static void restore(void) {
  if (active) {
    fputs("\033[0m\033[?1000l\033[?1006l\033[?25h\033[?1049l", stdout);
    fflush(stdout);
    tcsetattr(STDIN_FILENO, TCSADRAIN, &saved);
    active = 0;
  }
}
static void workspace_draw(TuiTree *tree, TuiTabs *tabs, TuiSplit split,
                           TuiCanvas *canvas, TuiRect area, int tab_focus,
                           int en, int ascii) {
  TuiPathItem path[] = {{"root", en ? "Workspace" : "작업 공간"},
                        {"current", en ? "Components" : "컴포넌트"}};
  TuiStatusItem state[] = {
      {"ready", en ? "Ready" : "준비", "success", 10},
      {"keys", en ? "Tab focus | < > resize" : "Tab 포커스 | < > 크기", "hint",
       1}};
  tui_tabs_draw(tabs, canvas, (TuiRect){area.x, area.y, area.width, 1},
                tab_focus);
  TuiLine *line = tui_breadcrumbs(path, 2, area.width);
  if (line) {
    tui_line_draw(line, canvas, (TuiRect){area.x, area.y + 1, area.width, 1});
    tui_line_free(line);
  }
  int body = area.height > 3 ? area.height - 3 : 0;
  TuiSplitLayout layout = tui_split_layout(split, area.width);
  TuiRect right = {area.x, area.y + 2, area.width, body};
  if (!layout.compact) {
    TuiRect left = tui_canvas_panel(
        canvas, (TuiRect){area.x, area.y + 2, layout.first, body},
        en ? "Explorer" : "탐색", !tab_focus, ascii);
    tui_tree_draw(tree, canvas, left, !tab_focus, ascii);
    for (int y = 0; y < body; y++)
      tui_canvas_write(canvas, area.x + layout.first, area.y + 2 + y,
                       ascii ? "|" : "│", "focus.border", 0, 1);
    right.x += layout.first + 1;
    right.width = layout.second;
  }
  right = tui_canvas_panel(canvas, right, en ? "Content" : "내용", 0, ascii);
  tui_canvas_write(canvas, right.x, right.y, en ? "Selected tab" : "선택한 탭",
                   "hint", 0, right.width);
  tui_canvas_write(canvas, right.x, right.y + 1,
                   (!strcmp(tui_tabs_active(tabs), "draft")
                        ? (en ? "Draft" : "초안")
                        : (en ? "Overview" : "개요")),
                   "body", 0, right.width);
  line = tui_status_line(state, 2, area.width);
  if (line) {
    tui_line_draw(line, canvas,
                  (TuiRect){area.x, area.y + area.height - 1, area.width, 1});
    tui_line_free(line);
  }
}
int main(int argc, char **argv) {
  const char *theme = "dark", *profile = "256";
  int en = 0, ascii = 0, snapshot = 0, workspace = 0, tab_focus = 0,
      text_demo = 0, form_demo = 0, list_demo = 0, picker_demo = 0,
      menu_demo = 0, context_demo = 0;
  TuiSplit split = {24, 16, 20};
  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "--lang") && i + 1 < argc)
      en = !strcmp(argv[++i], "en");
    else if (!strcmp(argv[i], "--theme") && i + 1 < argc)
      theme = argv[++i];
    else if (!strcmp(argv[i], "--colors") && i + 1 < argc)
      profile = argv[++i];
    else if (!strcmp(argv[i], "--ascii"))
      ascii = 1;
    else if (!strcmp(argv[i], "--snapshot"))
      snapshot = 1;
    else if (!strcmp(argv[i], "--snapshot-ansi"))
      snapshot = 2;
    else if (!strcmp(argv[i], "--demo") && i + 1 < argc) {
      const char *demo = argv[++i];
      workspace = !strcmp(demo, "workspace");
      text_demo = !strcmp(demo, "text");
      form_demo = !strcmp(demo, "form");
      list_demo = !strcmp(demo, "list");
      picker_demo = !strcmp(demo, "picker");
      context_demo = !strcmp(demo, "context-menu");
      menu_demo = context_demo || !strcmp(demo, "menu");
      if (strcmp(demo, "tree") && !workspace && !text_demo && !form_demo &&
          !list_demo && !picker_demo && !menu_demo) {
        fputs("Supported demos: tree, workspace, text, form, list, picker, "
              "menu, context-menu\n",
              stderr);
        return 2;
      }
    } else {
      puts("--demo tree|workspace|text|form|list|picker|menu|context-menu "
           "--lang ko|en --theme "
           "dark|light|blackwhite "
           "--colors "
           "8|16|256|truecolor --ascii --snapshot");
      return !strcmp(argv[i], "--help") ? 0 : 2;
    }
  }
  MenuDemo menu_host;
  if (!menu_demo_init(&menu_host, en, context_demo))
    return 1;
  TuiNode nodes[] = {
      {.id = "root", .name = en ? "Workspace" : "작업 공간"},
      {.id = "src", .name = en ? "Sources" : "소스", .parent = "root"},
      {.id = "components",
       .name = en ? "Components" : "컴포넌트",
       .parent = "src"},
      {.id = "tree", .name = en ? "Tree" : "트리", .parent = "components"},
      {.id = "leaf",
       .name = en ? "Fifth level" : "다섯 단계",
       .parent = "tree"},
      {.id = "docs", .name = en ? "Documentation" : "문서", .parent = "root"}};
  TuiTree *tree = tui_tree_new(nodes, 6);
  if (!tree)
    return 1;
  tui_tree_handle(tree, "right", 12);
  tui_tree_handle(tree, "down", 12);
  tui_tree_handle(tree, "right", 12);
  tui_tree_handle(tree, "down", 12);
  tui_tree_handle(tree, "right", 12);
  tui_tree_handle(tree, "down", 12);
  tui_tree_handle(tree, "right", 12);
  tui_tree_handle(tree, "home", 12);
  TuiTab tab_items[] = {{"overview", en ? "Overview" : "개요", 0, 0, 0},
                        {"draft", en ? "Draft document" : "초안 문서", 1, 1, 0},
                        {"disabled", en ? "Disabled" : "비활성", 0, 0, 1}};
  TuiTabs *tabs = tui_tabs_new(tab_items, 3);
  if (!tabs) {
    tui_tabs_free(tabs);
    tui_tree_free(tree);
    return 1;
  }
  TuiText *text =
      tui_text_new(en ? (ascii ? "Grapheme text\nEdit with real cursor."
                               : "Unicode é 界\nEdit with real cursor.")
                      : "한글 é 界\n여러 줄을 편집합니다.");
  if (!text) {
    tui_tabs_free(tabs);
    tui_tree_free(tree);
    return 1;
  }
  TuiFormOption choices[] = {{"a", en ? "Default" : "기본", 0},
                             {"off", en ? "Unavailable" : "사용 불가", 1},
                             {"b", en ? "Alternative" : "다른 값", 0}};
  TuiField fields[] = {{.id = "name",
                        .kind = "text",
                        .label = en ? "Name" : "이름",
                        .value = en ? "Input" : "한글 입력",
                        .required = 1},
                       {.id = "password",
                        .kind = "password",
                        .label = en ? "Password" : "비밀번호",
                        .value = "example"},
                       {.id = "off",
                        .kind = "checkbox",
                        .label = en ? "Disabled" : "비활성",
                        .state = {.disabled = 1}},
                       {.id = "mode",
                        .kind = "select",
                        .label = en ? "Mode" : "모드",
                        .choice = "a",
                        .options = choices,
                        .option_count = 3},
                       {.id = "apply",
                        .kind = "button",
                        .label = en ? "Apply" : "적용",
                        .action = "submit"}};
  TuiForm *form = tui_form_new(fields, 5);
  if (!form) {
    tui_text_free(text);
    tui_tabs_free(tabs);
    tui_tree_free(tree);
    return 1;
  }
  TuiItem collection_items[] = {
      {.id = "group", .label = en ? "Languages" : "지원 언어", .separator = 1},
      {.id = "go",
       .label = "Go",
       .secondary = en ? "Static package" : "정적 패키지",
       .icon = "◆",
       .ascii_icon = "G",
       .shortcut = "G"},
      {.id = "off", .label = en ? "Disabled" : "비활성", .disabled = 1},
      {.id = "rust",
       .label = "Rust",
       .secondary = en ? "Independent implementation" : "독립 구현",
       .icon = "◆",
       .ascii_icon = "R",
       .shortcut = "R"},
      {.id = "docs",
       .label = en ? "Documentation" : "문서",
       .secondary = en ? "Korean and English" : "한글·영어",
       .icon = "◇",
       .ascii_icon = "D"}};
  TuiList *list = tui_list_new(collection_items, 5);
  TuiSearchPicker *picker = tui_picker_new(collection_items, 5);
  if (!list || !picker) {
    tui_list_free(list);
    tui_picker_free(picker);
    tui_form_free(form);
    tui_text_free(text);
    tui_tabs_free(tabs);
    tui_tree_free(tree);
    return 1;
  }
  tui_list_empty(list, en ? "(empty)" : "항목 없음");
  tui_list_empty(tui_picker_list(picker), en ? "(empty)" : "항목 없음");
  tui_picker_handle(picker, "open", "", 10);
  if (!snapshot) {
    if (!isatty(STDIN_FILENO) || !isatty(STDOUT_FILENO) ||
        tcgetattr(STDIN_FILENO, &saved)) {
      tui_tabs_free(tabs);
      tui_tree_free(tree);
      fputs("Interactive demo requires a POSIX TTY; use --snapshot\n", stderr);
      return 1;
    }
    struct termios raw = saved;
    raw.c_lflag &= ~(ICANON | ECHO | ISIG);
    raw.c_iflag &= ~(IXON | ICRNL);
    raw.c_cc[VMIN] = 1;
    raw.c_cc[VTIME] = 0;
    atexit(restore);
    active = 1;
    if (tcsetattr(STDIN_FILENO, TCSADRAIN, &raw)) {
      restore();
      tui_tabs_free(tabs);
      tui_tree_free(tree);
      return 1;
    }
    fputs("\033[?1049h", stdout);
    if (menu_demo)
      fputs("\033[?1000h\033[?1006h", stdout);
    signal(SIGTERM, stop_signal);
    signal(SIGINT, stop_signal);
  }
  while (!stopped) {
    struct winsize size = {0};
    int width = 72, height = 18;
    if (!snapshot && ioctl(STDOUT_FILENO, TIOCGWINSZ, &size) == 0 &&
        size.ws_col && size.ws_row) {
      width = size.ws_col;
      height = size.ws_row;
    }
    TuiCanvas *canvas = tui_canvas_new(width, height, theme, profile);
    if (!canvas) {
      restore();
      tui_tabs_free(tabs);
      tui_tree_free(tree);
      return 1;
    }
    TuiRect inner = tui_canvas_panel(
        canvas, (TuiRect){0, 0, width, height > 0 ? height - 1 : 0},
        en ? "Tuivory C example" : "Tuivory C 예제", 1, ascii);
    if (menu_demo)
      menu_demo_draw(&menu_host, canvas, inner, ascii);
    else if (list_demo)
      tui_list_draw(list, canvas, inner, 1, ascii);
    else if (picker_demo)
      tui_picker_draw(picker, canvas, inner, 1, ascii);
    else if (form_demo)
      tui_form_draw(form, canvas, inner, 1);
    else if (text_demo)
      tui_text_draw(text, canvas, inner, 1);
    else if (workspace)
      workspace_draw(tree, tabs, split, canvas, inner, tab_focus, en, ascii);
    else
      tui_tree_draw(tree, canvas, inner, 1, ascii);
    const char *hint =
        menu_demo ? (en ? "Ctrl+Q quit | F10 menu | arrows | Enter | Esc"
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
    tui_canvas_write(canvas, 0, height - 1, hint, "hint", 0, width);
    if (snapshot) {
      if (snapshot == 2) {
        char *ansi_output = tui_canvas_ansi(canvas);
        if (!ansi_output) {
          tui_canvas_free(canvas);
          tui_tabs_free(tabs);
          tui_tree_free(tree);
          return 1;
        }
        fputs(ansi_output, stdout);
        tui_string_free(ansi_output);
      } else
        for (int y = 0; y < height; y++) {
          char *line = tui_canvas_line(canvas, y);
          if (!line) {
            tui_canvas_free(canvas);
            tui_tabs_free(tabs);
            tui_tree_free(tree);
            return 1;
          }
          puts(line);
          tui_string_free(line);
        }
      tui_canvas_free(canvas);
      break;
    }
    char *output = tui_canvas_ansi(canvas);
    if (!output) {
      tui_canvas_free(canvas);
      restore();
      tui_tabs_free(tabs);
      tui_tree_free(tree);
      return 1;
    }
    fputs(output, stdout);
    fflush(stdout);
    tui_string_free(output);
    tui_canvas_free(canvas);
    unsigned char key;
    if (read(STDIN_FILENO, &key, 1) != 1)
      break;
    if (key == 17 || key == 3)
      break;
    const char *action = key == 'w'                   ? "up"
                         : key == 's'                 ? "down"
                         : key == 'a'                 ? "left"
                         : key == 'd'                 ? "right"
                         : key == '\r' || key == '\n' ? "activate"
                         : key == ' '                 ? "toggle"
                                                      : "";
    if (text_demo || form_demo || list_demo || picker_demo || menu_demo) {
      char input[8] = {0};
      const char *edit_action = "";
      if (key == 27) {
        char seq[24] = {0};
        int n = 0;
        struct pollfd fd = {STDIN_FILENO, POLLIN, 0};
        while (n < 23 && poll(&fd, 1, 30) > 0 &&
               read(STDIN_FILENO, &seq[n], 1) == 1) {
          n++;
          if (seq[n - 1] == 17 || seq[n - 1] == 3) {
            stopped = 1;
            break;
          }
          if (n > 1 && ((seq[n - 1] >= 'A' && seq[n - 1] <= 'Z') ||
                        seq[n - 1] == 'm' || seq[n - 1] == '~'))
            break;
        }
        int button = 0, x = 0, y = 0;
        char ending = 0;
        if (menu_demo &&
            sscanf(seq, "[<%d;%d;%d%c", &button, &x, &y, &ending) == 4) {
          if (ending == 'M' && x > 0 && y > 0)
            menu_demo_pointer(&menu_host, x - 1, y - 1, button);
          continue;
        }
        edit_action = !strcmp(seq, "[21~")     ? "f10"
                      : !strcmp(seq, "[21;2~") ? "shift_f10"
                      : !strcmp(seq, "[A")     ? "up"
                      : !strcmp(seq, "[B")     ? "down"
                      : !strcmp(seq, "[C")     ? "right"
                      : !strcmp(seq, "[D")     ? "left"
                      : !strcmp(seq, "[H")     ? "home"
                      : !strcmp(seq, "[F")     ? "end"
                      : !strcmp(seq, "[3~")    ? "delete"
                                               : (n == 0 ? "cancel" : "");
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
        input[0] = (char)key;
        int n = key < 128 ? 1 : key < 224 ? 2 : key < 240 ? 3 : 4;
        for (int i = 1; i < n; i++)
          if (read(STDIN_FILENO, &input[i], 1) != 1) {
            input[0] = 0;
            break;
          }
        edit_action = "insert";
      }
      if (menu_demo)
        menu_demo_handle(
            &menu_host,
            !strcmp(edit_action, "newline") ? "activate" : edit_action, input);
      else if (list_demo)
        tui_list_handle(list,
                        key == 27   ? edit_action
                        : key == 32 ? "select"
                                    : action,
                        inner.height);
      else if (picker_demo)
        tui_picker_handle(picker,
                          (key == 13 || key == 10) ? "activate" : edit_action,
                          input, inner.height);
      else if (form_demo)
        tui_form_handle(form,
                        key == 9                   ? "next"
                        : (key == 13 || key == 10) ? "activate"
                                                   : edit_action,
                        input);
      else
        tui_text_handle(text, edit_action, input);
    } else if (workspace && key == 9)
      tab_focus = !tab_focus;
    else if (workspace && (key == '<' || key == '>'))
      tui_split_resize(&split, inner.width,
                       split.preferred + (key == '<' ? -1 : 1));
    else if (workspace && tab_focus)
      tui_tabs_handle(tabs, !strcmp(action, "left")    ? "previous"
                            : !strcmp(action, "right") ? "next"
                                                       : action);
    else
      tui_tree_handle(tree, action, inner.height);
  }
  restore();
  menu_demo_free(&menu_host);
  tui_list_free(list);
  tui_picker_free(picker);
  tui_form_free(form);
  tui_text_free(text);
  tui_tabs_free(tabs);
  tui_tree_free(tree);
  return 0;
}
