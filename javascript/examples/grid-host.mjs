import * as ui from "../dist/index.js";
/** Application-owned rows, approval choices and example navigation modes. */
export class GridDemo {
  constructor(en = false, ascii = false) {
    this.en = en;
    this.area = ui.rect();
    this.search = null;
    this.detail = null;
    this.pending = null;
    this.saved = null;
    this.message = "";
    this.density = false;
    this.rows = [
      {
        id: "r1",
        cells: {
          id: "01",
          name: this.word("한글 👩‍💻", ascii ? "ASCII sample" : "Unicode 👩‍💻"),
          value: "1234",
          state: this.word("준비", "Ready"),
        },
      },
      {
        id: "r2",
        cells: {
          id: "02",
          name: this.word("널 값", "Null value"),
          value: null,
          state: "NULL",
        },
      },
      {
        id: "r3",
        cells: {
          id: "03",
          name: this.word("비활성 행", "Disabled row"),
          value: "blocked",
          state: this.word("비활성", "Disabled"),
        },
        state: { disabled: true },
      },
      {
        id: "r4",
        cells: {
          id: "04",
          name: this.word("읽기 전용", "Read only"),
          value: "read-only",
          state: this.word("읽기 전용", "Read only"),
        },
        state: { read_only: true },
      },
      {
        id: "r5",
        cells: {
          id: "05",
          name: this.word("수정된 셀", "Edited cell"),
          value: "changed",
          state: this.word("수정됨", "Edited"),
        },
        cellStates: { value: { edited: true } },
      },
      {
        id: "r6",
        cells: {
          id: "06",
          name: this.word("빈 문자열", "Empty string"),
          value: "",
          state: this.word("비어 있음", "Empty"),
        },
      },
      {
        id: "r7",
        cells: {
          id: "07",
          name: "Find target",
          value: "long_value_for_horizontal_scrolling",
          state: this.word("검색 가능", "Searchable"),
        },
      },
      {
        id: "r8",
        cells: {
          id: "08",
          name: this.word("오류 표시", "Invalid cell"),
          value: "invalid",
          state: this.word("오류", "Invalid"),
        },
        cellStates: { value: { invalid: true } },
      },
    ];
    this.grid = new ui.Grid(
      [
        { id: "id", label: "ID", width: 5, pin: "left" },
        {
          id: "name",
          label: this.word("이름", "Name"),
          width: 18,
          editable: true,
        },
        {
          id: "value",
          label: this.word("값", "Value"),
          width: 22,
          editable: true,
        },
        {
          id: "state",
          label: this.word("상태", "State"),
          width: 12,
          pin: "right",
        },
      ],
      this.rows,
    );
    this.grid.setOptions(ui.gridPreset("data"));
    this.grid.setLabels(
      new ui.GridLabels({
        loading: this.word("로딩 중", "loading"),
        empty: this.word("비어 있음", "empty"),
        range: this.word("범위", "range"),
        more: this.word("더 있음", "more"),
      }),
    );
    this.grid.setEditOptions({
      enabled: true,
      startTyping: true,
      allowNull: true,
    });
    this.grid.setColumnOptions(
      "value",
      new ui.GridColumnOptions({
        align: "auto",
        overflow: "scroll",
        expand: 1,
      }),
    );
    this.grid.setCellInfo(
      (r, c) =>
        new ui.GridCellInfo({
          display: "1,234",
          hasDisplay: c.id === "value" && r.cells.value === "1234",
          numeric: c.id === "value" && r.cells.value === "1234",
        }),
    );
    this.grid.focus("r1", "name");
  }
  word(ko, en) {
    return this.en ? en : ko;
  }
  draw(c, a, ascii) {
    this.area = ui.rect(a.x, a.y, a.width, Math.max(0, a.height - 3));
    this.grid.draw(
      c,
      this.area,
      this.search === null && this.detail === null,
      ascii,
    );
    if (this.detail) {
      const inner = c.panel(
        this.area,
        this.word("원문 상세", "Raw cell details"),
        true,
        ascii,
      );
      this.detail.wrap = true;
      this.detail.draw(c, inner, true, ascii);
    }
    if (a.height >= 3) {
      const y = a.y + a.height - 3;
      if (this.search !== null) {
        const prompt = this.word("검색: ", "Find: "),
          offset = Math.min(a.width, ui.cells(prompt));
        c.write(a.x, y, prompt, "hint", false, a.width);
        this.search.draw(
          c,
          ui.rect(a.x + offset, y, Math.max(0, a.width - offset), 1),
        );
      } else c.write(a.x, y, this.message, "info", false, a.width);
    }
    if (a.height >= 2)
      c.write(
        a.x,
        a.y + a.height - 2,
        this.word(
          "Enter 편집 | / 검색 | d 원문 | p 붙여넣기 | c 복사",
          "Enter edit | / find | d details | p paste | c copy",
        ),
        "hint",
        false,
        a.width,
      );
    if (a.height)
      c.write(
        a.x,
        a.y + a.height - 1,
        this.word(
          "대기: y 승인/r 거절 | Ctrl+N NULL | v 간격 | b 보기 저장/복원",
          "Pending: y approve/r reject | Ctrl+N NULL | v density | b view",
        ),
        "hint",
        false,
        a.width,
      );
  }
  approve(accept) {
    const pending = this.pending;
    if (!pending) return;
    const [kind, data] = pending;
    if (!accept) {
      if (kind === "edit")
        this.grid.resolveEdit(
          data.id,
          this.word("거절됨: 수정 후 다시 제출", "Rejected: edit and retry"),
        );
      else this.grid.cancelPaste();
      this.message = this.word(
        "앱이 요청을 거절했습니다.",
        "Host rejected the request.",
      );
      this.pending = null;
      return;
    }
    const rows = structuredClone(this.rows),
      changes =
        kind === "edit"
          ? [
              {
                rowId: data.row_id,
                columnId: data.column_id,
                value: data.value,
              },
            ]
          : data.changes;
    for (const change of changes) {
      const row = rows.find((r) => r.id === change.rowId);
      if (row) {
        row.cells[change.columnId] = change.value;
        row.cellStates ??= {};
        row.cellStates[change.columnId] = { edited: true };
      }
    }
    const accepted =
      kind === "edit"
        ? this.grid.resolveEdit(data.id, "", rows)
        : this.grid.resolvePaste(data.id, rows);
    if (accepted) this.rows = rows;
    this.message = accepted
      ? this.word("앱이 요청을 승인했습니다.", "Host approved the request.")
      : this.word("만료된 요청입니다.", "Stale request.");
    this.pending = null;
  }
  handle(action, text = "") {
    const command = action === "insert" ? text : action;
    if (this.detail !== null) {
      if (action === "cancel") this.detail = null;
      else this.detail.handle(action, text);
      return;
    }
    if (this.search !== null) {
      if (action === "cancel") this.search = null;
      else if (action === "activate") {
        const found = this.grid.find(this.search.value);
        this.search = null;
        this.message = found
          ? this.word("검색 일치", "Match found")
          : this.word("검색 결과 없음", "No match");
      } else this.search.handle(action, text);
      return;
    }
    if (this.pending !== null) {
      if (command === "y" || command === "r") this.approve(command === "y");
      else if (action === "cancel") {
        if (this.grid.edit) this.grid.handle("cancel");
        this.grid.cancelPaste();
        this.pending = null;
        this.message = this.word("요청 취소", "Request cancelled");
      }
      return;
    }
    let event;
    if (this.grid.edit !== null)
      event = this.grid.handle(action, Math.max(0, this.area.height), text);
    else if (command === "/") {
      this.search = new ui.Text("", { multiline: false });
      return;
    } else if (command === "d") {
      this.detail = this.grid.details();
      return;
    } else if (command === "p")
      event = this.grid.paste('"paste\tname"\t"raw\nvalue"');
    else if (command === "c") event = this.grid.copySelection();
    else if (command === "v") {
      this.density = !this.density;
      this.grid.setOptions(
        ui
          .gridPreset("data")
          .withDensity(this.density ? "comfortable" : "normal"),
      );
      return;
    } else if (command === "b") {
      if (this.saved === null) {
        this.saved = this.grid.saveView();
        this.message = this.word("보기 저장됨", "View saved");
      } else {
        this.grid.restoreView(this.saved);
        this.saved = null;
        this.message = this.word("보기 복원됨", "View restored");
      }
      return;
    } else
      event = this.grid.handle(action, Math.max(0, this.area.height), text);
    if (event.kind === "edit_submit" || event.kind === "paste_request") {
      this.pending = [
        event.kind === "edit_submit" ? "edit" : "paste",
        structuredClone(event.data),
      ];
      this.message = this.word(
        "승인 대기: y 승인 / r 거절",
        "Pending approval: y approve / r reject",
      );
    } else if (event.kind === "copy")
      this.message = this.word("복사 원문: ", "Raw copy: ") + event.text;
    else if (event.kind === "paste_rejected" || event.kind === "edit_denied")
      this.message = this.word(
        "편집할 수 없는 셀입니다.",
        "This cell cannot be edited.",
      );
  }
  pointer(x, y, button) {
    if (
      button !== 0 ||
      this.detail !== null ||
      this.search !== null ||
      this.pending !== null
    )
      return;
    const a = this.area;
    if (x >= a.x && x < a.x + a.width && y >= a.y && y < a.y + a.height) {
      const e = this.grid.click(x - a.x, y - a.y, a.width, a.height);
      if (e.kind === "sort_request")
        this.message = this.word(
          "정렬 요청: 앱이 처리합니다.",
          "Sort requested: handled by the host.",
        );
    }
  }
}
