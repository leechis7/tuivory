#ifndef TUIVORY_EXAMPLE_CONTAINER_HOST_H
#define TUIVORY_EXAMPLE_CONTAINER_HOST_H
#include "tuivory.h"
#include <stdio.h>
#include <string.h>
typedef struct {
  int en, opened, ascii, ox, oy, scroll;
  TuiContainer *base, *layers;
  TuiText *editor;
  char status[160];
} ContainerDemo;
static const char *container_word(const ContainerDemo *h, const char *ko,
                                  const char *en) {
  return h->en ? en : ko;
}
static void container_demo_free(ContainerDemo *h) {
  tui_container_free(h->base);
  tui_container_free(h->layers);
  tui_text_free(h->editor);
}
static int container_demo_init(ContainerDemo *h, int en, int ascii) {
  memset(h, 0, sizeof *h);
  h->en = en;
  TuiLayoutItem base[] = {{.id = "nav", .track = {.fixed = 20}},
                          {.id = "editor"}},
                background = {.id = "background"};
  TuiContainerOptions o = {.kind = "row", .gap = 1, .virtual_width = 96},
                      layers = {.kind = "layers"};
  h->base = tui_container_new(base, 2, &o);
  h->layers = tui_container_new(&background, 1, &layers);
  h->editor = tui_text_new(
      container_word(h, "편집 영역 한글 界",
                     ascii ? "Editor area ASCII" : "Editor area Unicode 界"));
  if (!h->base || !h->layers || !h->editor) {
    container_demo_free(h);
    memset(h, 0, sizeof *h);
    return 0;
  }
  tui_container_move_focus(tui_container_state(h->base), base, 2, 0);
  return 1;
}
static TuiResult container_paint_pane(void *context, const char *id,
                                      TuiCanvas *child, int focused) {
  ContainerDemo *h = context;
  TuiRect inner = tui_canvas_panel(child, tui_canvas_bounds(child),
                                   !strcmp(id, "nav")
                                       ? container_word(h, "탐색", "Navigator")
                                       : container_word(h, "편집", "Editor"),
                                   focused, h->ascii);
  if (!strcmp(id, "nav"))
    return tui_canvas_write(child, inner.x, inner.y,
                            container_word(h, "개요", "Overview"), "body", 0,
                            inner.width);
  return tui_text_draw(h->editor, child, inner, focused);
}
static TuiResult container_paint_layer(void *context, const char *id,
                                       TuiCanvas *child, int focused) {
  ContainerDemo *h = context;
  (void)focused;
  if (!strcmp(id, "background"))
    return tui_container_draw(h->base, child, tui_canvas_bounds(child),
                              container_paint_pane, h);
  TuiRect inner =
      tui_canvas_panel(child, tui_canvas_bounds(child),
                       container_word(h, "팝업", "Modal"), 0, h->ascii);
  TuiResult r = tui_canvas_write(
      child, inner.x, inner.y,
      container_word(h, "배경 입력 차단", "Background input blocked"), "body",
      0, inner.width);
  if (r == TUI_OK)
    r = tui_canvas_write(child, inner.x, inner.y + 1,
                         container_word(h, "m / Esc 닫기", "m / Esc close"),
                         "hint", 0, inner.width);
  return r;
}
static void container_demo_draw(ContainerDemo *h, TuiCanvas *c, TuiRect area,
                                int ascii) {
  h->ascii = ascii;
  h->ox = area.x;
  h->oy = area.y;
  tui_container_draw(h->layers, c,
                     (TuiRect){area.x, area.y, area.width,
                               area.height > 0 ? area.height - 1 : 0},
                     container_paint_layer, h);
  char status[160];
  snprintf(status, sizeof status, "%s%d",
           container_word(h, "스크롤: ", "Scroll: "), h->scroll);
  if (area.height)
    tui_canvas_write(c, area.x, area.y + area.height - 1,
                     *h->status ? h->status : status, "hint", 0, area.width);
}
static void container_demo_handle(ContainerDemo *h, const char *action,
                                  const char *text) {
  const char *command = !strcmp(action, "insert") ? text : action;
  if (!strcmp(command, "m") || (!strcmp(command, "cancel") && h->opened)) {
    h->opened = !strcmp(command, "m") ? !h->opened : 0;
    TuiLayoutItem items[] = {
        {.id = "background"},
        {.id = "popup", .modal = 1, .centered = 1, .area = {0, 0, 30, 6}}};
    tui_container_set_items(h->layers, items, h->opened ? 2 : 1, NULL);
    snprintf(h->status, sizeof h->status, "%s",
             h->opened ? container_word(h, "팝업 열림", "Popup open")
                       : container_word(h, "팝업 닫힘", "Popup closed"));
  } else if (!h->opened) {
    if (!strcmp(command, "h") || !strcmp(command, "l")) {
      h->scroll += !strcmp(command, "l") ? 4 : -4;
      if (h->scroll < 0)
        h->scroll = 0;
      tui_container_scroll(h->base, h->scroll, 0);
      snprintf(h->status, sizeof h->status, "%s%d",
               container_word(h, "스크롤: ", "Scroll: "), h->scroll);
    } else if (!strcmp(command, "next") || !strcmp(command, "previous")) {
      TuiLayoutItem items[] = {{.id = "nav", .track = {.fixed = 20}},
                               {.id = "editor"}};
      tui_container_move_focus(tui_container_state(h->base), items, 2,
                               !strcmp(command, "previous"));
    } else if (!strcmp(tui_container_focused(tui_container_state(h->base)),
                       "editor"))
      tui_text_handle(h->editor, action, text);
  }
}
static void container_demo_pointer(ContainerDemo *h, int x, int y, int button) {
  const char *id = "";
  if (!button && tui_container_pointer(h->layers, x, y, 1, 1, &id) == TUI_OK &&
      !strcmp(id, "background"))
    tui_container_pointer(h->base, x - h->ox, y - h->oy, 1, 1, &id);
}
#endif
