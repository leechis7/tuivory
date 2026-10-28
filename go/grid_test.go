package tuivory_test

import (
	"fmt"
	ui "github.com/leechis7/tuivory/go"
	"strconv"
	"strings"
	"testing"
)

type virtualRows struct{ calls int }

func (v *virtualRows) Len() int { return 100000 }
func (v *virtualRows) IndexOf(id string) int {
	n, e := strconv.Atoi(strings.TrimPrefix(id, "row-"))
	if e != nil || n < 0 || n >= v.Len() {
		return -1
	}
	return n
}
func (v *virtualRows) Row(n int) ui.GridRecord {
	v.calls++
	if n < 0 || n >= v.Len() {
		panic("outside source")
	}
	return ui.GridRecord{ID: fmt.Sprintf("row-%d", n), Cells: map[string]string{"name": fmt.Sprint("한글", n), "value": fmt.Sprint(n)}, State: ui.ControlState{Disabled: n == 1}}
}
func TestVirtualGridAndRequests(t *testing.T) {
	source := &virtualRows{}
	g, e := ui.NewGrid([]ui.GridColumn{{ID: "name", Label: "Name", Width: 8, Editable: true}, {ID: "value", Label: "Value", Width: 8}}, source)
	if e != nil {
		t.Fatal(e)
	}
	source.calls = 0
	lines := g.Layout(18, 7)
	if len(lines) != 7 || source.calls > 10 {
		t.Fatal("not virtual", len(lines), source.calls)
	}
	g.Handle("down", 7)
	if g.RowID != "row-2" {
		t.Fatal("disabled row")
	}
	g.Handle("select", 7)
	if g.Handle("copy", 7).Text != "한글2" {
		t.Fatal("copy leaked UI markers")
	}
	if g.Handle("activate", 7).Kind != "edit" {
		t.Fatal("edit request")
	}
	g.Handle("right", 7)
	if g.Handle("activate", 7).Kind != "" {
		t.Fatal("noneditable column")
	}
	g.Handle("last", 7)
	if g.RowID != "row-99999" {
		t.Fatal("last")
	}
	for _, line := range g.Layout(8, 4) {
		for _, span := range line.Spans {
			if span.Start+span.Width > 8 {
				t.Fatal("span overflow")
			}
		}
	}
	if g.RequestFilter("query").Text != "query" || g.Handle("sort", 4).Direction != "asc" {
		t.Fatal("requests")
	}
	if g.ResizeColumn("name", 0) || !g.ResizeColumn("name", 20) {
		t.Fatal("resize")
	}
}
func TestGridStableIDsAndEmpty(t *testing.T) {
	cols := []ui.GridColumn{{ID: "n", Width: 8, Editable: true}}
	a, _ := ui.NewMemoryRows([]ui.GridRecord{{ID: "a", Cells: map[string]string{"n": "A"}}, {ID: "b", Cells: map[string]string{"n": "B"}, State: ui.ControlState{ReadOnly: true}}})
	g, _ := ui.NewGrid(cols, a)
	g.Focus("b", "n")
	if g.Handle("activate", 3).Kind != "" {
		t.Fatal("readonly")
	}
	b, _ := ui.NewMemoryRows([]ui.GridRecord{a.Row(1), a.Row(0)})
	g.SetSource(b)
	if g.RowID != "b" || g.Row != 0 {
		t.Fatal("stable row ID")
	}
	empty, _ := ui.NewMemoryRows(nil)
	g.SetSource(empty)
	if len(g.Layout(20, 3)) != 2 || g.Handle("sort", 3).Kind != "sort" {
		t.Fatal("empty table")
	}
	if _, e := ui.NewMemoryRows([]ui.GridRecord{{ID: "a"}, {ID: "a"}}); e == nil {
		t.Fatal("duplicate row")
	}
}
