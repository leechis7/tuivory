// Example host owns global keys, screen composition, callbacks and focus scopes.
import * as ui from "../dist/index.js";
export class MenuDemo {
  constructor(en = false, context = false, shadow = false) {
    this.en = en;
    this.shadowDemo = shadow;
    this.shadowIndex = 0;
    this.context = context;
    const word = (ko, eng) => (en ? eng : ko);
    this.menu = new ui.Menu([
      { id: "file", label: word("파일", "File"), mnemonic: "f" },
      {
        id: "new",
        parent: "file",
        label: word("새 문서", "New document"),
        mnemonic: "n",
        shortcut: "Ctrl+N",
      },
      { id: "line", parent: "file", separator: true },
      {
        id: "off",
        parent: "file",
        label: word("사용 불가", "Unavailable"),
        disabled: true,
      },
      {
        id: "recent",
        parent: "file",
        label: word("최근 문서", "Recent documents"),
        mnemonic: "r",
      },
      {
        id: "a",
        parent: "recent",
        label: word("예제 A", "Example A"),
        mnemonic: "a",
      },
      {
        id: "more",
        parent: "recent",
        label: word("더 보기", "More"),
        mnemonic: "m",
      },
      {
        id: "b",
        parent: "more",
        label: word("예제 B", "Example B"),
        mnemonic: "b",
      },
      { id: "edit", label: word("편집", "Edit"), mnemonic: "e" },
      {
        id: "copy",
        parent: "edit",
        label: word("복사", "Copy"),
        mnemonic: "c",
        shortcut: "Ctrl+C",
      },
    ]);
    this.menu.backLabel = word("뒤로", "Back");
    this.menu.emptyLabel = word("항목 없음", "(empty)");
    this.focus = new ui.Focus("root", [{ id: "editor" }]);
    this.editor = new ui.Text(
      word(
        "메뉴를 닫으면 여기를 편집할 수 있습니다.",
        "Close the menu to edit this text.",
      ),
    );
    this.area = this.bar = this.content = this.editorArea = ui.rect();
    this.anchor = null;
    this.status = word(
      "팝업 밖의 클릭은 배경에 전달되지 않습니다.",
      "Clicks outside the popup are blocked.",
    );
    this.open(context ? "" : "file");
  }
  open(id) {
    this.menu.open(id, "editor");
    if (this.menu.opened && this.focus.depth === 0)
      this.focus.open("popup", [{ id: "menu" }]);
    this.sync();
  }
  sync(event) {
    if (!this.menu.opened && this.focus.depth) this.focus.close("popup");
    if (event?.kind === "activate")
      this.status =
        (this.en ? "Selected: " : "선택: ") +
        this.menu.items.find((i) => i.id === event.id).label;
  }
  draw(c, area, ascii) {
    this.area = area;
    this.bar = ui.rect(area.x, area.y, area.width, this.context ? 0 : 1);
    this.editorArea = ui.rect(
      area.x,
      area.y + this.bar.height,
      area.width,
      Math.min(2, Math.max(0, area.height - this.bar.height)),
    );
    this.editor.draw(c, this.editorArea, !this.menu.opened);
    for (
      let y = this.editorArea.y + this.editorArea.height;
      y < area.y + Math.max(0, area.height - 2);
      y++
    )
      c.write(
        area.x,
        y,
        (ascii ? (this.shadowDemo ? ":" : ".") : this.en ? "界" : "가").repeat(
          area.width,
        ),
        "hint",
        false,
        area.width,
      );
    if (this.bar.height) this.menu.drawBar(c, this.bar);
    c.write(
      area.x,
      area.y + Math.max(0, area.height - 2),
      this.status,
      "hint",
      false,
      area.width,
    );
    const mode = this.shadowDemo
      ? ["auto", "solid", "off", "dim"][this.shadowIndex]
      : "off";
    const footer = this.shadowDemo
      ? this.en
        ? "Shadow: " + mode + " | s cycle | d Dim"
        : "그림자: " +
          ["자동", "검정", "끄기", "Dim"][this.shadowIndex] +
          " | s 변경 | d Dim"
      : this.en
        ? "F10 menu | Shift+F10 / right click"
        : "F10 메뉴 | Shift+F10 / 오른쪽 클릭";
    c.write(
      area.x,
      area.y + Math.max(0, area.height - 1),
      footer,
      "hint",
      false,
      area.width,
    );
    const anchor =
      this.anchor ??
      ui.rect(
        area.x + (this.context ? Math.floor(area.width / 2) : 1),
        area.y + (this.context ? 5 : 0),
        1,
        1,
      );
    if (this.context || this.anchor)
      c.write(anchor.x, anchor.y, "+", "warning", false, 1);
    if (this.menu.opened) {
      const [w, h] = this.menu.contentSize();
      const options = new ui.ShadowOptions(mode),
        placement = ui.popupPlacement(
          anchor,
          area,
          Math.min(48, Math.floor((w + 5) / 2) * 2),
          h + 4,
          options,
        );
      let local = ui.rect();
      const layout = new ui.Shadow(options).draw(
        c,
        placement.bounds,
        (child) => {
          local = this.menu.drawPopup(
            child,
            ui.rect(0, 0, child.width, child.height),
            this.menu.title() || (this.en ? "Context menu" : "문맥 메뉴"),
            1,
            ascii,
          );
        },
        ascii,
      );
      this.popup = layout.card;
      this.shadowLayout = layout;
      this.content = ui.rect(
        layout.card.x + local.x,
        layout.card.y + local.y,
        local.width,
        local.height,
      );
    } else this.content = ui.rect();
  }
  handle(action, text = "") {
    const command = action === "insert" ? text : action;
    if (this.shadowDemo && ["s", "d"].includes(command)) {
      this.shadowIndex =
        command === "d"
          ? 3
          : this.shadowIndex < 3
            ? (this.shadowIndex + 1) % 3
            : 0;
      this.content=ui.rect();
      return;
    }
    if (action === "f10") {
      if (this.menu.opened) this.sync(this.menu.close());
      else {
        this.anchor = null;
        this.open(this.context ? "" : "file");
      }
    } else if (action === "shift_f10") {
      this.anchor = ui.rect(
        this.area.x + Math.floor(this.area.width / 2),
        this.area.y + 4,
        1,
        1,
      );
      this.open("");
    } else if (this.menu.opened) {
      if (action === "cancel" && !this.focus.requestClose()) return;
      this.sync(
        this.menu.handle(
          action === "insert" ? "mnemonic" : action,
          text,
          this.content.height,
        ),
      );
    } else if (!this.focus.route("root").blocked)
      this.editor.handle(action === "activate" ? "newline" : action, text);
  }
  pointer(x, y, button) {
    const inside = (r) =>
      x >= r.x && x < r.x + r.width && y >= r.y && y < r.y + r.height;
    if (button === 2 && inside(this.area)) {
      this.anchor = ui.rect(x, y, 1, 1);
      this.open("");
    } else if (button === 0) {
      if (this.menu.opened && inside(this.content))
        this.sync(
          this.menu.click(
            x - this.content.x,
            y - this.content.y,
            this.content.height,
          ),
        );
      else if (inside(this.bar)) {
        const e = this.menu.barClick(x - this.bar.x, this.bar.width);
        if (e.kind === "open_request") {
          this.anchor = null;
          this.open(e.id);
        }
      } else if (!this.focus.route("root").blocked && inside(this.editorArea))
        this.editor.click(
          x - this.editorArea.x,
          y - this.editorArea.y,
          this.editorArea.width,
          this.editorArea.height,
        );
    }
  }
}
