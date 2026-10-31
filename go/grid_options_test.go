package tuivory_test

import (
	"reflect"
	"strings"
	"testing"

	tcell "github.com/leechis7/tuivory/go/terminal"
	ui "github.com/leechis7/tuivory/go"
	tview "github.com/leechis7/tuivory/go/ui"
	"github.com/rivo/uniseg"
)

func optionGrid(t *testing.T) *ui.Grid {
	t.Helper()
	rows, err := ui.NewMemoryRows([]ui.GridRecord{
		{ID: "a", Cells: map[string]string{"name": "한글😀e\u0301 long", "value": "1\t2"}},
		{ID: "b", Cells: map[string]string{"name": "B\n\"C", "value": ""}},
		{ID: "c", Cells: map[string]string{"name": "C", "value": "003"}},
	})
	if err != nil {
		t.Fatal(err)
	}
	g, err := ui.NewGrid([]ui.GridColumn{{ID: "name", Label: "Name", Width: 12, Editable: true}, {ID: "value", Label: "Value", Width: 8, Editable: true}}, rows)
	if err != nil {
		t.Fatal(err)
	}
	return g
}
func TestGridOptionsPreserveStateAndRawValues(t *testing.T) {
	g := optionGrid(t)
	r := ui.GridRange{AnchorRow: "a", AnchorColumn: "name", EndRow: "b", EndColumn: "value"}
	if !g.SelectRange(r) || !g.Focus("b", "value") {
		t.Fatal("setup")
	}
	g.Top = 1
	g.Left = 1
	g.SetCellInfo(func(r ui.GridRecord, c ui.GridColumn) ui.GridCellInfo {
		return ui.GridCellInfo{Display: "formatted", HasDisplay: true, State: ui.ControlState{Edited: true}, Metadata: "TEXT"}
	})
	before := g.Handle("copy_range", 4).Text
	if before != "한글😀e\u0301 long\t\"1\t2\"\n\"B\n\"\"C\"\t" {
		t.Fatalf("raw TSV: %q", before)
	}
	widths := g.Columns()
	for _, preset := range []string{"data", "simple", "data"} {
		o, _ := ui.GridPreset(preset)
		if err := g.SetOptions(o); err != nil {
			t.Fatal(err)
		}
		g.Layout(40, 5)
		if g.RowID != "b" || g.ColumnID != "value" || g.SelectedRange() != r || g.Top != 1 || g.Left != 1 || !reflect.DeepEqual(g.Columns(), widths) {
			t.Fatal("style change lost state")
		}
		if got := g.Handle("copy_range", 4).Text; got != before {
			t.Fatalf("copy mutated %q", got)
		}
	}
	o := g.Options()
	o.Padding = 99
	if g.SetOptions(o) == nil || g.Options().Padding == 99 {
		t.Fatal("non-atomic validation")
	}
	o = g.Options()
	o.StatusFields = []string{}
	if err := g.SetOptions(o); err != nil || len(g.StatusItems()) != 0 {
		t.Fatal("empty status list should hide all fields")
	}
}
func TestGridVisibleAutoFitAndLargeCopy(t *testing.T) {
	source := &virtualRows{}
	g, _ := ui.NewGrid([]ui.GridColumn{{ID: "name", Width: 8}, {ID: "value", Width: 8}}, source)
	o, _ := ui.GridPreset("data")
	o.HorizontalLines = true
	o.Striped = true
	if err := g.SetOptions(o); err != nil {
		t.Fatal(err)
	}
	if err := g.SetColumnOptions("name", ui.GridColumnOptions{AutoFit: true, MinWidth: 4, MaxWidth: 20, Expand: 1}); err != nil {
		t.Fatal(err)
	}
	source.calls = 0
	g.Layout(80, 12)
	if source.calls > 12 {
		t.Fatalf("scanned outside viewport: %d", source.calls)
	}
	if !g.SelectRange(ui.GridRange{AnchorRow: "row-0", AnchorColumn: "name", EndRow: "row-99999", EndColumn: "value"}) {
		t.Fatal("range")
	}
	source.calls = 0
	if e := g.Handle("copy_range", 12); e.Kind != "copy_request" || e.Text != "" || source.calls > 3 {
		t.Fatal("large copy must delegate without reading all rows", e, source.calls)
	}
	if g.ResizeColumn("name", 21) || !g.AutoFitColumn("name", 6) {
		t.Fatal("width bounds")
	}
	if g.ColumnOptions("name").AutoFit || g.ColumnOptions("name").Expand != 0 {
		t.Fatal("manual fit must take precedence")
	}
	g.RequestFilter("old")
	old := g.Revision()
	g.RequestFilter("new")
	replacement, _ := ui.NewMemoryRows([]ui.GridRecord{{ID: "new"}})
	if g.ApplySource(old, replacement) || !g.ApplySource(g.Revision(), replacement) || g.ApplySource(g.Revision(), replacement) {
		t.Fatal("stale/duplicate response accepted")
	}
}
func TestGridOptionsNarrowUnicodeAndStates(t *testing.T) {
	g := optionGrid(t)
	g.SetCellInfo(func(r ui.GridRecord, c ui.GridColumn) ui.GridCellInfo {
		return ui.GridCellInfo{State: ui.ControlState{Edited: r.ID == "a", ReadOnly: c.ID == "value"}, Null: r.ID == "b" && c.ID == "value", Numeric: c.ID == "value", Metadata: "host type"}
	})
	for _, ascii := range []bool{false, true} {
		for _, density := range []string{"compact", "normal", "comfortable"} {
			o, _ := ui.GridPreset("data")
			o.ASCII = ascii
			o.HorizontalLines = true
			o.Striped = true
			o, _ = o.WithDensity(density)
			if err := g.SetOptions(o); err != nil {
				t.Fatal(err)
			}
			for _, overflow := range []string{"ellipsis", "clip", "scroll"} {
				if err := g.SetColumnOptions("name", ui.GridColumnOptions{Align: "center", Overflow: overflow}); err != nil {
					t.Fatal(err)
				}
				for w := 0; w < 80; w++ {
					for h := 0; h < 12; h++ {
						lines := g.Layout(w, h)
						if len(lines) > h {
							t.Fatalf("height overflow %dx%d", w, h)
						}
						for _, l := range lines {
							for _, s := range l.Spans {
								if s.Start < 0 || s.Start+s.Width > w || uniseg.StringWidth(s.Text) > s.Width {
									t.Fatalf("span overflow %dx%d %#v", w, h, s)
								}
							}
						}
					}
				}
			}
		}
	}
	if !g.Focus("a", "value") || g.Handle("activate", 6).Kind != "" {
		t.Fatal("readonly edit")
	}
	g.Focus("a", "name")
	if g.Handle("activate", 6).Kind != "edit" {
		t.Fatal("editable host cell")
	}
	found := false
	for _, s := range g.StatusItems() {
		if s.ID == "meta" && strings.Contains(s.Text, "host type") {
			found = true
		}
	}
	if !found {
		t.Fatal("active cell metadata not exposed")
	}
	for _, l := range g.Layout(60, 8) {
		for _, s := range l.Spans {
			if l.ID == "a" && s.Focused && s.Role != "grid.edited" {
				t.Fatal("edited state hidden", s)
			}
		}
	}
}
func TestGridPointerRangeResizeAndHover(t *testing.T) {
	g := optionGrid(t)
	o, _ := ui.GridPreset("data")
	g.SetOptions(o)
	geo := g.Geometry(60, 8)
	x := geo.Columns[0].Start
	g.Pointer("", x, 2, 60, 8, false)
	g.Pointer("move", x, 2, 60, 8, false)
	if g.RowID != "a" {
		t.Fatal("hover changed focus")
	}
	g.Pointer("down", x, 1, 60, 8, false)
	g.Pointer("move", geo.Columns[1].Start, 3, 60, 8, false)
	g.Pointer("up", 0, 0, 60, 8, false)
	if g.SelectedRange().EndRow != "c" || g.SelectionMode() != "range" {
		t.Fatal("drag range", g.SelectedRange())
	}
	g.Pointer("down", x, 1, 60, 8, false)
	g.Pointer("up", x, 1, 60, 8, false)
	if g.SelectionMode() != "cell" {
		t.Fatal("new click must collapse range")
	}
	divider := geo.Columns[0].Start + geo.Columns[0].Width
	g.Pointer("down", divider, 0, 60, 8, false)
	g.Pointer("move", divider+3, 0, 60, 8, false)
	g.Pointer("up", 0, 0, 60, 8, false)
	if g.Columns()[0].Width != 15 {
		t.Fatal("drag resize")
	}
}

