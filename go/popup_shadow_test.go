package tuivory_test

import (
	"encoding/json"
	tcell "github.com/leechis7/tuivory/go/terminal"
	ui "github.com/leechis7/tuivory/go"
	tview "github.com/leechis7/tuivory/go/ui"
	"os"
	"reflect"
	"testing"
)

func rect4(r ui.CellRect) [4]int { return [4]int{r.X, r.Y, r.Width, r.Height} }
func TestSharedPopupShadowGeometry(t *testing.T) {
	raw, _ := os.ReadFile("testdata/popup-shadow-cases.json")
	var data struct {
		Cases []struct {
			Name             string
			Anchor, Viewport [4]int
			Width, Height    int
			Options          ui.ShadowOptions
			Expected         struct{ Bounds, Card, Shadow [4]int }
		}
	}
	if e := json.Unmarshal(raw, &data); e != nil {
		t.Fatal(e)
	}
	for _, c := range data.Cases {
		a, v := c.Anchor, c.Viewport
		l := ui.PopupPlacement(ui.CellRect{X: a[0], Y: a[1], Width: a[2], Height: a[3]}, ui.CellRect{X: v[0], Y: v[1], Width: v[2], Height: v[3]}, c.Width, c.Height, c.Options)
		if rect4(l.Bounds) != c.Expected.Bounds || rect4(l.Card) != c.Expected.Card || rect4(l.Shadow) != c.Expected.Shadow {
			t.Fatal(c.Name, l, c.Expected)
		}
		for _, r := range l.ShadowRegions() {
			for y := 0; y < r.Height; y++ {
				for x := 0; x < r.Width; x++ {
					xx, yy := r.X+x, r.Y+y
					if xx >= l.Card.X && xx < l.Card.X+l.Card.Width && yy >= l.Card.Y && yy < l.Card.Y+l.Card.Height {
						t.Fatal("shadow overlaps card", c.Name)
					}
				}
			}
		}
	}
}
func TestShadowModesAfterShowAndRestoration(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, mode := range []ui.ShadowMode{ui.ShadowOff, ui.ShadowAuto, ui.ShadowSolid, ui.ShadowDim} {
				for _, glyph := range []string{"界", "한", "😀", "é"} {
					doc, _ := ui.CandidateTokens()
					tokens, _ := doc.Palette(theme, profile)
					p, _ := ui.Resolve(tokens)
					screen := drawingScreen(t)
					screen.SetSize(40, 14)
					base := p["surface"].Style().Italic(true)
					background := func() {
						screen.Fill('R', base)
						screen.Put(19, 5, glyph, base)
						screen.Put(5, 10, glyph, base)
						screen.Put(18, 10, glyph, base)
						screen.Show()
					}
					background()
					rows, _ := ui.NewRowsView(func(w, h int) []ui.ComponentLine { return []ui.ComponentLine{{Text: "Card", Role: "body"}} }, p)
					panel, _ := ui.NewPanelView(rows, p)
					view, e := ui.NewShadowView(panel, p, ui.ShadowOptions{Mode: mode})
					if e != nil {
						t.Fatal(e)
					}
					view.SetRect(4, 3, 16, 8)
					view.Draw(screen)
					screen.Show()
					l := view.Layout()
					outputCell(t, screen, 4, 3, "┌")
					_, _, attrs := outputCell(t, screen, 6, 5, "C").Decompose()
					if attrs&tcell.AttrDim != 0 {
						t.Fatal("shadow leaked into card", theme, profile, mode)
					}
					if mode != ui.ShadowOff {
						r := l.ShadowRegions()[0]
						if r.Width > 0 && r.Height > 0 {
							want := " "
							if mode == ui.ShadowDim {
								want = "R"
							} else if mode == ui.ShadowAuto {
								rr, gg, bb := p["surface"].BG.RGB()
								if rr <= 16 && gg <= 16 && bb <= 16 {
									want = "░"
								}
							}
							_, _, attrs := outputCell(t, screen, r.X, r.Y, want).Decompose()
							if mode == ui.ShadowDim && attrs&tcell.AttrDim == 0 {
								t.Fatal("missing dim")
							}
						}
					}
					if mode != ui.ShadowOff && glyph != "é" {
						if st := outputCell(t, screen, 20, 5, " "); st != base {
							t.Fatal("outside shadow style changed")
						}
						if st := outputCell(t, screen, 5, 10, " "); st != base {
							t.Fatal("outside left style changed")
						}
					}
					if st := outputCell(t, screen, 1, 1, "R"); st != base {
						t.Fatal("outside style changed")
					}
					// The host repaints the background when closing/moving; no stale snapshot is restored.
					background()
					if st := outputCell(t, screen, 6, 5, "R"); st != base {
						t.Fatal("redraw failed")
					}
				}
			}
		}
	}
}
func TestShadowNoHitTargetsAndInvalidConfig(t *testing.T) {
	doc, _ := ui.CandidateTokens()
	raw, _ := doc.Palette("dark", "256")
	p, _ := ui.Resolve(raw)
	called, focused := 0, 0
	child, _ := ui.NewRowsView(func(w, h int) []ui.ComponentLine { return []ui.ComponentLine{{Text: "Item", Role: "body"}} }, p)
	child.Click = func(ui.ComponentLine) { called++ }
	v, _ := ui.NewShadowView(child, p, ui.ShadowOptions{Mode: ui.ShadowAuto})
	v.SetRect(2, 2, 12, 6)
	s := drawingScreen(t)
	v.Draw(s)
	s.Show()
	l := v.Layout()
	for _, r := range l.ShadowRegions() {
		if r.Width > 0 && r.Height > 0 {
			if v.InRect(r.X, r.Y) {
				t.Fatal("shadow hit target")
			}
			v.MouseHandler()(tview.MouseLeftClick, tcell.NewEventMouse(r.X, r.Y, tcell.Button1, tcell.ModNone), func(tview.Primitive) { focused++ })
		}
	}
	if called != 0 || focused != 0 {
		t.Fatal(called, focused)
	}
	v.MouseHandler()(tview.MouseLeftClick, tcell.NewEventMouse(l.Card.X, l.Card.Y, tcell.Button1, tcell.ModNone), func(tview.Primitive) { focused++ })
	if called != 1 || focused != 1 {
		t.Fatal("card click lost")
	}
	before := v.Layout()
	if v.SetShadow(ui.ShadowOptions{Mode: "bad"}) == nil || v.SetShadow(ui.ShadowOptions{Mode: ui.ShadowAuto, OffsetX: -1}) == nil {
		t.Fatal("invalid options accepted")
	}
	if !reflect.DeepEqual(before, v.Layout()) {
		t.Fatal("bad config mutated")
	}
}

func TestShadowExtremeGeometryDoesNotWrap(t *testing.T) {
	limit := int(^uint(0) >> 1)
	l := ui.PopupPlacement(ui.CellRect{X: limit, Y: limit, Width: limit, Height: limit}, ui.CellRect{X: 100, Y: 50, Width: 10, Height: 10}, limit, limit, ui.ShadowOptions{Mode: ui.ShadowAuto, OffsetX: limit, OffsetY: limit})
	if l.Bounds != (ui.CellRect{X: 100, Y: 50, Width: 10, Height: 10}) || l.Card.Width != 1 || l.Card.Height != 1 {
		t.Fatal(l)
	}
}
