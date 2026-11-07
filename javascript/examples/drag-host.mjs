const rect = (x = 0, y = 0, width = 0, height = 0) => ({ x, y, width, height });
import { Tree, Tabs, DragState, DropError } from "../dist/index.js";
// This host owns cross-component focus and approvals; the library owns gestures.
export class DragDemo {
  constructor(en = false, ascii = false) {
    this.en = en;
    this.tabFocus = false;
    this.pending = null;
    this.message = "";
    this.area = rect();
    this.tabArea = rect();
    this.treeArea = rect();
    this.tabs = new Tabs([
      { id: "a", title: this.word("데이터", "Data"), edited: true },
      { id: "b", title: this.word("로그", "Logs") },
      { id: "c", title: this.word("작업", "Tasks") },
      { id: "d", title: this.word("비활성", "Disabled"), disabled: true },
    ]);
    this.tree = new Tree([
      { id: "root", name: this.word("작업 공간", "Workspace"), branch: true },
      {
        id: "a",
        name: this.word("보고서", "Reports"),
        parent: "root",
        branch: true,
      },
      {
        id: "a1",
        name: this.word("월별 보고서", "Monthly report"),
        parent: "a",
      },
      {
        id: "b",
        name: this.word("보관함", "Archive"),
        parent: "root",
        branch: true,
      },
      { id: "b1", name: this.word("이전 자료", "Previous data"), parent: "b" },
      { id: "c", name: this.word("메모", "Notes"), parent: "root" },
    ]);
    this.tree.expanded = new Set(["root", "a"]);
    this.drag = new DragState(true);
    this.options = { autoScroll: true, hoverExpand: true };
  }
  word(ko, en) {
    return this.en ? en : ko;
  }
  get model() {
    return this.tabFocus ? this.tabs : this.tree;
  }
  draw(c, area, ascii = false) {
    this.area = area;
    this.tabArea = rect(area.x, area.y, area.width, Math.min(1, area.height));
    this.treeArea = rect(
      area.x,
      area.y + Math.min(2, area.height),
      area.width,
      Math.max(0, area.height - 6),
    );
    if (this.tabFocus) {
      this.tree.draw(c, this.treeArea, false, ascii);
      this.drag.draw(this.tabs, c, this.tabArea, true, ascii);
    } else {
      this.tabs.draw(c, this.tabArea, false, ascii);
      this.drag.draw(this.tree, c, this.treeArea, true, ascii);
    }
    let status =
      this.message ||
      this.word(
        "앱 승인 후에만 순서가 바뀝니다.",
        "Order changes only after host approval.",
      );
    if (this.pending) {
      const r = this.pending;
      status =
        this.word("승인 대기: ", "Pending approval: ") +
        r.sourceId +
        " -> " +
        r.targetId +
        " (" +
        r.position +
        ") | y / r";
    }
    const lines = [
      this.word(
        "Tab 대상 전환 | [ 이전 / ] 다음 | i 안으로 / o 밖으로",
        "Tab switch | [ previous / ] next | i inside / o outside",
      ),
      this.word(
        "마우스로 끌기 | d 드래그 켜기/끄기 | Esc 취소",
        "Drag with mouse | d toggle dragging | Esc cancel",
      ),
      status,
      this.word("드래그: ", "Dragging: ") +
        (this.drag.enabled ? "ON" : "OFF") +
        " | " +
        this.drag.phase,
    ];
    lines.forEach((line, i) => {
      const y = area.y + area.height - 4 + i;
      if (y >= area.y)
        c.write(area.x, y, line, i === 2 ? "info" : "hint", false, area.width);
    });
  }
  handle(action, text = "") {
    const command = action === "insert" ? text : action;
    if (this.pending) {
      if (command === "y") {
        try {
          const next = this.model.applyDrop(this.pending);
          if (this.tabFocus) this.tabs = next;
          else this.tree = next;
          this.message = this.word(
            "앱이 이동을 승인했습니다.",
            "Host approved the move.",
          );
        } catch (error) {
          if (!(error instanceof DropError)) throw error;
          this.message = error.reason;
        }
        this.pending = null;
      } else if (command === "r" || action === "cancel") {
        this.pending = null;
        this.message = this.word(
          "앱이 이동을 거절했습니다.",
          "Host rejected the move.",
        );
      }
      return;
    }
    if (action === "next" || action === "previous") {
      this.drag.cancel();
      this.tabFocus = !this.tabFocus;
      return;
    }
    if (action === "cancel") {
      this.drag.cancel();
      return;
    }
    if (command === "d") {
      this.drag.enabled = !this.drag.enabled;
      this.drag.cancel();
      return;
    }
    if (["[", "]", "i", "o"].includes(command)) {
      this.drag.cancel();
      try {
        this.pending = this.model.keyboardDrop(
          { "[": "previous", "]": "next", i: "inside", o: "outside" }[command],
          this.options,
        );
      } catch (error) {
        if (!(error instanceof DropError)) throw error;
        this.message = error.reason;
      }
      return;
    }
    this.drag.cancel();
    if (this.tabFocus)
      this.tabs.handle({ left: "previous", right: "next" }[action] || action);
    else this.tree.handle(action, this.treeArea.height);
  }
  pointer(x, y, button, kind = "down") {
    if (this.pending || button & 64 || ![0, 3].includes(button & 3)) return;
    const inside = (a) =>
      x >= a.x && x < a.x + a.width && y >= a.y && y < a.y + a.height;
    if (kind === "down") {
      let target;
      if (inside(this.tabArea)) target = true;
      else if (inside(this.treeArea)) target = false;
      else return;
      if (target !== this.tabFocus) {
        this.drag.cancel();
        this.tabFocus = target;
      }
    }
    const a = this.tabFocus ? this.tabArea : this.treeArea;
    if (kind !== "down" && !this.drag.captured) return;
    const request = this.drag.pointer(
      this.model,
      {
        action: kind,
        x: x - a.x,
        y: y - a.y,
        width: a.width,
        height: a.height,
      },
      this.options,
    );
    const outcome = this.drag.result;
    if (request) this.pending = request;
    if (kind === "up" && outcome === "" && inside(a)) {
      if (this.tabFocus) this.tabs.click(x - a.x, a.width);
      else this.tree.click(x - a.x, y - a.y, a.height);
    }
  }
}
