package tuivory_test

import (
	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
	"reflect"
	"testing"
)

func TestLegacyStyleHelpersMatchCanonicalSurfaces(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			styles, _ := ui.NewStyles(theme, profile)
			for _, custom := range []bool{false, true} {
				if custom {
					styles.Field = tcell.NewHexColor(0x213141)
					styles.FieldText = tcell.NewHexColor(0xc1d1e1)
					styles.Footer = tcell.ColorMaroon
					styles.Surface = tcell.ColorNavy
					styles.Text = tcell.ColorSilver
				}
				for _, pair := range [][2]tcell.Style{{styles.FieldStyle(), styles.TextStyle(ui.Field, ui.Body)}, {styles.FooterButtonStyle(), styles.TextStyle(ui.Footer, ui.Body)}, {styles.PopupCardStyle(), styles.TextStyle(ui.Panel, ui.Body)}} {
					if pair[0] != pair[1] {
						t.Fatal(theme, profile, custom, pair)
					}
				}
			}
			// A compatibility snapshot must not silently act as the live selection setting.
			before := styles.SelectionStyle()
			styles.SelectionText = tcell.ColorRed
			if styles.SelectionStyle() != before {
				t.Fatal("legacy snapshot unexpectedly changed rendering")
			}
			styles.SelectionFG = tcell.ColorGreen
			if fg, _, _ := styles.SelectionStyle().Decompose(); fg != tcell.ColorGreen {
				t.Fatal("live replacement ignored")
			}
			styler, _ := ui.New(theme, profile)
			table := func() *tview.Table {
				v := tview.NewTable().SetBorders(true).SetSelectable(true, true)
				v.SetCell(0, 0, tview.NewTableCell("Name").SetSelectable(false))
				v.SetCell(0, 1, tview.NewTableCell("Value").SetSelectable(false))
				v.SetCell(1, 0, tview.NewTableCell("한글"))
				v.SetCell(1, 1, tview.NewTableCell("界"))
				v.Select(1, 1)
				v.SetRect(0, 0, 30, 7)
				return v
			}
			a, b := table(), table()
			styler.Table(a)
			styler.TableOn(b, ui.Canvas)
			first, second := drawingScreen(t), drawingScreen(t)
			a.Draw(first)
			first.Show()
			b.Draw(second)
			second.Show()
			ca, wa, ha := first.GetContents()
			cb, wb, hb := second.GetContents()
			if wa != wb || ha != hb || !reflect.DeepEqual(ca, cb) {
				t.Fatal("Table and explicit Canvas output differ", theme, profile)
			}
		}
	}
}

func lifecycleGrid(t *testing.T) *ui.Grid {
	t.Helper()
	source, _ := ui.NewMemoryRows([]ui.GridRecord{{ID: "r1", Cells: map[string]string{"name": "A", "value": "1"}}, {ID: "r2", Cells: map[string]string{"name": "B", "value": "2"}}})
	g, err := ui.NewGrid([]ui.GridColumn{{ID: "name", Width: 12}, {ID: "value", Width: 12}}, source)
	if err != nil {
		t.Fatal(err)
	}
	return g
}
func TestLegacyGridClickAndPointerMigration(t *testing.T) {
	for _, header := range []bool{false, true} {
		old, new := lifecycleGrid(t), lifecycleGrid(t)
		geo := new.Geometry(40, 8)
		x := geo.Columns[1].Start
		y := geo.HeaderRows
		kind := ""
		if header {
			y = 0
			kind = "@header"
		}
		a := old.Click("r1", kind, x, 40, 8)
		b := new.Pointer("click", x, y, 40, 8, false)
		if !reflect.DeepEqual(a, b) || old.RowID != new.RowID || old.ColumnID != new.ColumnID {
			t.Fatal("migration changed click", header, a, b)
		}
	}
	// Direct legacy calls keep their original programmatic bypass semantics.
	old, new := lifecycleGrid(t), lifecycleGrid(t)
	opts := old.Options()
	opts.DisableMouse = true
	old.SetOptions(opts)
	new.SetOptions(opts)
	geo := new.Geometry(40, 8)
	if e := old.Click("r2", "", geo.Columns[1].Start, 40, 8); e.Kind == "" {
		t.Fatal("legacy behavior changed")
	}
	if e := new.Pointer("click", geo.Columns[1].Start, geo.HeaderRows, 40, 8, false); e.Kind != "" {
		t.Fatal("pointer bypassed DisableMouse")
	}
	if !new.Focus("r2", "value") || new.Handle("select", 8).Kind == "" {
		t.Fatal("programmatic replacement failed")
	}
}
