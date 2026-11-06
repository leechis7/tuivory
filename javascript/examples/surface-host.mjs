import * as ui from "../dist/index.js";
export class SurfaceDemo {
  constructor(en = false) {
    this.en = en;
    this.index = 1;
    this.roles = ["surface", "editor", "field", "button.focus"];
    this.input = new ui.Text(this.word("읽기 전용", "Read only"), {
      readOnly: true,
    });
  }
  word(ko, en) {
    return this.en ? en : ko;
  }
  draw(c, area, ascii) {
    new ui.Surface(this.roles[this.index]).draw(
      c,
      ui.rect(area.x, area.y, area.width, Math.max(0, area.height - 1)),
      (child) => {
        const w = child.width;
        [
          [this.word("바탕 위 문구", "Body on surface"), "body"],
          [this.word("보조 설명", "Secondary"), "hint"],
          [this.word("정상 상태", "Success"), "success"],
        ].forEach(([text, role], y) => child.write(0, y, text, role, false, w));
        new ui.Chip({
          id: "off",
          label: this.word("비활성", "Disabled"),
          state: { disabled: true },
        }).draw(child, ui.rect(0, 3, w, 1));
        new ui.Badge({
          label: this.word("선택", "Selected"),
          count: 0,
          state: { selected: true },
        }).draw(child, ui.rect(0, 4, w, 1));
        new ui.Chip({
          id: "edited",
          label: this.word("수정", "Edited"),
          state: { edited: true },
        }).draw(child, ui.rect(0, 5, w, 1));
        this.input.draw(child, ui.rect(0, 6, w, 1), false);
        new ui.Help([
          { key: "s", text: this.word("바탕 변경", "Change surface") },
        ]).draw(child, ui.rect(0, 8, w, 1));
      },
    );
    const labels = this.en
      ? ["panel", "editor", "field", "focused button"]
      : ["패널", "편집", "입력", "포커스 버튼"];
    if (area.height)
      c.write(
        area.x,
        area.y + area.height - 1,
        this.word("바탕: ", "Surface: ") + labels[this.index],
        "hint",
        false,
        area.width,
      );
  }
  handle(action, text = "") {
    if ((action === "insert" ? text : action) === "s")
      this.index = (this.index + 1) % 4;
  }
  pointer() {}
}
