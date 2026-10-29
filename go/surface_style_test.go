package tuivory_test

import (
	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
	"testing"
)

func TestPlainTextBackgroundsAndExplicitRegionsAfterShow(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			doc, _ := ui.CandidateTokens()
			raw, _ := doc.Palette(theme, profile)
			p, _ := ui.Resolve(raw)
			p["custom"] = ui.Pair{FG: tcell.ColorWhite, BG: tcell.ColorMaroon}
			roles := []string{"body", "hint", "disabled", "info", "success", "warning", "error", "field", "button", "selection", "edited", "custom"}
			lines := []ui.ComponentLine{}
			for _, role := range roles {
				lines = append(lines, ui.ComponentLine{Text: "Label", Role: role, Spans: []ui.ComponentSpan{{Start: 10, Width: 8, Text: "Span", Role: role}}})
			}
			v, err := ui.NewRowsView(func(w, h int) []ui.ComponentLine { return lines }, p)
			if err != nil {
				t.Fatal(err)
			}
			s := drawingScreen(t)
			s.SetSize(40, 16)
			v.SetRect(0, 0, 40, 16)
			for _, preserve := range []bool{false, true} {
				v.PreserveBackgrounds = preserve
				v.Draw(s)
				s.Show()
				for y, role := range roles {
					expected := p[role].BG
					if !preserve && y < 7 {
						expected = p["surface"].BG
					}
					for _, x := range []int{0, 10, 17} {
						_, bg, _ := outputCell(t, s, x, y, map[int]string{0: "L", 10: "S", 17: " "}[x]).Decompose()
						if bg != expected {
							t.Fatalf("%s/%s role=%s preserve=%t x=%d bg=%v expected=%v", theme, profile, role, preserve, x, bg, expected)
						}
					}
				}
			}
			helper, err := ui.TextOnSurface(p, "success", "surface")
			if err != nil {
				t.Fatal(err)
			}
			fg, bg, _ := helper.Decompose()
			if bg != p["surface"].BG {
				t.Fatal("helper ignored actual surface")
			}
			if theme == "light" && profile == "16" && fg != p["surface"].FG {
				t.Fatal("success foreground must be corrected on light-16 surface")
			}
			onCanvas, _ := ui.TextOnSurface(p, "body", "body")
			_, bg, _ = onCanvas.Decompose()
			if bg != p["body"].BG {
				t.Fatal("explicit canvas lost")
			}
			for _, state := range []ui.ControlState{{Selected: true}, {Edited: true}} {
				rawStyle, _ := ui.ControlStyle(p, state, true)
				bound, _ := ui.ControlStyleOnSurface(p, state, true, "surface")
				if rawStyle != bound {
					t.Fatal("explicit control background changed")
				}
			}
			for _, ctor := range []func() (interface {
				SetRect(int, int, int, int)
				Draw(tcell.Screen)
			}, error){
				func() (interface {
					SetRect(int, int, int, int)
					Draw(tcell.Screen)
				}, error) {
					return ui.NewBreadcrumbView([]ui.PathItem{{ID: "r", Label: "Root"}, {ID: "c", Label: "Current"}}, p)
				},
				func() (interface {
					SetRect(int, int, int, int)
					Draw(tcell.Screen)
				}, error) {
					return ui.NewStatusView([]ui.StatusItem{{ID: "s", Text: "Success", Role: "success", Priority: 1}}, p)
				},
			} {
				view, err := ctor()
				if err != nil {
					t.Fatal(err)
				}
				view.SetRect(0, 14, 40, 1)
				view.Draw(s)
				s.Show()
				for x := 0; x < 40; x++ {
					_, _, st, _ := s.GetContent(x, 14)
					_, bg, _ := st.Decompose()
					if bg != p["surface"].BG {
						t.Fatalf("line background leaked at %s/%s x=%d", theme, profile, x)
					}
				}
			}
		}
	}
}
func TestTextSurfaceErrorsAndGridPreservation(t *testing.T) {
	doc, _ := ui.CandidateTokens()
	raw, _ := doc.Palette("dark", "256")
	p, _ := ui.Resolve(raw)
	if _, err := ui.TextOnSurface(p, "missing", "surface"); err == nil {
		t.Fatal("unknown text role accepted")
	}
	if _, err := ui.TextOnSurface(p, "body", "missing"); err == nil {
		t.Fatal("unknown surface accepted")
	}
	data, _ := ui.NewMemoryRows([]ui.GridRecord{{ID: "a", Cells: map[string]string{"name": "One"}}, {ID: "b", Cells: map[string]string{"name": "Two"}}})
	grid, _ := ui.NewGrid([]ui.GridColumn{{ID: "name", Label: "Name", Width: 12}}, data)
	view, _ := ui.NewGridView(grid, p, nil)
	s := drawingScreen(t)
	s.SetSize(40, 12)
	view.SetRect(0, 0, 40, 12)
	view.Draw(s)
	s.Show()
	if !view.PreserveBackgrounds {
		t.Fatal("grid must preserve its own background policy")
	}
	geo := grid.Geometry(40, 12)
	x := geo.Columns[0].Start
	_, _, st, _ := s.GetContent(x, geo.HeaderRows+1)
	_, bg, _ := st.Decompose()
	if bg != p["body"].BG {
		t.Fatal("simple grid canvas changed")
	}
	p["grid.base"] = ui.Pair{FG: tcell.ColorWhite, BG: tcell.ColorMaroon}
	opts, _ := ui.GridPreset("data")
	grid.SetOptions(opts)
	view.SetPalette(p)
	view.Draw(s)
	s.Show()
	geo = grid.Geometry(40, 12)
	x = geo.Columns[0].Start
	_, _, st, _ = s.GetContent(x, geo.HeaderRows+1)
	_, bg, _ = st.Decompose()
	if bg != tcell.ColorMaroon {
		t.Fatal("custom grid background lost")
	}
}

