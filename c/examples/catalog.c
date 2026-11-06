#define _POSIX_C_SOURCE 200809L
#include "tuivory.h"
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
    fputs("\033[0m\033[?25h\033[?1049l", stdout);
    fflush(stdout);
    tcsetattr(STDIN_FILENO, TCSADRAIN, &saved);
    active = 0;
  }
}
int main(int argc, char **argv) {
  const char *theme = "dark", *profile = "256";
  int en = 0, ascii = 0, snapshot = 0;
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
      if (strcmp(argv[++i], "tree")) {
        fputs("Only --demo tree is supported\n", stderr);
        return 2;
      }
    } else {
      puts("--demo tree --lang ko|en --theme dark|light|blackwhite --colors "
           "8|16|256|truecolor --ascii --snapshot");
      return !strcmp(argv[i], "--help") ? 0 : 2;
    }
  }
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
  if (!snapshot) {
    if (!isatty(STDIN_FILENO) || !isatty(STDOUT_FILENO) ||
        tcgetattr(STDIN_FILENO, &saved)) {
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
      tui_tree_free(tree);
      return 1;
    }
    fputs("\033[?1049h", stdout);
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
      tui_tree_free(tree);
      return 1;
    }
    TuiRect inner = tui_canvas_panel(
        canvas, (TuiRect){0, 0, width, height > 0 ? height - 1 : 0},
        en ? "Tuivory C example" : "Tuivory C 예제", 1, ascii);
    tui_tree_draw(tree, canvas, inner, 1, ascii);
    tui_canvas_write(canvas, 0, height - 1,
                     en ? "Ctrl+Q quit | w/s/a/d navigate | Enter activate"
                        : "Ctrl+Q 종료 | w/s/a/d 탐색 | Enter 선택",
                     "hint", 0, width);
    if (snapshot) {
      if (snapshot == 2) {
        char *ansi_output = tui_canvas_ansi(canvas);
        if (!ansi_output) {
          tui_canvas_free(canvas);
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
    tui_tree_handle(tree, action, inner.height);
  }
  restore();
  tui_tree_free(tree);
  return 0;
}
