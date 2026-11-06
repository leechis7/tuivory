package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.util.List;
/** Example host owns clocks, business callbacks and cancellation approval. */
final class FeedbackHost {
  private final boolean en;
  private long now, frame;
  private final NoticeQueue queue = new NoticeQueue(4);
  private final Progress progress = new Progress("job");
  private DataState state;
  private String status;
  private Rect noticeArea = new Rect(0, 0, 0, 0), progressArea = noticeArea;
  FeedbackHost(boolean en) {
    this.en = en;
    var info = new Notice("info", word("저장했습니다.", "Saved."));
    info.expiresAt = 5;
    queue.push(info);
    var warning = new Notice("warning", word("선택한 항목이 없습니다.", "No items selected."));
    warning.severity = "warning";
    warning.expiresAt = 20;
    queue.push(warning);
    var error = new Notice("error", word("예제 작업 실패", "Demo operation failed"));
    error.detail = word("예제 데이터", "Sample only");
    error.severity = "error";
    var off = new NoticeAction("off", word("사용 불가", "Unavailable"));
    off.disabled = true;
    error.actions = List.of(off, new NoticeAction("retry", word("재시도", "Retry")));
    queue.push(error);
    progress.label = word("내보내기", "Export");
    progress.message = word("처리 중", "Working");
    progress.cancelLabel = word("[ 취소 ]", "[ Cancel ]");
    progress.current = 40;
    progress.total = 100;
    progress.cancellable = true;
    state = new DataState("empty", word("결과 없음", "No records"),
        word("앱이 데이터를 연결합니다.", "The app supplies data."));
    status =
        word("시간·요청 처리는 예제 앱이 결정합니다.", "This host owns time and request handling.");
  }
  private String word(String ko, String en) {
    return this.en ? en : ko;
  }
  void draw(Canvas c, Rect area, boolean ascii) {
    int remaining = Math.max(0, area.height() - 1), top = area.y(), height = Math.min(5, remaining);
    noticeArea = c.panel(
        new Rect(area.x(), top, area.width(), height), word("알림", "Notices"), false, ascii);
    top += height;
    remaining -= height;
    queue.draw(c, noticeArea, now);
    height = Math.min(5, remaining);
    progressArea = c.panel(
        new Rect(area.x(), top, area.width(), height), word("진행", "Progress"), false, ascii);
    top += height;
    remaining -= height;
    if (progress.status.equals("cancelled"))
      new DataState("empty", word("내보내기 취소됨", "Export cancelled"),
          word("앱이 취소 요청을 처리했습니다.", "The host handled cancellation."))
          .draw(c, progressArea);
    else
      progress.draw(c, progressArea, frame);
    height = Math.min(4, remaining);
    state.draw(c,
        c.panel(new Rect(area.x(), top, area.width(), height), word("데이터 상태", "Data state"),
            false, ascii));
    if (area.height() > 0)
      c.write(area.x(), area.y() + area.height() - 1, status, "hint", false, area.width());
  }
  private void apply(NoticeEvent event) {
    if (event.kind().equals("action") && event.action().equals("retry")) {
      var replacement = new Notice(event.id(), word("재시도 요청 처리", "Retry accepted"));
      replacement.severity = "success";
      queue.push(replacement);
      state = new DataState("ready", word("준비 완료", "Ready"),
          word("앱이 요청을 처리했습니다.", "The host accepted the request."));
      status = word("재시도 요청을 앱에서 처리했습니다.", "Retry request handled by the host.");
    } else if (event.kind().equals("dismiss")) {
      queue.dismiss(event.id());
      status = word("알림을 닫았습니다.", "Notice dismissed.");
    }
  }
  private void cancel() {
    if (progress.requestCancel().kind().equals("cancel")) {
      progress.status = "cancelled";
      status = word("취소 요청을 앱에서 처리했습니다.", "Cancel request handled by the host.");
    }
  }
  void handle(String action, String text) {
    String command = action.equals("insert") ? text : action;
    if (command.equals("t")) {
      now += 10;
      frame++;
      status = word("만료한 알림: ", "Expired notices: ") + queue.expire(now).size();
    } else if (command.equals("c"))
      cancel();
    else if (action.equals("click")) {
      String[] xy = text.split(" +");
      if (xy.length == 2)
        try {
          pointer(Integer.parseInt(xy[0]), Integer.parseInt(xy[1]), 0);
        } catch (NumberFormatException ignored) { /* Invalid host command leaves state unchanged. */
        }
    } else
      apply(queue.handle(action.equals("delete") ? "dismiss" : action, now, noticeArea.height()));
  }
  private static boolean contains(Rect r, int x, int y) {
    return x >= r.x() && x < r.x() + r.width() && y >= r.y() && y < r.y() + r.height();
  }
  void pointer(int x, int y, int button) {
    if (button != 0)
      return;
    if (contains(noticeArea, x, y))
      apply(queue.click(x - noticeArea.x(), y - noticeArea.y(), now));
    else if (contains(progressArea, x, y) && y - progressArea.y() == 2
        && x - progressArea.x() < Math.min(progressArea.width(), cells(progress.cancelLabel)))
      cancel();
  }
}
