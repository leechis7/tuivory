package tuivory_test

import (
	"encoding/json"
	ui "github.com/leechis7/tuivory/go"
	"os"
	"strings"
	"testing"
)

func TestGridRealCursorLifecycleAndClipping(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, ascii := range []bool{false, true} {
				g := editGrid(t)
				o, _ := ui.GridPreset("data")
				o.ASCII = ascii
				g.SetOptions(o)
				g.SetCellInfo(func(r ui.GridRecord, c ui.GridColumn) ui.GridCellInfo {
					return ui.GridCellInfo{State: ui.ControlState{Edited: c.ID == "name"}}
				})
				g.SetColumnOptions("name", ui.GridColumnOptions{Align: "right", Overflow: "scroll"})
				g.Handle("cell_pan_right", 8)
				tokens, _ := ui.CandidateTokens()
				raw, _ := tokens.Palette(theme, profile)
				palette, _ := ui.Resolve(raw)
				v, _ := ui.NewGridView(g, palette, nil)
				s := ui.NewSimulationScreen("UTF-8")
				s.Init()
				s.SetSize(80, 14)
				v.SetRect(3, 2, 60, 9)
				v.Focus(func(ui.Primitive) {})
				draw := func(w, h int, want bool) {
					t.Helper()
					v.SetRect(3, 2, w, h)
					v.Draw(s)
					s.Show()
					x, y, visible := s.GetCursor()
					c, ok := g.EditCursor(w, h)
					if visible != want || want && !ok {
						t.Fatalf("%s/%s ascii=%v: cursor %d,%d/%v expected %v, model=%+v/%v", theme, profile, ascii, x, y, visible, want, c, ok)
					}
					if want && (x != 3+c.X || y != 2+c.Y) {
						t.Fatal("cursor origin", x, y, c)
					}
					for _, line := range g.Layout(w, h) {
						if line.ID == "a" {
							for _, span := range line.Spans {
								if span.Role != "grid.divider" && strings.Contains(span.Text, "|") {
									t.Fatal("fake pipe caret", span)
								}
							}
						}
					}
				}
				draw(60, 9, false)
				g.BeginEdit("")
				g.EditInput("select_all", "")
				g.EditInput("insert", "한글👩‍💻e\u0301")
				draw(60, 9, true)
				g.EditInput("home", "")
				draw(60, 9, true)
				c, _ := g.EditCursor(60, 9)
				r, _, _, width := s.GetContent(3+c.X, 2+c.Y)
				if r != '한' || width != 2 || c.Width != 2 {
					t.Fatal("wide caret lead", r, width, c)
				}
				g.EditInput("end", "")
				for _, w := range []int{40, 20, 8, 3, 1, 0, 60} {
					_, ok := g.EditCursor(w, 9)
					draw(w, 9, ok)
				}
				v.Cursor = nil
				draw(60, 9, false)
				v.Cursor = g.EditCursor
				draw(60, 9, true)
				v.Blur()
				s.Show()
				if _, _, ok := s.GetCursor(); ok {
					t.Fatal("blur cursor")
				}
				other, _ := ui.NewRowsView(func(int, int) []ui.ComponentLine { return nil }, palette)
				other.Cursor = func(int, int) (ui.GridCursor, bool) { return ui.GridCursor{X: 1, Y: 1}, true }
				other.SetRect(0, 0, 3, 3)
				other.Focus(func(ui.Primitive) {})
				other.Draw(s)
				v.Draw(s)
				s.Show()
				if x, y, ok := s.GetCursor(); !ok || x != 1 || y != 1 {
					t.Fatal("unfocused grid stole another cursor", x, y, ok)
				}
				other.Blur()
				v.Focus(func(ui.Primitive) {})
				draw(60, 9, true)
				g.EditInput("null", "")
				draw(60, 9, false)
				g.EditInput("null", "")
				draw(60, 9, true)
				g.EditInput("submit", "")
				session, _ := g.EditSession()
				draw(60, 9, false)
				g.ResolveEdit(session.ID, "retry", nil)
				draw(60, 9, true)
				g.Focus("c", "name")
				draw(60, 2, false)
				g.Focus("a", "name")
				draw(60, 9, true)
				g.InvalidateRequests()
				draw(60, 9, false)
				g.BeginEdit("x")
				draw(60, 9, true)
				g.CancelEdit()
				draw(60, 9, false)
				g.BeginEdit("x")
				g.EditInput("submit", "")
				session, _ = g.EditSession()
				g.ResolveEdit(session.ID, "", nil)
				draw(60, 9, false)
				g.BeginEdit("x")
				g.EditInput("home", "")
				s.SetSize(4, 14)
				draw(60, 9, false)
				s.SetSize(80, 14)
				draw(60, 9, true)
				empty, _ := ui.NewMemoryRows(nil)
				g.SetSource(empty)
				draw(60, 9, false)
				s.Fini()
			}
		}
	}
}
func TestGridCursorMouseUsesSameViewport(t *testing.T) {
	g := editGrid(t)
	g.BeginEdit("A한글👩‍💻e\u0301Z")
	g.EditInput("home", "")
	g.EditInput("right", "")
	geo := g.Geometry(40, 8)
	c, _ := g.EditCursor(40, 8)
	g.Pointer("click", c.X, c.Y, 40, 8, false)
	g.EditInput("insert", "X")
	session, _ := g.EditSession()
	if session.Value.Text != "AX한글👩‍💻e\u0301Z" {
		t.Fatal(session.Value.Text)
	}
	_ = geo
}

func TestSharedGridCursorCases(t *testing.T) {
	raw, err := os.ReadFile("testdata/grid-cursor-cases.json")
	if err != nil {
		t.Fatal(err)
	}
	// JSON uses snake_case for the shared language-neutral fixture.
	var fixture struct {
		Cases []struct {
			ID, Text         string
			Cursor, Width, X int
			VisibleText      string `json:"visible_text"`
		}
	}
	if err = json.Unmarshal(raw, &fixture); err != nil {
		t.Fatal(err)
	}
	for _, c := range fixture.Cases {
		t.Run(c.ID, func(t *testing.T) {
			rows, _ := ui.NewMemoryRows([]ui.GridRecord{{ID: "r", Cells: map[string]string{"c": c.Text}}})
			g, _ := ui.NewGrid([]ui.GridColumn{{ID: "c", Width: c.Width, Editable: true}}, rows)
			g.SetOptions(ui.GridOptions{HideMarkers: true, HideHeader: true})
			g.SetEditOptions(ui.GridEditOptions{Enabled: true})
			g.BeginEdit("")
			g.EditInput("select_all", "")
			g.EditInput("left", "")
			for i := 0; i < c.Cursor; i++ {
				g.EditInput("right", "")
			}
			pos, ok := g.EditCursor(c.Width, 2)
			if !ok || pos.X != c.X || pos.Y != 0 {
				t.Fatal("cursor", pos, ok, c)
			}
			lines := g.Layout(c.Width, 2)
			if got := strings.TrimRight(lines[0].Spans[0].Text, " "); got != c.VisibleText {
				t.Fatalf("text %q != %q", got, c.VisibleText)
			}
		})
	}
}
