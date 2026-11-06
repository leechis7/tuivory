// Example host owns clock advancement, business callbacks and cancellation.
import * as ui from "../dist/index.js";
export class FeedbackDemo {
  constructor(en = false) {
    this.en = en;
    this.now = this.frame = 0;
    this.queue = new ui.NoticeQueue(4);
    this.queue.push({
      id: "info",
      text: this.word("저장했습니다.", "Saved."),
      expiresAt: 5,
    });
    this.queue.push({
      id: "warning",
      text: this.word("선택한 항목이 없습니다.", "No items selected."),
      severity: "warning",
      expiresAt: 20,
    });
    this.queue.push({
      id: "error",
      text: this.word("예제 작업 실패", "Demo operation failed"),
      detail: this.word("예제 데이터", "Sample only"),
      severity: "error",
      actions: [
        {
          id: "off",
          label: this.word("사용 불가", "Unavailable"),
          disabled: true,
        },
        { id: "retry", label: this.word("재시도", "Retry") },
      ],
    });
    this.progress = new ui.Progress({
      id: "job",
      label: this.word("내보내기", "Export"),
      message: this.word("처리 중", "Working"),
      cancelLabel: this.word("[ 취소 ]", "[ Cancel ]"),
      current: 40,
      total: 100,
      cancellable: true,
    });
    this.state = new ui.DataState(
      "empty",
      this.word("결과 없음", "No records"),
      this.word("앱이 데이터를 연결합니다.", "The app supplies data."),
    );
    this.status = this.word(
      "시간·요청 처리는 예제 앱이 결정합니다.",
      "This host owns time and request handling.",
    );
    this.noticeArea = this.progressArea = ui.rect();
  }
  word(ko, en) {
    return this.en ? en : ko;
  }
  draw(c, area, ascii) {
    let remaining = Math.max(0, area.height - 1),
      top = area.y;
    const panel = (limit, title) => {
      const height = Math.min(limit, remaining),
        r = c.panel(
          ui.rect(area.x, top, area.width, height),
          title,
          false,
          ascii,
        );
      remaining -= height;
      top += height;
      return r;
    };
    this.noticeArea = panel(5, this.word("알림", "Notices"));
    this.queue.draw(c, this.noticeArea, this.now);
    this.progressArea = panel(5, this.word("진행", "Progress"));
    if (this.progress.status === "cancelled")
      new ui.DataState(
        "empty",
        this.word("내보내기 취소됨", "Export cancelled"),
        this.word(
          "앱이 취소 요청을 처리했습니다.",
          "The host handled cancellation.",
        ),
      ).draw(c, this.progressArea);
    else this.progress.draw(c, this.progressArea, this.frame);
    this.state.draw(c, panel(4, this.word("데이터 상태", "Data state")));
    if (area.height)
      c.write(
        area.x,
        area.y + area.height - 1,
        this.status,
        "hint",
        false,
        area.width,
      );
  }
  apply(event) {
    if (event.kind === "action" && event.action === "retry") {
      this.queue.push({
        id: event.id,
        text: this.word("재시도 요청 처리", "Retry accepted"),
        severity: "success",
      });
      this.state = new ui.DataState(
        "ready",
        this.word("준비 완료", "Ready"),
        this.word(
          "앱이 요청을 처리했습니다.",
          "The host accepted the request.",
        ),
      );
      this.status = this.word(
        "재시도 요청을 앱에서 처리했습니다.",
        "Retry request handled by the host.",
      );
    } else if (event.kind === "dismiss") {
      this.queue.dismiss(event.id);
      this.status = this.word("알림을 닫았습니다.", "Notice dismissed.");
    }
  }
  cancel() {
    if (this.progress.requestCancel().kind === "cancel") {
      this.progress.status = "cancelled";
      this.status = this.word(
        "취소 요청을 앱에서 처리했습니다.",
        "Cancel request handled by the host.",
      );
    }
  }
  handle(action, text = "") {
    const command = action === "insert" ? text : action;
    if (command === "t") {
      this.now += 10;
      this.frame++;
      const count = this.queue.expire(this.now).length;
      this.status = this.word("만료한 알림: ", "Expired notices: ") + count;
    } else if (command === "c") this.cancel();
    else
      this.apply(
        this.queue.handle(
          action === "delete" ? "dismiss" : action,
          this.now,
          this.noticeArea.height,
        ),
      );
  }
  pointer(x, y, button) {
    if (button !== 0) return;
    const inside = (r) =>
      x >= r.x && x < r.x + r.width && y >= r.y && y < r.y + r.height;
    if (inside(this.noticeArea))
      this.apply(
        this.queue.click(
          x - this.noticeArea.x,
          y - this.noticeArea.y,
          this.now,
        ),
      );
    else if (
      inside(this.progressArea) &&
      y - this.progressArea.y === 2 &&
      x - this.progressArea.x <
        Math.min(this.progressArea.width, ui.cells(this.progress.cancelLabel))
    )
      this.cancel();
  }
}
