#ifndef TUIVORY_EXAMPLE_LAYOUT_HOST_H
#define TUIVORY_EXAMPLE_LAYOUT_HOST_H
#include "tuivory.h"
#include <stdio.h>
#include <string.h>
/* Host decides contents/global keys and chip-removal approval. */
typedef struct {
  TuiRect rect;
  int chip, disabled;
} LayoutHit;
typedef struct {
  int en, active;
  const char *density;
  TuiChip chips[3];
  LayoutHit hits[3];
  size_t hit_count;
  char status[256];
} LayoutDemo;
static const char *layout_word(const LayoutDemo *h, const char *ko,
                               const char *en) {
  return h->en ? en : ko;
}
static void layout_demo_init(LayoutDemo *h, int en) {
  memset(h, 0, sizeof *h);
  h->en = en;
  h->active = 1;
  h->density = "auto";
  h->chips[0] = (TuiChip){.id = "filter",
                          .label = layout_word(h, "최근", "Recent"),
                          .removable = 1};
  h->chips[1] = (TuiChip){.id = "fixed",
                          .label = layout_word(h, "읽기 전용", "Read only"),
                          .state = {.read_only = 1},
                          .removable = 1};
  h->chips[2] = (TuiChip){.id = "off",
                          .label = layout_word(h, "비활성", "Disabled"),
                          .state = {.disabled = 1},
                          .removable = 1};
}
static void layout_demo_draw(LayoutDemo *h, TuiCanvas *c, TuiRect area,
                             int ascii) {
  h->hit_count = 0;
  TuiSpacingTokens tokens;
  if (tui_spacing_tokens(h->density, area.width, &tokens) != TUI_OK)
    return;
  TuiStackItem items[] = {{"badges", 16, 20, 0}, {"support", 24, 40, 1}};
  TuiLayoutResult *layout = NULL;
  if (tui_stack_rects((TuiRect){area.x, area.y, area.width,
                                area.height > 0 ? area.height - 1 : 0},
                      items, 2, tokens, 0, &layout) != TUI_OK)
    return;
  TuiBadge badges[] = {
      {.label = layout_word(h, "항목", "Items"), .has_count = 1, .count = 123},
      {.label = layout_word(h, "선택", "Selected"),
       .has_count = 1,
       .count = 0,
       .state = {.selected = 1}},
      {.label = layout_word(h, "비활성", "Disabled"),
       .state = {.disabled = 1}}};
  for (size_t n = 0; n < tui_layout_rect_count(layout); n++) {
    const TuiNamedRect *named = tui_layout_rect_at(layout, n);
    if (!named->rect.width || !named->rect.height)
      continue;
    TuiRect inner = tui_canvas_panel(
        c, named->rect,
        !strcmp(named->id, "badges")
            ? layout_word(h, "배지", "Badges")
            : layout_word(h, "칩·단축키", "Chips and shortcuts"),
        0, ascii);
    int y = inner.y;
    if (!strcmp(named->id, "badges")) {
      for (size_t i = 0; i < 3; i++) {
        if (y >= inner.y + inner.height)
          break;
        tui_badge_draw(&badges[i], c, (TuiRect){inner.x, y, inner.width, 1});
        y += 1 + tokens.control_gap;
      }
    } else {
      for (int i = 0; i < 3; i++) {
        if (i == 0 && !h->active)
          continue;
        if (y >= inner.y + inner.height)
          break;
        tui_chip_draw(&h->chips[i], c, (TuiRect){inner.x, y, inner.width, 1});
        TuiFeedbackView *v = NULL;
        if (tui_chip_line(&h->chips[i], inner.width, &v) == TUI_OK) {
          const TuiFeedbackRow *r = tui_feedback_row(v, 0);
          for (size_t j = 0; j < r->span_count && h->hit_count < 3; j++)
            h->hits[h->hit_count++] = (LayoutHit){
                {inner.x + r->spans[j].start, y, r->spans[j].width, 1},
                i,
                r->spans[j].disabled};
        }
        tui_feedback_free(v);
        y += 1 + tokens.control_gap;
      }
      TuiShortcut shortcuts[] = {
          {"d", layout_word(h, "간격 변경", "Change density"), 10, 0},
          {"x", layout_word(h, "필터 제거", "Remove filter"), 5, !h->active},
          {"r", layout_word(h, "사용 불가", "Unavailable"), 0, 1}};
      TuiHelp *help = tui_help_new(shortcuts, 3);
      if (help)
        tui_help_draw(help, c,
                      (TuiRect){inner.x, y, inner.width,
                                inner.y + inner.height > y
                                    ? inner.y + inner.height - y
                                    : 0});
      tui_help_free(help);
    }
  }
  const char *label =
      !strcmp(h->density, "auto")      ? layout_word(h, "자동", "auto")
      : !strcmp(h->density, "compact") ? layout_word(h, "촘촘", "compact")
                                       : layout_word(h, "여유", "comfortable");
  char status[256];
  snprintf(status, sizeof status, "%s%s%s%zu",
           layout_word(h, "밀도: ", "Density: "), label,
           layout_word(h, " | 숨긴 패널: ", " | Hidden panes: "),
           tui_layout_hidden_count(layout));
  if (area.height)
    tui_canvas_write(c, area.x, area.y + area.height - 1,
                     *h->status ? h->status : status, "hint", 0, area.width);
  tui_layout_free(layout);
}
static void layout_demo_apply(LayoutDemo *h, TuiEvent e) {
  if (!strcmp(e.kind, "remove") && !strcmp(e.id, "filter") && h->active) {
    h->active = 0;
    h->hit_count = 0;
    snprintf(h->status, sizeof h->status, "%s",
             layout_word(h, "필터를 제거했습니다.", "Filter removed."));
  }
}
static void layout_demo_handle(LayoutDemo *h, const char *action,
                               const char *text) {
  const char *command = !strcmp(action, "insert") ? text : action;
  if (!strcmp(command, "x") || !strcmp(command, "activate"))
    layout_demo_apply(h, tui_chip_request_remove(&h->chips[0]));
  else if (!strcmp(command, "d")) {
    h->density = !strcmp(h->density, "comfortable") ? "compact" : "comfortable";
    h->hit_count = 0;
    snprintf(h->status, sizeof h->status, "%s",
             !strcmp(h->density, "compact")
                 ? layout_word(h, "밀도: 촘촘", "Density: compact")
                 : layout_word(h, "밀도: 여유", "Density: comfortable"));
  }
}
static void layout_demo_pointer(LayoutDemo *h, int x, int y, int button) {
  if (button != 0)
    return;
  for (size_t i = 0; i < h->hit_count; i++) {
    LayoutHit hit = h->hits[i];
    if (x >= hit.rect.x && x < hit.rect.x + hit.rect.width && y >= hit.rect.y &&
        y < hit.rect.y + hit.rect.height) {
      if (!hit.disabled)
        layout_demo_apply(h, tui_chip_request_remove(&h->chips[hit.chip]));
      return;
    }
  }
}
#endif