func TestDirectChoicesAndApplyBindLabelToSurface(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			styler, _ := ui.New(theme, profile)
			dropdown := tview.NewDropDown().SetLabel("Choice ").SetOptions([]string{"One", "Two"}, nil).SetCurrentOption(0)
			choice := ui.NewChoice("Choice ", []string{"One", "Two"}, 0, nil)
			styler.DropDown(dropdown)
			styler.Choice(choice)
			s := drawingScreen(t)
			s.SetSize(48, 4)
			for _, v := range []tview.Primitive{dropdown, choice} {
				v.SetRect(0, 0, 48, 4)
				v.Draw(s)
				s.Show()
				_, bg, _ := outputCell(t, s, 0, 0, "C").Decompose()
				if bg != styler.Styles.Surface {
					t.Fatal("standalone choice label retained default black", theme, profile)
				}
			}
			styler.Apply(ui.Roles{Surfaces: map[*tview.Box]ui.Surface{dropdown.Box: ui.Canvas}}, dropdown)
			dropdown.Draw(s)
			s.Show()
			_, bg, _ := outputCell(t, s, 0, 0, "C").Decompose()
			if bg != styler.Styles.Background {
				t.Fatal("Apply did not use host-selected canvas")
			}
		}
	}
}

func TestInheritedForegroundIsNotGuessed(t *testing.T) {
	p := ui.Palette{"body": {FG: tcell.ColorDefault, BG: tcell.ColorBlack}, "surface": {FG: tcell.ColorWhite, BG: tcell.ColorBlack}}
	style, err := ui.TextOnSurface(p, "body", "surface")
	if err != nil {
		t.Fatal(err)
	}
	fg, _, _ := style.Decompose()
	if fg != tcell.ColorDefault {
		t.Fatal("terminal-inherited foreground must be preserved")
	}
}
