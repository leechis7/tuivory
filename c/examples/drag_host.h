#ifndef TUIVORY_DRAG_HOST_H
#define TUIVORY_DRAG_HOST_H
#include "tuivory.h"
#include <stdio.h>
#include <string.h>
/* The application owns focus and approval. Models own their copied input. */
typedef struct {
  int en, tab_focus, enabled;
  TuiTree *tree;
  TuiTabs *tabs;
  TuiDragState *drag;
  TuiDragOptions options;
  TuiRect tab_area, tree_area;
  TuiDropRequest *pending;
  char message[512];
} DragDemo;
static void drag_demo_free(DragDemo *h) {
  tui_tree_free(h->tree);
  tui_tabs_free(h->tabs);
  tui_drag_free(h->drag);
  tui_drop_request_free(h->pending);
  memset(h, 0, sizeof(*h));
}
static int drag_demo_init(DragDemo *h, int en) {
  memset(h, 0, sizeof(*h));
  h->en = en;
  h->enabled = 1;
  TuiTab tabs[] = {{"a", en ? "Data" : "데이터", 1, 0, 0},
                   {"b", en ? "Logs" : "로그", 0, 0, 0},
                   {"c", en ? "Tasks" : "작업", 0, 0, 0},
                   {"d", en ? "Disabled" : "비활성", 0, 0, 1}};
  TuiNode nodes[] = {
      {.id = "root", .name = en ? "Workspace" : "작업 공간", .branch = 1},
      {.id = "a",
       .name = en ? "Reports" : "보고서",
       .parent = "root",
       .branch = 1},
      {.id = "a1",
       .name = en ? "Monthly report" : "월별 보고서",
       .parent = "a"},
      {.id = "b",
       .name = en ? "Archive" : "보관함",
       .parent = "root",
       .branch = 1},
      {.id = "b1", .name = en ? "Previous data" : "이전 자료", .parent = "b"},
      {.id = "c", .name = en ? "Notes" : "메모", .parent = "root"}};
  h->tree = tui_tree_new(nodes, 6);
  h->tabs = tui_tabs_new(tabs, 4);
  h->drag = tui_drag_new(1);
  h->options.auto_scroll = h->options.hover_expand = 1;
  if (!h->tree || !h->tabs || !h->drag) {
    drag_demo_free(h);
    return 0;
  }
  tui_tree_handle(h->tree, "toggle", 10);
  tui_tree_handle(h->tree, "down", 10);
  tui_tree_handle(h->tree, "toggle", 10);
  tui_tree_handle(h->tree, "home", 10);
  return 1;
}
static int drag_demo_draw(DragDemo *h, TuiCanvas *c, TuiRect area, int ascii) {
  TuiResult result;
  h->tab_area = (TuiRect){area.x, area.y, area.width, area.height ? 1 : 0};
  h->tree_area = (TuiRect){area.x, area.y + (area.height < 2 ? area.height : 2),
                           area.width, area.height > 6 ? area.height - 6 : 0};
  if (h->tab_focus) {
    tui_tree_draw(h->tree, c, h->tree_area, 0, ascii);
    result = tui_drag_tabs_draw(h->drag, h->tabs, c, h->tab_area, 1, ascii);
  } else {
    tui_tabs_draw(h->tabs, c, h->tab_area, 0);
    result = tui_drag_tree_draw(h->drag, h->tree, c, h->tree_area, 1, ascii);
  }
  char status[512], state[128];
  const char *hint = h->en ? "Order changes only after host approval."
                           : "앱 승인 후에만 순서가 바뀝니다.";
  snprintf(status, sizeof(status), "%s", *h->message ? h->message : hint);
  if (h->pending)
    snprintf(
        status, sizeof(status), "%s%s -> %s (%s) | y / r",
        h->en ? "Pending approval: " : "승인 대기: ", h->pending->source_id,
        h->pending->target_id, h->pending->position);
  snprintf(state, sizeof(state), "%s%s | %s",
           h->en ? "Dragging: " : "드래그: ", h->enabled ? "ON" : "OFF",
           tui_drag_view(h->drag).phase);
  const char *lines[] = {
      h->en ? "Tab switch | [ previous / ] next | i inside / o outside"
            : "Tab 대상 전환 | [ 이전 / ] 다음 | i 안으로 / o 밖으로",
      h->en ? "Drag with mouse | d toggle dragging | Esc cancel"
            : "마우스로 끌기 | d 드래그 켜기/끄기 | Esc 취소",
      status, state};
  for (int i = 0; i < 4; i++) {
    int y = area.y + area.height - 4 + i;
    if (y >= area.y)
      tui_canvas_write(c, area.x, y, lines[i], i == 2 ? "info" : "hint", 0,
                       area.width);
  }
  return result == TUI_OK;
}
static void drag_demo_handle(DragDemo *h, const char *action,
                             const char *text) {
  const char *command = !strcmp(action, "insert") ? text : action;
  if (h->pending) {
    if (!strcmp(command, "y")) {
      const char *reason = "";
      int applied = 0;
      if (h->tab_focus) {
        TuiTabs *next = tui_tabs_apply_drop(h->tabs, h->pending, &reason);
        if (next) {
          tui_tabs_free(h->tabs);
          h->tabs = next;
          applied = 1;
        }
      } else {
        TuiTree *next = tui_tree_apply_drop(h->tree, h->pending, &reason);
        if (next) {
          tui_tree_free(h->tree);
          h->tree = next;
          applied = 1;
        }
      }
      snprintf(h->message, sizeof(h->message), "%s",
               applied ? (h->en ? "Host approved the move."
                                : "앱이 이동을 승인했습니다.")
                       : reason);
      tui_drop_request_free(h->pending);
      h->pending = NULL;
    } else if (!strcmp(command, "r") || !strcmp(action, "cancel")) {
      tui_drop_request_free(h->pending);
      h->pending = NULL;
      snprintf(h->message, sizeof(h->message), "%s",
               h->en ? "Host rejected the move." : "앱이 이동을 거절했습니다.");
    }
    return;
  }
  if (!strcmp(action, "next") || !strcmp(action, "previous")) {
    tui_drag_cancel(h->drag);
    h->tab_focus = !h->tab_focus;
    return;
  }
  if (!strcmp(action, "cancel")) {
    tui_drag_cancel(h->drag);
    return;
  }
  if (!strcmp(command, "d")) {
    h->enabled = !h->enabled;
    tui_drag_enable(h->drag, h->enabled);
    tui_drag_cancel(h->drag);
    return;
  }
  tui_drag_cancel(h->drag);
  if (!strcmp(command, "[") || !strcmp(command, "]") || !strcmp(command, "i") ||
      !strcmp(command, "o")) {
    const char *direction = !strcmp(command, "[")   ? "previous"
                            : !strcmp(command, "]") ? "next"
                            : !strcmp(command, "i") ? "inside"
                                                    : "outside",
               *reason = "";
    h->pending = h->tab_focus
                     ? tui_tabs_keyboard_drop(h->tabs, direction, &h->options,
                                              NULL, NULL, &reason)
                     : tui_tree_keyboard_drop(h->tree, direction, &h->options,
                                              NULL, NULL, &reason);
    if (!h->pending)
      snprintf(h->message, sizeof(h->message), "%s", reason);
    return;
  }
  if (h->tab_focus)
    tui_tabs_handle(h->tabs, !strcmp(action, "left")    ? "previous"
                             : !strcmp(action, "right") ? "next"
                                                        : action);
  else
    tui_tree_handle(h->tree, action, h->tree_area.height);
}
static int drag_demo_inside(TuiRect a, int x, int y) {
  return x >= a.x && x < a.x + a.width && y >= a.y && y < a.y + a.height;
}
static void drag_demo_pointer(DragDemo *h, int x, int y, int button,
                              const char *kind) {
  if (h->pending || (button & 64) || ((button & 3) != 0 && (button & 3) != 3))
    return;
  if (!strcmp(kind, "down")) {
    int target;
    if (drag_demo_inside(h->tab_area, x, y))
      target = 1;
    else if (drag_demo_inside(h->tree_area, x, y))
      target = 0;
    else
      return;
    if (target != h->tab_focus) {
      tui_drag_cancel(h->drag);
      h->tab_focus = target;
    }
  }
  TuiRect a = h->tab_focus ? h->tab_area : h->tree_area;
  if (strcmp(kind, "down") && !tui_drag_view(h->drag).captured)
    return;
  TuiDropRequest *r = NULL;
  TuiDragPointer p = {kind, x - a.x, y - a.y, a.width, a.height};
  TuiResult result = h->tab_focus
                         ? tui_drag_tabs_pointer(h->drag, h->tabs, p,
                                                 &h->options, NULL, NULL, &r)
                         : tui_drag_tree_pointer(h->drag, h->tree, p,
                                                 &h->options, NULL, NULL, &r);
  if (result != TUI_OK) {
    tui_drop_request_free(r);
    return;
  }
  if (r)
    h->pending = r;
  if (!strcmp(kind, "up") && !*tui_drag_view(h->drag).result &&
      drag_demo_inside(a, x, y)) {
    if (h->tab_focus)
      tui_tabs_click(h->tabs, x - a.x, a.width);
    else
      tui_tree_click(h->tree, x - a.x, y - a.y, a.height);
  }
}
#endif
