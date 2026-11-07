import * as ui from "../dist/index.js";
export class DialogDemo {
  constructor(en = false) {
    this.en = en;
    this.opened = false;
    this.disabled = false;
    this.card = ui.rect();
    this.area = ui.rect();
    this.focus = new ui.Focus("root", [{ id: "editor" }]);
    this.editor = new ui.Text(
      this.word(
        "대화상자를 닫으면 편집합니다.",
        "Close the dialog to edit this text.",
      ),
    );
    this.dialog = new ui.Dialog(
      this.word("다시 연결", "Reconnect"),
      this.word(
        "작업을 다시 시도할까요?\n내용과 실행은 앱이 결정합니다.",
        "Retry the operation?\nThe host supplies content and actions.",
      ),
      this.buttons(),
      "cancel",
    );
    this.status = this.word("아직 실행하지 않았습니다.", "No action accepted.");
    this.open();
  }
  word(ko, en) {
    return this.en ? en : ko;
  }
  buttons() {
    return [
      { id: "retry", label: this.word("작업 다시 시도", "Retry operation") },
      { id: "settings", label: this.word("연결 설정 열기", "Open settings") },
      {
        id: "cancel",
        label: this.word("취소", "Cancel"),
        disabled: this.disabled,
      },
    ];
  }
  open() {
    if (!this.opened) {
      this.focus.open("dialog", [{ id: "buttons" }]);
      this.opened = true;
    }
    this.dialog.focus("cancel");
  }
  accept(e) {
    if (["activate", "cancel"].includes(e.kind)) {
      this.status = this.word("앱이 수락한 요청: ", "Host accepted: ") + e.id;
      this.opened = false;
      this.focus.close("dialog");
      this.card = ui.rect();
    }
  }
  draw(c, a, ascii) {
    this.area = a;
    this.editor.draw(
      c,
      ui.rect(a.x, a.y, a.width, Math.min(2, a.height)),
      !this.opened,
    );
    for (let y = a.y + 2; y < a.y + Math.max(0, a.height - 2); y++)
      c.write(
        a.x,
        y,
        (ascii ? ":" : this.en ? "界" : "가").repeat(a.width),
        "hint",
        false,
        a.width,
      );
    if (a.height >= 2)
      c.write(a.x, a.y + a.height - 2, this.status, "hint", false, a.width);
    if (a.height)
      c.write(
        a.x,
        a.y + a.height - 1,
        this.word(
          "m 열기 | x 취소 비활성 전환",
          "m reopen | x toggle Cancel disabled",
        ),
        "hint",
        false,
        a.width,
      );
    if (this.opened) {
      const w = Math.min(41, a.width),
        h = Math.min(12, Math.max(0, a.height - 2));
      this.card = new ui.Shadow(new ui.ShadowOptions("auto")).draw(
        c,
        ui.rect(
          a.x + Math.floor((a.width - w) / 2),
          a.y + Math.max(0, Math.floor((a.height - h) / 2) - 1),
          w,
          h,
        ),
        (child) =>
          this.dialog.draw(
            child,
            ui.rect(0, 0, child.width, child.height),
            true,
            ascii,
          ),
        ascii,
      ).card;
    }
  }
  handle(action, text = "") {
    const command = action === "insert" ? text : action;
    if (command === "m") this.open();
    else if (command === "x") {
      this.disabled = !this.disabled;
      this.dialog.setButtons(this.buttons());
    } else if (this.opened) this.accept(this.dialog.handle(action));
    else this.editor.handle(action === "activate" ? "newline" : action, text);
  }
  pointer(x, y, button) {
    if (button !== 0) return;
    if (this.opened) {
      if (contains(this.card, x, y))
        this.accept(this.dialog.click(x - this.card.x, y - this.card.y));
    } else if (contains(this.area, x, y))
      this.editor.click(
        x - this.area.x,
        y - this.area.y,
        this.area.width,
        Math.min(2, this.area.height),
      );
  }
}

function contains(r, x, y) {
  return x >= r.x && y >= r.y && x < r.x + r.width && y < r.y + r.height;
}
