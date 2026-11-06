import * as ui from "../dist/index.js";
export class ContainerDemo {
  constructor(en = false, ascii = false) {
    this.en = en;
    this.opened = false;
    this.status = "";
    this.base = new ui.Container(
      [{ id: "nav", track: { fixed: 20 } }, { id: "editor" }],
      { kind: "row", gap: 1, virtualWidth: 96 },
    );
    this.base.state.moveFocus(this.base.items);
    this.layers = new ui.Container([{ id: "background" }], { kind: "layers" });
    this.editor = new ui.Text(
      this.word(
        "편집 영역 한글 界",
        ascii ? "Editor area ASCII" : "Editor area Unicode 界",
      ),
    );
  }
  word(ko, en) {
    return this.en ? en : ko;
  }
  draw(c, area, ascii) {
    this.ox = area.x;
    this.oy = area.y;
    const pane = (id, child, focused) => {
      const inner = child.panel(
        ui.rect(0, 0, child.width, child.height),
        id === "nav"
          ? this.word("탐색", "Navigator")
          : this.word("편집", "Editor"),
        focused,
        ascii,
      );
      if (id === "nav")
        child.write(
          inner.x,
          inner.y,
          this.word("개요", "Overview"),
          "body",
          false,
          inner.width,
        );
      else this.editor.draw(child, inner, focused);
    };
    this.layers.draw(
      c,
      ui.rect(area.x, area.y, area.width, Math.max(0, area.height - 1)),
      (id, child, focused) => {
        if (id === "background")
          this.base.draw(child, ui.rect(0, 0, child.width, child.height), pane);
        else {
          const inner = child.panel(
            ui.rect(0, 0, child.width, child.height),
            this.word("팝업", "Modal"),
            false,
            ascii,
          );
          child.write(
            inner.x,
            inner.y,
            this.word("배경 입력 차단", "Background input blocked"),
            "body",
            false,
            inner.width,
          );
          child.write(
            inner.x,
            inner.y + 1,
            this.word("m / Esc 닫기", "m / Esc close"),
            "hint",
            false,
            inner.width,
          );
        }
      },
    );
    if (area.height)
      c.write(
        area.x,
        area.y + area.height - 1,
        this.status || this.word("스크롤: ", "Scroll: ") + this.base.scrollX,
        "hint",
        false,
        area.width,
      );
  }
  handle(action, text = "") {
    const command = action === "insert" ? text : action;
    if (command === "m" || (command === "cancel" && this.opened)) {
      this.opened = command === "m" ? !this.opened : false;
      this.layers.setItems([
        { id: "background" },
        ...(this.opened
          ? [
              {
                id: "popup",
                modal: true,
                centered: true,
                area: ui.rect(0, 0, 30, 6),
              },
            ]
          : []),
      ]);
      this.status = this.opened
        ? this.word("팝업 열림", "Popup open")
        : this.word("팝업 닫힘", "Popup closed");
    } else if (!this.opened) {
      if (command === "h" || command === "l") {
        this.base.scrollX = Math.max(
          0,
          this.base.scrollX + (command === "l" ? 4 : -4),
        );
        this.status = this.word("스크롤: ", "Scroll: ") + this.base.scrollX;
      } else if (command === "next" || command === "previous")
        this.base.state.moveFocus(this.base.items, command === "previous");
      else if (this.base.state.focused === "editor")
        this.editor.handle(action, text);
    }
  }
  pointer(x, y, button) {
    if (button === 0 && this.layers.pointer(x, y, true, true) === "background")
      this.base.pointer(x - this.ox, y - this.oy, true, true);
  }
}
