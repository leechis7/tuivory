package main

import ui "github.com/leechis7/tuivory/go"

type translate func(string, string) string

func sampleGrid(tr translate) *ui.Grid {
	columns := []ui.GridColumn{{ID: "id", Label: "ID", Width: 5}, {ID: "name", Label: tr("이름", "Name"), Width: 18, Editable: true}, {ID: "email", Label: tr("이메일", "Email"), Width: 25, Editable: true}, {ID: "value", Label: tr("금액", "Amount"), Width: 10, Editable: true}, {ID: "state", Label: tr("상태", "State"), Width: 10}}
	rows := []ui.GridRecord{}
	for n, name := range []string{tr("김하늘", "Haneul Kim"), tr("이수정", "Sujeong Lee"), tr("박지수", "Jisu Park"), tr("최민준", "Minjun Choi"), tr("정유진", "Yujin Jung")} {
		id := string(rune('1' + n))
		rows = append(rows, ui.GridRecord{ID: "row-" + id, Cells: map[string]string{"id": id, "name": name, "email": "user" + id + "@example.test", "value": []string{"12500.00", "24000.00", "", "950.00", "3100.50"}[n], "state": tr("준비", "ready")}})
	}
	source, _ := ui.NewMemoryRows(rows)
	g, _ := ui.NewGrid(columns, source)
	g.Focus("row-2", "name")
	g.Handle("select", 12)
	return g
}
func configureGrid(g *ui.Grid, tr translate) {
	g.Labels = map[string]string{"row": tr("행", "R"), "column": tr("열", "C"), "null": "NULL", "selected": tr("선택", "selected"), "loading": tr("로딩", "loading"), "more": tr("추가", "more"), "sort": tr("정렬", "sort"), "filter": tr("필터", "filter")}
	g.SetCellInfo(func(r ui.GridRecord, c ui.GridColumn) ui.GridCellInfo {
		return ui.GridCellInfo{Null: r.Cells[c.ID] == "" && c.ID == "value", Numeric: c.ID == "value", Metadata: map[string]string{"id": "INTEGER", "name": "TEXT", "email": "TEXT", "value": "DECIMAL", "state": "TEXT"}[c.ID], State: ui.ControlState{Edited: r.ID == "row-2" && c.ID == "name", ReadOnly: !c.Editable}}
	})
	_ = g.SetColumnOptions("value", ui.GridColumnOptions{Align: "numeric", MinWidth: 4, MaxWidth: 40})
}
