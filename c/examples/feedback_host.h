#ifndef TUIVORY_EXAMPLE_FEEDBACK_HOST_H
#define TUIVORY_EXAMPLE_FEEDBACK_HOST_H
#include "tuivory.h"
#include <stdio.h>
#include <string.h>
/* Example host owns clocks, callbacks and cancellation approval. */
typedef struct {
  int en;
  unsigned long long now, frame;
  TuiNoticeQueue *queue;
  TuiProgress progress;
  TuiDataState state;
  TuiRect notice_area, progress_area;
  char status[256];
} FeedbackDemo;
static const char *feedback_word(const FeedbackDemo *h, const char *ko,
                                 const char *en) {
  return h->en ? en : ko;
}
static void feedback_demo_status(FeedbackDemo *h, const char *ko,
                                 const char *en) {
  snprintf(h->status, sizeof h->status, "%s", feedback_word(h, ko, en));
}
static void feedback_demo_free(FeedbackDemo *h) {
  tui_notice_queue_free(h->queue);
  h->queue = NULL;
}
static int feedback_demo_init(FeedbackDemo *h, int en) {
  memset(h, 0, sizeof *h);
  h->en = en;
  h->queue = tui_notice_queue_new(4);
  if (!h->queue)
    return 0;
  TuiNotice info = {.id = "info",
                    .text = feedback_word(h, "저장했습니다.", "Saved."),
                    .expires_at = 5};
  TuiNotice warning = {
      .id = "warning",
      .text = feedback_word(h, "선택한 항목이 없습니다.", "No items selected."),
      .severity = "warning",
      .expires_at = 20};
  TuiNoticeAction actions[] = {
      {"off", feedback_word(h, "사용 불가", "Unavailable"), 1},
      {"retry", feedback_word(h, "재시도", "Retry"), 0}};
  TuiNotice error = {
      .id = "error",
      .text = feedback_word(h, "예제 작업 실패", "Demo operation failed"),
      .detail = feedback_word(h, "예제 데이터", "Sample only"),
      .severity = "error",
      .actions = actions,
      .action_count = 2};
  if (tui_notice_queue_push(h->queue, &info) != TUI_OK ||
      tui_notice_queue_push(h->queue, &warning) != TUI_OK ||
      tui_notice_queue_push(h->queue, &error) != TUI_OK) {
    feedback_demo_free(h);
    return 0;
  }
  h->progress =
      (TuiProgress){.id = "job",
                    .label = feedback_word(h, "내보내기", "Export"),
                    .message = feedback_word(h, "처리 중", "Working"),
                    .cancel_label = feedback_word(h, "[ 취소 ]", "[ Cancel ]"),
                    .current = 40,
                    .total = 100,
                    .cancellable = 1};
  h->state = (TuiDataState){
      "empty", feedback_word(h, "결과 없음", "No records"),
      feedback_word(h, "앱이 데이터를 연결합니다.", "The app supplies data.")};
  feedback_demo_status(h, "시간·요청 처리는 예제 앱이 결정합니다.",
                       "This host owns time and request handling.");
  return 1;
}
static TuiRect feedback_panel(TuiCanvas *c, TuiRect area, int *top,
                              int *remaining, int limit, const char *title,
                              int ascii) {
  int height = *remaining < limit ? *remaining : limit;
  TuiRect r = tui_canvas_panel(c, (TuiRect){area.x, *top, area.width, height},
                               title, 0, ascii);
  *remaining -= height;
  *top += height;
  return r;
}
static void feedback_demo_draw(FeedbackDemo *h, TuiCanvas *c, TuiRect area,
                               int ascii) {
  int remaining = area.height > 0 ? area.height - 1 : 0, top = area.y;
  h->notice_area = feedback_panel(c, area, &top, &remaining, 5,
                                  feedback_word(h, "알림", "Notices"), ascii);
  tui_notice_queue_draw(h->queue, c, h->notice_area, h->now);
  h->progress_area =
      feedback_panel(c, area, &top, &remaining, 5,
                     feedback_word(h, "진행", "Progress"), ascii);
  if (h->progress.status && !strcmp(h->progress.status, "cancelled")) {
    TuiDataState cancelled = {
        "empty", feedback_word(h, "내보내기 취소됨", "Export cancelled"),
        feedback_word(h, "앱이 취소 요청을 처리했습니다.",
                      "The host handled cancellation.")};
    tui_data_state_draw(&cancelled, c, h->progress_area);
  } else
    tui_progress_draw(&h->progress, c, h->progress_area, h->frame);
  TuiRect state_area =
      feedback_panel(c, area, &top, &remaining, 4,
                     feedback_word(h, "데이터 상태", "Data state"), ascii);
  tui_data_state_draw(&h->state, c, state_area);
  if (area.height)
    tui_canvas_write(c, area.x, area.y + area.height - 1, h->status, "hint", 0,
                     area.width);
}
static void feedback_demo_apply(FeedbackDemo *h, TuiNoticeEvent event) {
  if (event.result != TUI_OK)
    return;
  if (!strcmp(event.kind, "action") && !strcmp(event.action, "retry")) {
    TuiNotice replacement = {
        .id = event.id,
        .text = feedback_word(h, "재시도 요청 처리", "Retry accepted"),
        .severity = "success"};
    if (tui_notice_queue_push(h->queue, &replacement) != TUI_OK) {
      feedback_demo_status(h, "알림 갱신 실패", "Notice update failed");
      return;
    }
    h->state = (TuiDataState){"ready", feedback_word(h, "준비 완료", "Ready"),
                              feedback_word(h, "앱이 요청을 처리했습니다.",
                                            "The host accepted the request.")};
    feedback_demo_status(h, "재시도 요청을 앱에서 처리했습니다.",
                         "Retry request handled by the host.");
  } else if (!strcmp(event.kind, "dismiss")) {
    tui_notice_queue_dismiss(h->queue, event.id);
    feedback_demo_status(h, "알림을 닫았습니다.", "Notice dismissed.");
  }
}
static void feedback_demo_cancel(FeedbackDemo *h) {
  TuiNoticeEvent e = tui_progress_request_cancel(&h->progress);
  if (!strcmp(e.kind, "cancel")) {
    h->progress.status = "cancelled";
    feedback_demo_status(h, "취소 요청을 앱에서 처리했습니다.",
                         "Cancel request handled by the host.");
  }
}
static void feedback_demo_handle(FeedbackDemo *h, const char *action,
                                 const char *text) {
  const char *command = !strcmp(action, "insert") ? text : action;
  if (!strcmp(command, "t")) {
    h->now += 10;
    h->frame++;
    TuiNoticeEvents *events = NULL;
    if (tui_notice_queue_expire(h->queue, h->now, &events) == TUI_OK)
      snprintf(h->status, sizeof h->status, "%s%zu",
               feedback_word(h, "만료한 알림: ", "Expired notices: "),
               tui_notice_events_count(events));
    tui_notice_events_free(events);
  } else if (!strcmp(command, "c"))
    feedback_demo_cancel(h);
  else
    feedback_demo_apply(h, tui_notice_queue_handle(
                               h->queue,
                               !strcmp(action, "delete") ? "dismiss" : action,
                               h->now, h->notice_area.height));
}
static int feedback_contains(TuiRect r, int x, int y) {
  return x >= r.x && x < r.x + r.width && y >= r.y && y < r.y + r.height;
}
static void feedback_demo_pointer(FeedbackDemo *h, int x, int y, int button) {
  if (button != 0)
    return;
  if (feedback_contains(h->notice_area, x, y))
    feedback_demo_apply(h,
                        tui_notice_queue_click(h->queue, x - h->notice_area.x,
                                               y - h->notice_area.y, h->now));
  else if (feedback_contains(h->progress_area, x, y) &&
           y - h->progress_area.y == 2) {
    int width = tui_cells(h->progress.cancel_label);
    if (width > h->progress_area.width)
      width = h->progress_area.width;
    if (x - h->progress_area.x < width)
      feedback_demo_cancel(h);
  }
}
#endif
