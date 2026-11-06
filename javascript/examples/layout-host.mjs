// Example host owns literal contents, global shortcuts and removal approval.
import * as ui from "../dist/index.js";
export class LayoutDemo {
  constructor(en = false) {
    this.en = en;
    this.density = "auto";
    this.active = true;
    this.hits = [];
    this.status = "";
    this.filter = new ui.Chip({
      id: "filter",
      label: this.word("최근", "Recent"),
      removable: true,
    });
    this.readonly = new ui.Chip({
      id: "fixed",
      label: this.word("읽기 전용", "Read only"),
      state: { read_only: true },
      removable: true,
    });
    this.disabled = new ui.Chip({
      id: "off",
      label: this.word("비활성", "Disabled"),
      state: { disabled: true },
      removable: true,
    });
  }
  word(ko, en) {
    return this.en ? en : ko;
  }
  draw(c, area, ascii) {
    this.hits = [];
    const tokens = ui.SpacingTokens.forWidth(this.density, area.width),
      layout = ui.stackRects(
        ui.rect(area.x, area.y, area.width, Math.max(0, area.height - 1)),
        [
          { id: "badges", min: 16, preferred: 20, weight: 0 },
          { id: "support", min: 24, preferred: 40, weight: 1 },
        ],
        tokens,
      );
    const badges = [
      new ui.Badge({ label: this.word("항목", "Items"), count: 123 }),
      new ui.Badge({
        label: this.word("선택", "Selected"),
        count: 0,
        state: { selected: true },
      }),
      new ui.Badge({
        label: this.word("비활성", "Disabled"),
        state: { disabled: true },
      }),
    ];
    for (const named of layout.rects) {
      if (!named.rect.width || !named.rect.height) continue;
      const inner = c.panel(
        named.rect,
        named.id === "badges"
          ? this.word("배지", "Badges")
          : this.word("칩·단축키", "Chips and shortcuts"),
        false,
        ascii,
      );
      let y = inner.y;
      if (named.id === "badges")
        for (const b of badges) {
          if (y >= inner.y + inner.height) break;
          b.draw(c, ui.rect(inner.x, y, inner.width, 1));
          y += 1 + tokens.controlGap;
        }
      else {
        for (const chip of [
          ...(this.active ? [this.filter] : []),
          this.readonly,
          this.disabled,
        ]) {
          if (y >= inner.y + inner.height) break;
          chip.draw(c, ui.rect(inner.x, y, inner.width, 1));
          for (const s of chip.line(inner.width).spans)
            this.hits.push({
              rect: ui.rect(inner.x + s.start, y, s.width, 1),
              chip,
              disabled: s.disabled,
            });
          y += 1 + tokens.controlGap;
        }
        new ui.Help([
          {
            key: "d",
            text: this.word("간격 변경", "Change density"),
            priority: 10,
          },
          {
            key: "x",
            text: this.word("필터 제거", "Remove filter"),
            priority: 5,
            disabled: !this.active,
          },
          {
            key: "r",
            text: this.word("사용 불가", "Unavailable"),
            disabled: true,
          },
        ]).draw(
          c,
          ui.rect(
            inner.x,
            y,
            inner.width,
            Math.max(0, inner.y + inner.height - y),
          ),
        );
      }
    }
    const label =
        this.density === "auto"
          ? this.word("자동", "auto")
          : this.density === "compact"
            ? this.word("촘촘", "compact")
            : this.word("여유", "comfortable"),
      text =
        this.status ||
        this.word("밀도: ", "Density: ") +
          label +
          this.word(" | 숨긴 패널: ", " | Hidden panes: ") +
          layout.hidden.length;
    if (area.height)
      c.write(
        area.x,
        area.y + area.height - 1,
        text,
        "hint",
        false,
        area.width,
      );
  }
  apply(e) {
    if (e.kind === "remove" && e.id === "filter" && this.active) {
      this.active = false;
      this.hits = [];
      this.status = this.word("필터를 제거했습니다.", "Filter removed.");
    }
  }
  handle(action, text = "") {
    const command = action === "insert" ? text : action;
    if (["x", "activate"].includes(command))
      this.apply(this.filter.requestRemove());
    else if (command === "d") {
      this.density = this.density === "comfortable" ? "compact" : "comfortable";
      this.hits = [];
      this.status =
        this.density === "compact"
          ? this.word("밀도: 촘촘", "Density: compact")
          : this.word("밀도: 여유", "Density: comfortable");
    }
  }
  pointer(x, y, button) {
    if (button !== 0) return;
    for (const h of this.hits) {
      const r = h.rect;
      if (x >= r.x && x < r.x + r.width && y >= r.y && y < r.y + r.height) {
        if (!h.disabled) this.apply(h.chip.requestRemove());
        return;
      }
    }
  }
}
