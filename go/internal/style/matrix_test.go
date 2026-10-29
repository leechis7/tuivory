package style

import (
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"strings"
	"testing"

	"github.com/gdamore/tcell/v2"
)

func styleSnapshot(st tcell.Style) [3]uint64 {
	fg, bg, a := st.Decompose()
	return [3]uint64{uint64(fg), uint64(bg), uint64(a)}
}

func TestStyleMatrixMatchesOriginalLazyOra(t *testing.T) {
	data, err := os.ReadFile("testdata/lazyora-matrix.json")
	if err != nil {
		t.Fatal(err)
	}
	var expected map[string]map[string][3]uint64
	if err := json.Unmarshal(data, &expected); err != nil {
		t.Fatal(err)
	}
	if len(expected) != 12 {
		t.Fatal("missing source profiles")
	}
	for key, want := range expected {
		t.Run(key, func(t *testing.T) {
			parts := strings.Split(key, "-")
			s, err := NewStyles(parts[0], parts[1])
			if err != nil {
				t.Fatal(err)
			}
			got := map[string][3]uint64{}
			put := func(name string, st tcell.Style) { got[name] = styleSnapshot(st) }
			put("field", s.FieldStyle())
			put("selection", s.SelectionStyle())
			put("button", s.ButtonStyle())
			put("button.focus", s.ButtonFocusStyle())
			// Historical raw disabled color; the current adapter has separate regression coverage.
			put("disabled", tcell.StyleDefault.Foreground(s.Disabled).Background(s.Surface))
			put("edited", s.EditedStyle())
			put("editor", s.EditorStyle())
			for surface := Canvas; surface <= Editor; surface++ {
				for role := Body; role <= Warning; role++ {
					put(fmt.Sprintf("text/%d/%d", surface, role), s.TextStyle(surface, role))
				}
				for _, focused := range []bool{false, true} {
					put(fmt.Sprintf("border/%d/%t", surface, focused), s.BorderStyle(focused, s.SurfaceColor(surface)))
				}
			}
			for _, active := range []bool{false, true} {
				put(fmt.Sprintf("header/%t", active), s.GridHeaderStyle(active))
			}
			for _, focused := range []bool{false, true} {
				for _, edited := range []bool{false, true} {
					put(fmt.Sprintf("active/%t/%t", focused, edited), s.GridActiveStyle(focused, edited))
				}
			}
			for row := 1; row <= 2; row++ {
				for _, current := range []bool{false, true} {
					for _, null := range []bool{false, true} {
						for _, edited := range []bool{false, true} {
							for _, inRange := range []bool{false, true} {
								put(fmt.Sprintf("cell/%d/%t/%t/%t/%t", row, current, null, edited, inRange), s.GridCellStyle(CellState{Row: row, CurrentRow: current, Null: null, Edited: edited, InRange: inRange}))
							}
						}
					}
				}
			}
			for surface := Canvas; surface <= Editor; surface++ {
				for kind := SyntaxKeyword; kind <= SyntaxParameter; kind++ {
					base := tcell.StyleDefault.Foreground(s.SurfaceText(surface)).Background(s.SurfaceColor(surface))
					put(fmt.Sprintf("syntax/%d/%d", surface, kind), s.SyntaxStyle(kind, base))
				}
			}
			put("dropdown", s.DropDownStyle())
			grid := reflect.ValueOf(s.GridColors())
			for i := 0; i < grid.NumField(); i++ {
				name := grid.Type().Field(i).Name
				got["gridcolor/"+strings.ToLower(name[:1])+name[1:]] = [3]uint64{grid.Field(i).Uint(), 0, 0}
			}
			for _, active := range []bool{false, true} {
				put(fmt.Sprintf("tab/%t", active), s.TabStyle(active))
				put(fmt.Sprintf("comparison/%t", active), s.ComparisonHeaderStyle(active))
			}
			put("footer", s.FooterButtonStyle())
			put("splitter", s.SplitterStyle())
			got["divider"] = [3]uint64{uint64(s.GridDividerColor()), 0, 0}
			put("gutter", s.GridGutterStyle())
			put("gridstatus", s.GridStatusStyle())
			put("popupcard", s.PopupCardStyle())
			put("popupshadow", s.PopupShadowStyle())
			for _, limited := range []bool{false, true} {
				put(fmt.Sprintf("popupbackdrop/%t", limited), s.PopupBackdrop(tcell.StyleDefault.Bold(true), limited))
			}
			if len(got) != len(want) {
				t.Fatalf("source matrix coverage: %d != %d", len(got), len(want))
			}
			for name, expected := range want {
				if actual, ok := got[name]; !ok || actual != expected {
					t.Errorf("%s differs: got %v, expected %v", name, actual, expected)
				}
			}
		})
	}
}
