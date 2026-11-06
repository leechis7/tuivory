#ifndef TUIVORY_EXAMPLE_SURFACE_HOST_H
#define TUIVORY_EXAMPLE_SURFACE_HOST_H
#include "tuivory.h"
#include <stdio.h>
#include <string.h>
typedef struct {
  int en, index;
  TuiText *input;
} SurfaceDemo;
static const char *surface_word(const SurfaceDemo *h, const char *ko,
                                const char *en) {
  return h->en ? en : ko;
}
static int surface_demo_init(SurfaceDemo *h, int en) {
  h->en = en;
  h->index = 1;
  h->input = tui_text_new(surface_word(h, "읽기 전용", "Read only"));
  if (!h->input)
    return 0;
  tui_text_options(h->input, (TuiState){.read_only = 1}, 0, 0);
  return 1;
}
static void surface_demo_free(SurfaceDemo *h) { tui_text_free(h->input); }
static TuiResult surface_paint(void *context, TuiCanvas *c) {
  SurfaceDemo *h = context;
  int w = tui_canvas_bounds(c).width;
  TuiResult result = tui_canvas_write(
      c, 0, 0, surface_word(h, "바탕 위 문구", "Body on surface"), "body", 0,
      w);
  if (result != TUI_OK)
    return result;
  tui_canvas_write(c, 0, 1, surface_word(h, "보조 설명", "Secondary"), "hint",
                   0, w);
  tui_canvas_write(c, 0, 2, surface_word(h, "정상 상태", "Success"), "success",
                   0, w);
  TuiChip off = {.id = "off",
                 .label = surface_word(h, "비활성", "Disabled"),
                 .state = {.disabled = 1}},
          edited = {.id = "edited",
                    .label = surface_word(h, "수정", "Edited"),
                    .state = {.edited = 1}};
  TuiBadge selected = {.label = surface_word(h, "선택", "Selected"),
                       .has_count = 1,
                       .state = {.selected = 1}};
  tui_chip_draw(&off, c, (TuiRect){0, 3, w, 1});
  tui_badge_draw(&selected, c, (TuiRect){0, 4, w, 1});
  tui_chip_draw(&edited, c, (TuiRect){0, 5, w, 1});
  tui_text_draw(h->input, c, (TuiRect){0, 6, w, 1}, 0);
  TuiShortcut hint = {"s", surface_word(h, "바탕 변경", "Change surface"), 0,
                      0};
  TuiHelp *help = tui_help_new(&hint, 1);
  if (!help)
    return TUI_NOMEM;
  result = tui_help_draw(help, c, (TuiRect){0, 8, w, 1});
  tui_help_free(help);
  return result;
}
static void surface_demo_draw(SurfaceDemo *h, TuiCanvas *c, TuiRect area,
                              int ascii) {
  (void)ascii;
  const char *roles[] = {"surface", "editor", "field", "button.focus"},
             *ko[] = {"패널", "편집", "입력", "포커스 버튼"},
             *en[] = {"panel", "editor", "field", "focused button"};
  TuiSurface surface = {roles[h->index]};
  tui_surface_draw(&surface, c,
                   (TuiRect){area.x, area.y, area.width,
                             area.height > 0 ? area.height - 1 : 0},
                   surface_paint, h);
  char status[120];
  snprintf(status, sizeof status, "%s%s",
           surface_word(h, "바탕: ", "Surface: "),
           h->en ? en[h->index] : ko[h->index]);
  if (area.height)
    tui_canvas_write(c, area.x, area.y + area.height - 1, status, "hint", 0,
                     area.width);
}
static void surface_demo_handle(SurfaceDemo *h, const char *action,
                                const char *text) {
  if (!strcmp(!strcmp(action, "insert") ? text : action, "s"))
    h->index = (h->index + 1) % 4;
}
static void surface_demo_pointer(SurfaceDemo *h, int x, int y, int button) {
  (void)h;
  (void)x;
  (void)y;
  (void)button;
}
#endif
