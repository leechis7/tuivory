#ifndef TUIVORY_EXAMPLE_GRID_HOST_H
#define TUIVORY_EXAMPLE_GRID_HOST_H
#include "tuivory.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* Application-owned data and approval; no database or cross-language runtime.
 */
typedef struct {
  int en, density;
  TuiRect area;
  TuiGrid *grid;
  TuiText *search;
  TuiDocument *detail;
  TuiGridViewState *saved;
  TuiGridRecord rows[8];
  TuiGridCell cells[8][4];
  char *values[8][4];
  TuiGridChange pending[32];
  size_t pending_count;
  unsigned long long pending_id;
  int pending_edit;
  char message[4096];
} GridDemo;
static const char *grid_demo_word(GridDemo *h, const char *ko, const char *en) {
  return h->en ? en : ko;
}
static char *grid_demo_copy(const char *s) {
  size_t n = strlen(s ? s : "") + 1;
  char *p = malloc(n);
  if (p)
    memcpy(p, s ? s : "", n);
  return p;
}
static void grid_demo_pending_clear(GridDemo *h) {
  for (size_t i = 0; i < h->pending_count; i++) {
    free((void *)h->pending[i].row_id);
    free((void *)h->pending[i].column_id);
    free((void *)h->pending[i].value.text);
  }
  memset(h->pending, 0, sizeof(h->pending));
  h->pending_count = 0;
  h->pending_id = 0;
}
static void grid_demo_free(GridDemo *h) {
  if (!h)
    return;
  tui_grid_free(h->grid);
  tui_text_free(h->search);
  tui_document_free(h->detail);
  tui_grid_view_free(h->saved);
  grid_demo_pending_clear(h);
  for (int i = 0; i < 8; i++)
    for (int j = 0; j < 4; j++)
      free(h->values[i][j]);
  memset(h, 0, sizeof(*h));
}
static TuiResult grid_demo_info(void *context, const TuiGridRecord *r,
                                const TuiGridColumn *c, TuiGridCellInfo *out) {
  (void)context;
  const char *raw = "";
  for (size_t i = 0; i < r->cell_count; i++)
    if (!strcmp(r->cells[i].column_id, "value"))
      raw = r->cells[i].text;
  out->display = "1,234";
  out->has_display = out->numeric =
      !strcmp(c->id, "value") && !strcmp(raw, "1234");
  return TUI_OK;
}
static TuiResult grid_demo_row(void *context, size_t i, TuiGridRecord *out) {
  GridDemo *h = context;
  if (i >= 8)
    return TUI_INVALID;
  *out = h->rows[i];
  return TUI_OK;
}
static TuiResult grid_demo_index(void *context, const char *id, size_t *out) {
  GridDemo *h = context;
  for (size_t i = 0; i < 8; i++)
    if (!strcmp(h->rows[i].id, id)) {
      *out = i;
      return TUI_OK;
    }
  return TUI_INVALID;
}
static TuiGridSource grid_demo_source(GridDemo *h) {
  return (TuiGridSource){h, 8, grid_demo_row, grid_demo_index};
}
static int grid_demo_init(GridDemo *h, int en, int ascii) {
  memset(h, 0, sizeof(*h));
  h->en = en;
  const char *ids[] = {"r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"};
  const char *columns[] = {"id", "name", "value", "state"};
  const char *data[8][4] = {
      {"01",
       grid_demo_word(h, "한글 👩‍💻",
                      ascii ? "ASCII sample" : "Unicode 👩‍💻"),
       "1234", grid_demo_word(h, "준비", "Ready")},
      {"02", grid_demo_word(h, "널 값", "Null value"), "", "NULL"},
      {"03", grid_demo_word(h, "비활성 행", "Disabled row"), "blocked",
       grid_demo_word(h, "비활성", "Disabled")},
      {"04", grid_demo_word(h, "읽기 전용", "Read only"), "read-only",
       grid_demo_word(h, "읽기 전용", "Read only")},
      {"05", grid_demo_word(h, "수정된 셀", "Edited cell"), "changed",
       grid_demo_word(h, "수정됨", "Edited")},
      {"06", grid_demo_word(h, "빈 문자열", "Empty string"), "",
       grid_demo_word(h, "비어 있음", "Empty")},
      {"07", "Find target", "long_value_for_horizontal_scrolling",
       grid_demo_word(h, "검색 가능", "Searchable")},
      {"08", grid_demo_word(h, "오류 표시", "Invalid cell"), "invalid",
       grid_demo_word(h, "오류", "Invalid")}};
  for (int i = 0; i < 8; i++) {
    h->rows[i] =
        (TuiGridRecord){.id = ids[i], .cells = h->cells[i], .cell_count = 4};
    for (int j = 0; j < 4; j++) {
      h->values[i][j] = grid_demo_copy(data[i][j]);
      if (!h->values[i][j])
        goto fail;
      h->cells[i][j] =
          (TuiGridCell){.column_id = columns[j], .text = h->values[i][j]};
    }
  }
  h->cells[1][2].is_null = 1;
  h->rows[2].state.disabled = 1;
  h->rows[3].state.read_only = 1;
  h->cells[4][2].state.edited = 1;
  h->cells[7][2].state.invalid = 1;
  TuiGridColumn cols[4] = {
      {.id = "id", .label = "ID", .width = 5, .pin = "left"},
      {.id = "name",
       .label = grid_demo_word(h, "이름", "Name"),
       .width = 18,
       .editable = 1},
      {.id = "value",
       .label = grid_demo_word(h, "값", "Value"),
       .width = 22,
       .editable = 1},
      {.id = "state",
       .label = grid_demo_word(h, "상태", "State"),
       .width = 12,
       .pin = "right"}};
  h->grid = tui_grid_new(cols, 4, h->rows, 8);
  if (!h->grid)
    goto fail;
  TuiGridOptions options;
  if (tui_grid_preset("data", &options) != TUI_OK ||
      tui_grid_configure(h->grid, &options) != TUI_OK ||
      tui_grid_set_labels(
          h->grid,
          (TuiGridLabels){"NULL", grid_demo_word(h, "로딩 중", "loading"),
                          grid_demo_word(h, "비어 있음", "empty"),
                          grid_demo_word(h, "범위", "range"),
                          grid_demo_word(h, "더 있음", "more")}) != TUI_OK ||
      tui_grid_set_edit_options(
          h->grid, (TuiGridEditOptions){.enabled = 1,
                                        .start_typing = 1,
                                        .allow_null = 1}) != TUI_OK ||
      tui_grid_set_column_options(
          h->grid, "value",
          (TuiGridColumnOptions){
              .align = "auto", .overflow = "scroll", .expand = 1}) != TUI_OK ||
      tui_grid_set_cell_info(h->grid, grid_demo_info, h) != TUI_OK ||
      !tui_grid_focus(h->grid, "r1", "name"))
    goto fail;
  return 1;
fail:
  grid_demo_free(h);
  return 0;
}
static int grid_demo_draw(GridDemo *h, TuiCanvas *c, TuiRect a, int ascii) {
  h->area = (TuiRect){a.x, a.y, a.width, a.height > 3 ? a.height - 3 : 0};
  if (tui_grid_draw(h->grid, c, h->area, !h->search && !h->detail, ascii) !=
      TUI_OK)
    return 0;
  if (h->detail) {
    TuiRect inner = tui_canvas_panel(
        c, h->area, grid_demo_word(h, "원문 상세", "Raw cell details"), 1,
        ascii);
    if (tui_document_configure(h->detail, (TuiDocumentOptions){.wrap = 1}) !=
            TUI_OK ||
        tui_document_draw(h->detail, c, inner, 1, ascii) != TUI_OK)
      return 0;
  }
  if (a.height >= 3) {
    int y = a.y + a.height - 3;
    if (h->search) {
      const char *prompt = grid_demo_word(h, "검색: ", "Find: ");
      int offset = tui_cells(prompt);
      if (offset > a.width)
        offset = a.width;
      if (tui_canvas_write(c, a.x, y, prompt, "hint", 0, a.width) != TUI_OK ||
          tui_text_draw(h->search, c,
                        (TuiRect){a.x + offset, y, a.width - offset, 1},
                        1) != TUI_OK)
        return 0;
    } else if (tui_canvas_write(c, a.x, y, h->message, "info", 0, a.width) !=
               TUI_OK)
      return 0;
  }
  if (a.height >= 2 &&
      tui_canvas_write(
          c, a.x, a.y + a.height - 2,
          grid_demo_word(h,
                         "Enter 편집 | / 검색 | d 원문 | p 붙여넣기 | c 복사",
                         "Enter edit | / find | d details | p paste | c copy"),
          "hint", 0, a.width) != TUI_OK)
    return 0;
  if (a.height &&
      tui_canvas_write(
          c, a.x, a.y + a.height - 1,
          grid_demo_word(
              h,
              "대기: y 승인/r 거절 | Ctrl+N NULL | v 간격 | b 보기 저장/복원",
              "Pending: y approve/r reject | Ctrl+N NULL | v density | b view"),
          "hint", 0, a.width) != TUI_OK)
    return 0;
  return 1;
}
static int grid_demo_capture(GridDemo *h, unsigned long long id, int edit,
                             const TuiGridChange *changes, size_t count) {
  if (count > 32)
    return 0;
  grid_demo_pending_clear(h);
  for (size_t i = 0; i < count; i++) {
    h->pending[i] = changes[i];
    h->pending[i].row_id = grid_demo_copy(changes[i].row_id);
    h->pending[i].column_id = grid_demo_copy(changes[i].column_id);
    h->pending[i].value.text = grid_demo_copy(changes[i].value.text);
    h->pending_count++;
    if (!h->pending[i].row_id || !h->pending[i].column_id ||
        !h->pending[i].value.text) {
      grid_demo_pending_clear(h);
      return 0;
    }
  }
  h->pending_id = id;
  h->pending_edit = edit;
  snprintf(h->message, sizeof h->message, "%s",
           grid_demo_word(h, "승인 대기: y 승인 / r 거절",
                          "Pending approval: y approve / r reject"));
  return 1;
}
static void grid_demo_approve(GridDemo *h, int accept) {
  if (!h->pending_id)
    return;
  if (!accept) {
    if (h->pending_edit)
      tui_grid_resolve_edit(h->grid, h->pending_id,
                            grid_demo_word(h, "거절됨: 수정 후 다시 제출",
                                           "Rejected: edit and retry"),
                            NULL);
    else
      tui_grid_cancel_paste(h->grid);
    snprintf(h->message, sizeof h->message, "%s",
             grid_demo_word(h, "앱이 요청을 거절했습니다.",
                            "Host rejected the request."));
    grid_demo_pending_clear(h);
    return;
  }
  char *next[8][4] = {{0}};
  TuiGridCell cells[8][4];
  memcpy(cells, h->cells, sizeof cells);
  for (int i = 0; i < 8; i++)
    for (int j = 0; j < 4; j++) {
      next[i][j] = grid_demo_copy(h->values[i][j]);
      if (!next[i][j])
        goto fail;
    }
  for (size_t k = 0; k < h->pending_count; k++) {
    const TuiGridChange *change = &h->pending[k];
    for (int i = 0; i < 8; i++)
      if (!strcmp(h->rows[i].id, change->row_id))
        for (int j = 0; j < 4; j++)
          if (!strcmp(h->cells[i][j].column_id, change->column_id)) {
            char *value = grid_demo_copy(change->value.text);
            if (!value)
              goto fail;
            free(next[i][j]);
            next[i][j] = value;
            cells[i][j].is_null = change->value.is_null;
            cells[i][j].state.edited = 1;
          }
  }
  TuiGridCell old_cells[8][4];
  memcpy(old_cells, h->cells, sizeof old_cells);
  for (int i = 0; i < 8; i++)
    for (int j = 0; j < 4; j++) {
      h->cells[i][j] = cells[i][j];
      h->cells[i][j].text = next[i][j];
    }
  TuiGridSource source = grid_demo_source(h);
  int accepted =
      h->pending_edit
          ? tui_grid_resolve_edit(h->grid, h->pending_id, "", &source)
          : tui_grid_resolve_paste(h->grid, h->pending_id, &source);
  if (accepted) {
    for (int i = 0; i < 8; i++)
      for (int j = 0; j < 4; j++) {
        free(h->values[i][j]);
        h->values[i][j] = next[i][j];
        next[i][j] = NULL;
      }
  } else
    memcpy(h->cells, old_cells, sizeof old_cells);
  for (int i = 0; i < 8; i++)
    for (int j = 0; j < 4; j++)
      free(next[i][j]);
  snprintf(h->message, sizeof h->message, "%s",
           accepted
               ? grid_demo_word(h, "앱이 요청을 승인했습니다.",
                                "Host approved the request.")
               : grid_demo_word(h, "만료된 요청입니다.", "Stale request."));
  grid_demo_pending_clear(h);
  return;
fail:
  for (int i = 0; i < 8; i++)
    for (int j = 0; j < 4; j++)
      free(next[i][j]);
  snprintf(h->message, sizeof h->message, "%s",
           grid_demo_word(h, "메모리 부족", "Out of memory"));
}
static void grid_demo_pointer(GridDemo *h, int x, int y, int button) {
  if (button || h->search || h->detail || h->pending_id || x < h->area.x ||
      x >= h->area.x + h->area.width || y < h->area.y ||
      y >= h->area.y + h->area.height)
    return;
  TuiGridEvent e = tui_grid_click(h->grid, x - h->area.x, y - h->area.y,
                                  h->area.width, h->area.height);
  if (!strcmp(e.kind, "sort_request"))
    snprintf(h->message, sizeof h->message, "%s",
             grid_demo_word(h, "정렬 요청: 앱이 처리합니다.",
                            "Sort requested: handled by the host."));
}
static void grid_demo_handle(GridDemo *h, const char *action,
                             const char *text) {
  const char *command = !strcmp(action, "insert") ? text : action;
  if (h->detail) {
    if (!strcmp(action, "cancel")) {
      tui_document_free(h->detail);
      h->detail = NULL;
    } else
      tui_document_handle(h->detail, action, text);
    return;
  }
  if (h->search) {
    if (!strcmp(action, "cancel")) {
      tui_text_free(h->search);
      h->search = NULL;
    } else if (!strcmp(action, "activate")) {
      int found =
          tui_grid_find(h->grid, tui_text_value(h->search), 0, 0, 0, 100000);
      tui_text_free(h->search);
      h->search = NULL;
      snprintf(h->message, sizeof h->message, "%s",
               found ? grid_demo_word(h, "검색 일치", "Match found")
                     : grid_demo_word(h, "검색 결과 없음", "No match"));
    } else
      tui_text_handle(h->search, action, text);
    return;
  }
  if (h->pending_id) {
    if (!strcmp(command, "y") || !strcmp(command, "r"))
      grid_demo_approve(h, !strcmp(command, "y"));
    else if (!strcmp(action, "cancel")) {
      if (tui_grid_edit_session(h->grid))
        tui_grid_handle(h->grid, "cancel", 10, "");
      tui_grid_cancel_paste(h->grid);
      grid_demo_pending_clear(h);
      snprintf(h->message, sizeof h->message, "%s",
               grid_demo_word(h, "요청 취소", "Request cancelled"));
    }
    return;
  }
  TuiGridEvent event = {.kind = ""};
  if (tui_grid_edit_session(h->grid))
    event = tui_grid_handle(h->grid, action, h->area.height, text);
  else if (!strcmp(command, "/")) {
    h->search = tui_text_new("");
    if (h->search)
      tui_text_options(h->search, (TuiState){0}, 0, 0);
    return;
  } else if (!strcmp(command, "d")) {
    h->detail = tui_grid_details(h->grid);
    return;
  } else if (!strcmp(command, "p")) {
    if (tui_grid_request_paste(h->grid, "\"paste\tname\"\t\"raw\nvalue\"",
                               10000, NULL) == TUI_OK) {
      const TuiGridPasteRequest *p = tui_grid_pending_paste(h->grid);
      if (p)
        grid_demo_capture(h, p->id, 0, p->changes, p->change_count);
    } else
      snprintf(h->message, sizeof h->message, "%s",
               grid_demo_word(h, "편집할 수 없는 셀입니다.",
                              "This cell cannot be edited."));
    return;
  } else if (!strcmp(command, "c")) {
    char *value = NULL;
    if (tui_grid_copy(h->grid, 0, "NULL", &value) == TUI_OK) {
      char *clipped = tui_clip(value, 64, 1);
      if (clipped)
        snprintf(h->message, sizeof h->message, "%s%s",
                 grid_demo_word(h, "복사 원문: ", "Raw copy: "), clipped);
      free(clipped);
      free(value);
    }
    return;
  } else if (!strcmp(command, "v")) {
    TuiGridOptions options;
    h->density = !h->density;
    tui_grid_preset("data", &options);
    tui_grid_density(&options, h->density ? "comfortable" : "normal");
    tui_grid_configure(h->grid, &options);
    return;
  } else if (!strcmp(command, "b")) {
    if (!h->saved) {
      h->saved = tui_grid_save_view(h->grid);
      snprintf(h->message, sizeof h->message, "%s",
               grid_demo_word(h, "보기 저장됨", "View saved"));
    } else {
      tui_grid_restore_view(h->grid, h->saved);
      tui_grid_view_free(h->saved);
      h->saved = NULL;
      snprintf(h->message, sizeof h->message, "%s",
               grid_demo_word(h, "보기 복원됨", "View restored"));
    }
    return;
  } else
    event = tui_grid_handle(h->grid, action, h->area.height, text);
  if (!strcmp(event.kind, "edit_submit")) {
    TuiGridChange change = {event.row_id, event.column_id, event.value};
    grid_demo_capture(h, event.id, 1, &change, 1);
  } else if (!strcmp(event.kind, "edit_denied") ||
             !strcmp(event.kind, "paste_rejected"))
    snprintf(h->message, sizeof h->message, "%s",
             grid_demo_word(h, "편집할 수 없는 셀입니다.",
                            "This cell cannot be edited."));
}
#endif
