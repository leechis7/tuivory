#ifndef TUIVORY_EXAMPLE_DIALOG_H
#define TUIVORY_EXAMPLE_DIALOG_H
#include "tuivory.h"
#include <stdio.h>
#include <string.h>
/* The host accepts requests and owns modal lifetime and focus scopes. */
typedef struct {
  int en, opened, disabled, ascii;
  TuiDialog *dialog;
  TuiText *editor;
  TuiFocus *focus;
  TuiRect area, card;
  char status[256];
} DialogDemo;
static const char *dialog_word(DialogDemo *h, const char *ko, const char *en) {
  return h->en ? en : ko;
}
static void dialog_demo_buttons(DialogDemo *h, TuiDialogButton b[3]) {
  b[0] = (TuiDialogButton){
      "retry", dialog_word(h, "작업 다시 시도", "Retry operation"), 0};
  b[1] = (TuiDialogButton){
      "settings", dialog_word(h, "연결 설정 열기", "Open settings"), 0};
  b[2] = (TuiDialogButton){"cancel", dialog_word(h, "취소", "Cancel"),
                           h->disabled};
}
static void dialog_demo_open(DialogDemo *h) {
  if (!h->opened) {
    TuiFocusTarget t = {.id = "buttons"};
    tui_focus_open(h->focus, "dialog", &t, 1, "", 1);
    h->opened = 1;
  }
  tui_dialog_focus(h->dialog, "cancel");
}
static void dialog_demo_free(DialogDemo *h) {
  tui_dialog_free(h->dialog);
  tui_text_free(h->editor);
  tui_focus_free(h->focus);
}
static int dialog_demo_init(DialogDemo *h, int en) {
  memset(h, 0, sizeof *h);
  h->en = en;
  TuiDialogButton b[3];
  dialog_demo_buttons(h, b);
  TuiFocusTarget t = {.id = "editor"};
  h->focus = tui_focus_new("root", &t, 1);
  h->editor = tui_text_new(dialog_word(h, "대화상자를 닫으면 편집합니다.",
                                       "Close the dialog to edit this text."));
  h->dialog = tui_dialog_new(
      dialog_word(h, "다시 연결", "Reconnect"),
      dialog_word(
          h, "작업을 다시 시도할까요?\n내용과 실행은 앱이 결정합니다.",
          "Retry the operation?\nThe host supplies content and actions."),
      b, 3, "cancel");
  if (!h->focus || !h->editor || !h->dialog) {
    dialog_demo_free(h);
    return 0;
  }
  snprintf(h->status, sizeof h->status, "%s",
           dialog_word(h, "아직 실행하지 않았습니다.", "No action accepted."));
  dialog_demo_open(h);
  return 1;
}
static void dialog_demo_accept(DialogDemo *h, TuiEvent e) {
  if (!strcmp(e.kind, "activate") || !strcmp(e.kind, "cancel")) {
    snprintf(h->status, sizeof h->status, "%s%s",
             dialog_word(h, "앱이 수락한 요청: ", "Host accepted: "), e.id);
    h->opened = 0;
    tui_focus_close(h->focus, "dialog");
    h->card = (TuiRect){0};
  }
}
static TuiResult dialog_demo_paint(void *ctx, TuiCanvas *c) {
  DialogDemo *h = ctx;
  return tui_dialog_draw(h->dialog, c, tui_canvas_bounds(c), 1, h->ascii, NULL);
}
static void dialog_demo_draw(DialogDemo *h, TuiCanvas *c, TuiRect a,
                             int ascii) {
  h->area = a;
  h->ascii = ascii;
  tui_text_draw(h->editor, c,
                (TuiRect){a.x, a.y, a.width, a.height < 2 ? a.height : 2},
                !h->opened);
  const char *glyph = ascii ? ":" : h->en ? "界" : "가";
  for (int y = a.y + 2; y < a.y + a.height - 2; y++)
    for (int x = 0; x < a.width; x += ascii ? 1 : 2)
      tui_canvas_write(c, a.x + x, y, glyph, "hint", 0,
                       ascii ? 1 : (a.width - x < 2 ? 1 : 2));
  if (a.height >= 2)
    tui_canvas_write(c, a.x, a.y + a.height - 2, h->status, "hint", 0, a.width);
  if (a.height)
    tui_canvas_write(c, a.x, a.y + a.height - 1,
                     dialog_word(h, "m 열기 | x 취소 비활성 전환",
                                 "m reopen | x toggle Cancel disabled"),
                     "hint", 0, a.width);
  if (h->opened) {
    int w = a.width < 41 ? a.width : 41, ht = a.height > 2 ? a.height - 2 : 0;
    if (ht > 12)
      ht = 12;
    int y = (a.height - ht) / 2 - 1;
    if (y < 0)
      y = 0;
    TuiPopupLayout layout;
    TuiShadowOptions o = {"auto", 0, 0};
    if (tui_shadow_draw(&o, c,
                        (TuiRect){a.x + (a.width - w) / 2, a.y + y, w, ht},
                        dialog_demo_paint, h, ascii, &layout) == TUI_OK)
      h->card = layout.card;
  }
}
static void dialog_demo_handle(DialogDemo *h, const char *action,
                               const char *text) {
  const char *cmd = !strcmp(action, "insert") ? text : action;
  if (!strcmp(cmd, "m"))
    dialog_demo_open(h);
  else if (!strcmp(cmd, "x")) {
    h->disabled = !h->disabled;
    TuiDialogButton b[3];
    dialog_demo_buttons(h, b);
    tui_dialog_set_buttons(h->dialog, b, 3, NULL);
  } else if (h->opened)
    dialog_demo_accept(h, tui_dialog_handle(h->dialog, action));
  else
    tui_text_handle(h->editor, !strcmp(action, "activate") ? "newline" : action,
                    text);
}
static int dialog_demo_contains(TuiRect r, int x, int y) {
  return x >= r.x && y >= r.y && x < r.x + r.width && y < r.y + r.height;
}
static void dialog_demo_pointer(DialogDemo *h, int x, int y, int button) {
  if (button != 0)
    return;
  if (h->opened) {
    if (dialog_demo_contains(h->card, x, y))
      dialog_demo_accept(
          h, tui_dialog_click(h->dialog, x - h->card.x, y - h->card.y));
  } else if (dialog_demo_contains(h->area, x, y))
    tui_text_click(h->editor, x - h->area.x, y - h->area.y, h->area.width,
                   h->area.height < 2 ? h->area.height : 2, 0);
}
#endif
