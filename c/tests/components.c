#include "tuivory.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
  TuiNode nodes[] = {{.id = "r", .name = "Root"},
                     {.id = "g", .name = "Group", .parent = "r"},
                     {.id = "a", .name = "한글 👩‍💻", .parent = "g"},
                     {.id = "z", .name = "Other"}};
  TuiTree *t = tui_tree_new(nodes, 4);
  assert(t);
  assert(!strcmp(tui_tree_handle(t, "right", 3).kind, "expand"));
  assert(!strcmp(tui_tree_handle(t, "down", 3).id, "g"));
  assert(!strcmp(tui_tree_handle(t, "right", 3).kind, "expand"));
  assert(!strcmp(tui_tree_handle(t, "right", 3).id, "a"));
  assert(!strcmp(tui_tree_handle(t, "left", 3).id, "g"));
  assert(!strcmp(tui_tree_handle(t, "left", 3).kind, "collapse"));
  assert(tui_cells("한글 👩‍💻") == 7);
  assert(tui_cells("\xff") == -1);
  assert(tui_cells("\xf8\x90\x80\x80") == -1);
  assert(tui_cells("\xc0\xaf") == -1);
  assert(tui_cells("\xed\xa0\x80") == -1);
  assert(tui_cells("\xf4\x90\x80\x80") == -1);
  assert(tui_cells("\xe2\x82") == -1);
  const char *themes[] = {"dark", "light", "blackwhite"},
             *profiles[] = {"8", "16", "256", "truecolor"};
  for (int th = 0; th < 3; th++)
    for (int p = 0; p < 4; p++) {
      TuiCanvas *c = tui_canvas_new(20, 5, themes[th], profiles[p]);
      assert(c);
      assert(tui_canvas_write(c, 0, 0, "한글💻abc", "body", 0, 20) == TUI_OK);
      char *line = tui_canvas_line(c, 0);
      assert(strstr(line, "한글💻abc"));
      tui_string_free(line);
      assert(tui_canvas_write(c, 1, 0, " X", "selection", 0, 2) == TUI_OK);
      line = tui_canvas_line(c, 0);
      assert(!strncmp(line, "  X ", 4));
      tui_string_free(line);
      TuiRect r = tui_canvas_panel(c, (TuiRect){0, 1, 20, 4}, "Tuivory", 1, 0);
      assert(tui_tree_draw(t, c, r, 1, 0) == TUI_OK);
      tui_canvas_cursor(c, 3, 2, 2);
      char *ansi = tui_canvas_ansi(c);
      assert(ansi);
      assert(!strstr(ansi, " q"));
      assert(!strstr(ansi, "\033[?12"));
      tui_string_free(ansi);
      for (int y = 0; y < 5; y++) {
        line = tui_canvas_line(c, y);
        assert(tui_cells(line) <= 20);
        tui_string_free(line);
      }
      tui_canvas_free(c);
    }
  TuiState s = {.disabled = 1};
  assert(!tui_state_editable(s));
  assert(!tui_state_activatable(s));
  tui_tree_free(t);
  tui_canvas_free(NULL);
  tui_tree_free(NULL);
  tui_string_free(NULL);
}
