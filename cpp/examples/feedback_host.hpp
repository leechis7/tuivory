#pragma once
#include "tuivory.hpp"
// Example host owns clocks, callbacks and cancellation approval.
class FeedbackDemo {
  bool en_;
  std::uint64_t now_ = 0, frame_ = 0;
  tuivory::NoticeQueue queue_{4};
  tuivory::Progress progress_;
  tuivory::DataState state_;
  tuivory::Rect notice_area_{}, progress_area_{};
  std::string status_;
  std::string word(const std::string &ko, const std::string &en) const {
    return en_ ? en : ko;
  }
  static bool contains(tuivory::Rect r, int x, int y) {
    return x >= r.x && x < r.x + r.width && y >= r.y && y < r.y + r.height;
  }
  void apply(const tuivory::NoticeEvent &e) {
    if (e.kind == "action" && e.action == "retry") {
      tuivory::Notice n;
      n.id = e.id;
      n.text = word("재시도 요청 처리", "Retry accepted");
      n.severity = "success";
      queue_.push(n);
      state_ = {
          "ready", word("준비 완료", "Ready"),
          word("앱이 요청을 처리했습니다.", "The host accepted the request.")};
      status_ = word("재시도 요청을 앱에서 처리했습니다.",
                     "Retry request handled by the host.");
    } else if (e.kind == "dismiss") {
      queue_.dismiss(e.id);
      status_ = word("알림을 닫았습니다.", "Notice dismissed.");
    }
  }
  void cancel() {
    if (progress_.request_cancel().kind == "cancel") {
      progress_.status = "cancelled";
      status_ = word("취소 요청을 앱에서 처리했습니다.",
                     "Cancel request handled by the host.");
    }
  }

public:
  explicit FeedbackDemo(bool en) : en_(en) {
    tuivory::Notice info;
    info.id = "info";
    info.text = word("저장했습니다.", "Saved.");
    info.expires_at = 5;
    queue_.push(info);
    tuivory::Notice warning;
    warning.id = "warning";
    warning.text = word("선택한 항목이 없습니다.", "No items selected.");
    warning.severity = "warning";
    warning.expires_at = 20;
    queue_.push(warning);
    tuivory::Notice error;
    error.id = "error";
    error.text = word("예제 작업 실패", "Demo operation failed");
    error.detail = word("예제 데이터", "Sample only");
    error.severity = "error";
    error.actions = {{"off", word("사용 불가", "Unavailable"), true},
                     {"retry", word("재시도", "Retry"), false}};
    queue_.push(error);
    progress_.id = "job";
    progress_.label = word("내보내기", "Export");
    progress_.message = word("처리 중", "Working");
    progress_.cancel_label = word("[ 취소 ]", "[ Cancel ]");
    progress_.current = 40;
    progress_.total = 100;
    progress_.cancellable = true;
    state_ = {"empty", word("결과 없음", "No records"),
              word("앱이 데이터를 연결합니다.", "The app supplies data.")};
    status_ = word("시간·요청 처리는 예제 앱이 결정합니다.",
                   "This host owns time and request handling.");
  }
  void draw(tuivory::Canvas &c, tuivory::Rect area, bool ascii) {
    int remaining = std::max(0, area.height - 1), top = area.y;
    auto panel = [&](int limit, const std::string &title) {
      int h = std::min(limit, remaining);
      auto r = c.panel({area.x, top, area.width, h}, title, false, ascii);
      remaining -= h;
      top += h;
      return r;
    };
    notice_area_ = panel(5, word("알림", "Notices"));
    queue_.draw(c, notice_area_, now_);
    progress_area_ = panel(5, word("진행", "Progress"));
    if (progress_.status == "cancelled")
      tuivory::DataState{"empty", word("내보내기 취소됨", "Export cancelled"),
                         word("앱이 취소 요청을 처리했습니다.",
                              "The host handled cancellation.")}
          .draw(c, progress_area_);
    else
      progress_.draw(c, progress_area_, frame_);
    state_.draw(c, panel(4, word("데이터 상태", "Data state")));
    if (area.height)
      c.write(area.x, area.y + area.height - 1, status_, "hint", false,
              area.width);
  }
  void handle(const std::string &action, const std::string &text = "") {
    auto command = action == "insert" ? text : action;
    if (command == "t") {
      now_ += 10;
      frame_++;
      auto count = queue_.expire(now_).size();
      status_ =
          word("만료한 알림: ", "Expired notices: ") + std::to_string(count);
    } else if (command == "c")
      cancel();
    else
      apply(queue_.handle(action == "delete" ? "dismiss" : action, now_,
                          notice_area_.height));
  }
  void pointer(int x, int y, int button) {
    if (button != 0)
      return;
    if (contains(notice_area_, x, y))
      apply(queue_.click(x - notice_area_.x, y - notice_area_.y, now_));
    else if (contains(progress_area_, x, y) && y - progress_area_.y == 2 &&
             x - progress_area_.x <
                 std::min(progress_area_.width,
                          tuivory::cells(progress_.cancel_label)))
      cancel();
  }
};