func TestGridPhysicalOutputAndOverlayRestore(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, ascii := range []bool{false, true} {
				g := optionGrid(t)
				o, _ := ui.GridPreset("data")
				o.ASCII = ascii
				g.SetOptions(o)
				doc, _ := ui.CandidateTokens()
				raw, _ := doc.Palette(theme, profile)
				p, _ := ui.Resolve(raw)
				v, err := ui.NewGridView(g, p, nil)
				if err != nil {
					t.Fatal(err)
				}
				s := drawingScreen(t)
				s.SetSize(64, 14)
				v.SetRect(3, 2, 54, 9)
				v.Focus(func(_ tview.Primitive) {})
				for y := 0; y < 14; y++ {
					s.PutStr(0, y, strings.Repeat("界", 32))
				}
				s.Show()
				v.Draw(s)
				s.Show()
				divider := "│"
				if ascii {
					divider = "|"
				}
				geo := g.Geometry(54, 9)
				for y := 2; y < 4; y++ {
					outputCell(t, s, 3+geo.Gutter-1, y, divider)
				}
				before, _, _ := s.GetContents()
				before = append([]tcell.SimCell(nil), before...)
				ui.DimRegion(s, ui.CellRect{X: 4, Y: 3, Width: 12, Height: 4})
				s.Show()
				v.Draw(s)
				s.Show()
				after, _, _ := s.GetContents()
				for y := 2; y < 11; y++ {
					for x := 3; x < 57; x++ {
						a, b := before[y*64+x], after[y*64+x]
						if string(a.Bytes) != string(b.Bytes) || a.Style != b.Style {
							t.Fatalf("overlay restore %s/%s at %d,%d", theme, profile, x, y)
						}
					}
				}
				if g.Handle("copy_cell", 9).Text != "한글😀e\u0301 long" {
					t.Fatal("output damaged raw value")
				}
			}
		}
	}
}

func TestGridViewportDoesNotJumpWhenMovingUp(t *testing.T) {
	g, _ := ui.NewGrid([]ui.GridColumn{{ID: "name", Width: 12}}, &virtualRows{})
	o, _ := ui.GridPreset("data")
	o, _ = o.WithDensity("comfortable")
	g.SetOptions(o)
	g.Layout(40, 12)
	g.Handle("page_down", 12)
	if g.Row != 5 {
		t.Fatalf("density page: %d", g.Row)
	}
	g.Handle("last", 12)
	before := g.Geometry(40, 12).Top
	g.Handle("up", 12)
	if after := g.Geometry(40, 12).Top; after != before {
		t.Fatalf("up moved viewport %d -> %d", before, after)
	}
}
