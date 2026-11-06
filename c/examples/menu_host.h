#ifndef TUIVORY_EXAMPLE_MENU_HOST_H
#define TUIVORY_EXAMPLE_MENU_HOST_H
#include "tuivory.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* Example host owns screens, global keys, focus scopes and action callbacks. */
typedef struct {
  int en, context, anchored;
  TuiMenu *menu;
  TuiFocus *focus;
  TuiText *editor;
  TuiRect area, bar, content, editor_area, anchor;
  char status[256];
} MenuDemo;
static void menu_demo_sync(MenuDemo *h, TuiMenuEvent e) {
  if (!tui_menu_opened(h->menu) && tui_focus_depth(h->focus))
    tui_focus_close(h->focus, "popup");
  if (!strcmp(e.kind, "activate")) {
    size_t count = 0;
    const TuiMenuItem *items = tui_menu_items(h->menu, &count);
    for (size_t i = 0; i < count; i++)
      if (!strcmp(items[i].id, e.id))
        snprintf(h->status, sizeof h->status, "%s%s",
                 h->en ? "Selected: " : "선택: ", items[i].label);
  }
}
static void menu_demo_open(MenuDemo *h, const char *id) {
  TuiMenuEvent e = tui_menu_open(h->menu, id, "editor");
  if (tui_menu_opened(h->menu) && !tui_focus_depth(h->focus)) {
    TuiFocusTarget target = {.id = "menu"};
    tui_focus_open(h->focus, "popup", &target, 1, "", 1);
  }
  menu_demo_sync(h, e);
}
static void menu_demo_free(MenuDemo *h) {
  tui_menu_free(h->menu);
  tui_focus_free(h->focus);
  tui_text_free(h->editor);
}
static int menu_demo_init(MenuDemo *h, int en, int context) {
  memset(h, 0, sizeof *h);
  h->en = en;
  h->context = context;
  TuiMenuItem items[] = {
      {.id = "file", .label = en ? "File" : "파일", .mnemonic = "f"},
      {.id = "new",
       .parent = "file",
       .label = en ? "New document" : "새 문서",
       .mnemonic = "n",
       .shortcut = "Ctrl+N"},
      {.id = "line", .parent = "file", .separator = 1},
      {.id = "off",
       .parent = "file",
       .label = en ? "Unavailable" : "사용 불가",
       .disabled = 1},
      {.id = "recent",
       .parent = "file",
       .label = en ? "Recent documents" : "최근 문서",
       .mnemonic = "r"},
      {.id = "a",
       .parent = "recent",
       .label = en ? "Example A" : "예제 A",
       .mnemonic = "a"},
      {.id = "more",
       .parent = "recent",
       .label = en ? "More" : "더 보기",
       .mnemonic = "m"},
      {.id = "b",
       .parent = "more",
       .label = en ? "Example B" : "예제 B",
       .mnemonic = "b"},
      {.id = "edit", .label = en ? "Edit" : "편집", .mnemonic = "e"},
      {.id = "copy",
       .parent = "edit",
       .label = en ? "Copy" : "복사",
       .mnemonic = "c",
       .shortcut = "Ctrl+C"}};
  TuiFocusTarget target = {.id = "editor"};
  h->menu = tui_menu_new(items, 10);
  h->focus = tui_focus_new("root", &target, 1);
  h->editor = tui_text_new(en ? "Close the menu to edit this text."
                              : "메뉴를 닫으면 여기를 편집할 수 있습니다.");
  if (!h->menu || !h->focus || !h->editor) {
    menu_demo_free(h);
    return 0;
  }
  tui_menu_labels(h->menu, en ? "Back" : "뒤로", en ? "(empty)" : "항목 없음");
  snprintf(h->status, sizeof h->status, "%s",
           en ? "Clicks outside the popup are blocked."
              : "팝업 밖의 클릭은 배경에 전달되지 않습니다.");
  menu_demo_open(h, context ? "" : "file");
  return 1;
}
static int menu_demo_contains(TuiRect r, int x, int y) {
  return x >= r.x && x < r.x + r.width && y >= r.y && y < r.y + r.height;
}
static void menu_demo_draw(MenuDemo *h, TuiCanvas *c, TuiRect area, int ascii) {
  h->area = area;
  h->bar = (TuiRect){area.x, area.y, area.width, h->context ? 0 : 1};
  int remaining = area.height - h->bar.height;
  h->editor_area = (TuiRect){area.x, area.y + h->bar.height, area.width,
                             remaining < 0   ? 0
                             : remaining < 2 ? remaining
                                             : 2};
  tui_text_draw(h->editor, c, h->editor_area, !tui_menu_opened(h->menu));
  const char *glyph = ascii ? "." : h->en ? "界" : "가";
  size_t bytes = strlen(glyph);
  char *line = malloc((size_t)area.width * bytes + 1);
  if (line) {
    for (int x = 0; x < area.width; x++)
      memcpy(line + (size_t)x * bytes, glyph, bytes);
    line[(size_t)area.width * bytes] = 0;
    for (int y = h->editor_area.y + h->editor_area.height;
         y < area.y + area.height - 2; y++)
      tui_canvas_write(c, area.x, y, line, "hint", 0, area.width);
    free(line);
  }
  if (h->bar.height)
    tui_menu_draw_bar(h->menu, c, h->bar);
  if (area.height >= 2)
    tui_canvas_write(c, area.x, area.y + area.height - 2, h->status, "hint", 0,
                     area.width);
  if (area.height >= 1)
    tui_canvas_write(c, area.x, area.y + area.height - 1,
                     h->en ? "F10 menu | Shift+F10 / right click"
                           : "F10 메뉴 | Shift+F10 / 오른쪽 클릭",
                     "hint", 0, area.width);
  TuiRect anchor = h->anchored
                       ? h->anchor
                       : (TuiRect){area.x + (h->context ? area.width / 2 : 1),
                                   area.y + (h->context ? 5 : 0), 1, 1};
  if (h->context || h->anchored)
    tui_canvas_write(c, anchor.x, anchor.y, "+", "warning", 0, 1);
  h->content = (TuiRect){0};
  if (tui_menu_opened(h->menu)) {
    int width = 0, height = 0;
    tui_menu_content_size(h->menu, &width, &height);
    width = ((width + 5) / 2) * 2;
    if (width > 48)
      width = 48;
    TuiRect popup = tui_menu_placement(anchor, area, width, height + 4);
    char *title = tui_menu_title(h->menu);
    tui_menu_draw_popup(h->menu, c, popup,
                        title && *title ? title
                        : h->en         ? "Context menu"
                                        : "문맥 메뉴",
                        1, ascii, &h->content);
    tui_string_free(title);
  }
}
static void menu_demo_handle(MenuDemo *h, const char *action,
                             const char *text) {
  if (!strcmp(action, "f10")) {
    if (tui_menu_opened(h->menu))
      menu_demo_sync(h, tui_menu_close(h->menu));
    else {
      h->anchored = 0;
      menu_demo_open(h, h->context ? "" : "file");
    }
  } else if (!strcmp(action, "shift_f10")) {
    h->anchored = 1;
    h->anchor = (TuiRect){h->area.x + h->area.width / 2, h->area.y + 4, 1, 1};
    menu_demo_open(h, "");
  } else if (tui_menu_opened(h->menu)) {
    if (!strcmp(action, "cancel") && !tui_focus_request_close(h->focus).id[0])
      return;
    menu_demo_sync(
        h, tui_menu_handle(h->menu,
                           !strcmp(action, "insert") ? "mnemonic" : action,
                           text, h->content.height));
  } else if (!tui_focus_route(h->focus, "root").blocked)
    tui_text_handle(h->editor, !strcmp(action, "activate") ? "newline" : action,
                    text);
}
static void menu_demo_pointer(MenuDemo *h, int x, int y, int button) {
  if (button == 2 && menu_demo_contains(h->area, x, y)) {
    h->anchored = 1;
    h->anchor = (TuiRect){x, y, 1, 1};
    menu_demo_open(h, "");
  } else if (button == 0) {
    if (tui_menu_opened(h->menu) && menu_demo_contains(h->content, x, y))
      menu_demo_sync(h, tui_menu_click(h->menu, x - h->content.x,
                                       y - h->content.y, h->content.height));
    else if (menu_demo_contains(h->bar, x, y)) {
      TuiMenuEvent e = tui_menu_bar_click(h->menu, x - h->bar.x, h->bar.width);
      if (!strcmp(e.kind, "open_request")) {
        h->anchored = 0;
        menu_demo_open(h, e.id);
      }
    } else if (!tui_focus_route(h->focus, "root").blocked &&
               menu_demo_contains(h->editor_area, x, y))
      tui_text_click(h->editor, x - h->editor_area.x, y - h->editor_area.y,
                     h->editor_area.width, h->editor_area.height, 0);
  }
}
#endif
