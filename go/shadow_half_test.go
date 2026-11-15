package tuivory_test

import (
	ui "github.com/leechis7/tuivory/go"
	"testing"
)

func TestCompactShadowPhysicalCapsAndBackdrop(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, ascii := range []bool{false, true} {
				for _, glyph := range []string{"한", "界", "😀", "👩‍💻", "é"} {
					doc, _ := ui.CandidateTokens()
					tokens, _ := doc.Palette(theme, profile)
					p, _ := ui.Resolve(tokens)
					s := drawingScreen(t)
					s.SetSize(30, 12)
					base := p["surface"].Style().Italic(true).Underline(true)
					s.Fill('R', base)
					// CJK crossing the bottom strip's left and right boundary.
					s.Put(4, 9, glyph, base)
					s.Put(15, 9, glyph, base)
					s.Show()
					child := ui.NewBox().SetBackgroundColor(p["surface"].BG)
					v, err := ui.NewShadowView(child, p, ui.ShadowOptions{Mode: ui.ShadowAuto})
					if err != nil {
						t.Fatal(err)
					}
					v.ASCII = ascii
					v.SetRect(4, 3, 12, 7)
					v.Draw(s)
					s.Show()
					l := v.Layout()
					if l.Card != (ui.CellRect{X: 4, Y: 3, Width: 11, Height: 6}) {
						t.Fatal(l)
					}
					for _, point := range []struct {
						x, y   int
						symbol string
					}{{15, 3, "▄"}, {15, 4, " "}, {5, 9, "▀"}, {15, 9, "▀"}} {
						want := point.symbol
						if ascii {
							want = "."
						}
						st := outputCell(t, s, point.x, point.y, want)
						fg, bg, attrs := st.Decompose()
						if attrs != 0 {
							t.Fatal("backdrop attributes leaked into block", theme, profile, attrs)
						}
						if ascii || want != " " {
							if bg != p["surface"].BG || fg == bg {
								t.Fatal("invisible cap or changed backdrop", theme, profile, st)
							}
						}
						if v.InRect(point.x, point.y) {
							t.Fatal("shadow received input")
						}
					}
					if glyph != "é" {
						if outputCell(t, s, 4, 9, " ") != base || outputCell(t, s, 16, 9, " ") != base {
							t.Fatal("wide edge repair changed outside styles")
						}
					}
					if outputCell(t, s, 17, 9, "R") != base {
						t.Fatal("outside damaged")
					}
					// Host redraw on close: the old half blocks must disappear.
					s.Fill('N', base)
					s.Show()
					outputCell(t, s, 5, 9, "N")
				}
			}
		}
	}
	// Palette surface differs from actual backdrop: shade the backdrop, not the card.
	doc, _ := ui.CandidateTokens()
	tokens, _ := doc.Palette("dark", "truecolor")
	p, _ := ui.Resolve(tokens)
	s := drawingScreen(t)
	backdrop := ui.StyleDefault.Background(ui.NewRGBColor(32, 39, 51))
	s.Fill('R', backdrop)
	s.Put(12, 1, "界", backdrop)
	v, _ := ui.NewShadowView(ui.NewBox(), p, ui.ShadowOptions{Mode: ui.ShadowAuto})
	v.SetRect(2, 1, 12, 6)
	v.Draw(s)
	s.Show()
	fg, bg, _ := outputCell(t, s, 13, 1, "▄").Decompose()
	r, g, b := fg.RGB()
	if r != 12 || g != 15 || b != 20 || bg != ui.NewRGBColor(32, 39, 51) {
		t.Fatal("dark contrast must use real backdrop", fg, bg)
	}
}

func TestCompactShadowClippingAndZeroVerticalOffset(t *testing.T) {
	doc, _ := ui.CandidateTokens()
	tokens, _ := doc.Palette("light", "8")
	p, _ := ui.Resolve(tokens)
	s := drawingScreen(t)
	for _, bounds := range []ui.CellRect{{X: -2, Y: -1, Width: 12, Height: 7}, {X: 22, Y: 6, Width: 12, Height: 7}, {Width: 1, Height: 1}, {Width: 1, Height: 7}, {Width: 8, Height: 1}, {}} {
		v, _ := ui.NewShadowView(ui.NewBox(), p, ui.ShadowOptions{Mode: ui.ShadowAuto})
		v.SetRect(bounds.X, bounds.Y, bounds.Width, bounds.Height)
		v.Draw(s)
		s.Show()
	}
	s.Fill('R', p["surface"].Style())
	v, _ := ui.NewShadowView(ui.NewBox(), p, ui.ShadowOptions{Mode: ui.ShadowAuto, OffsetX: 1})
	v.SetRect(2, 1, 12, 6)
	v.Draw(s)
	s.Show()
	outputCell(t, s, 13, 1, " ") // Explicit y=0: no half-row caps.
	outputCell(t, s, 3, 7, "R")
}

func TestShadowCanLeaveTopCapAndKeepCornerContinuous(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, ascii := range []bool{false, true} {
				s := drawingScreen(t)
				doc, _ := ui.CandidateTokens()
				tokens, _ := doc.Palette(theme, profile)
				p, _ := ui.Resolve(tokens)
				dark, bright := ui.PaletteColor(4), ui.PaletteColor(7)
				if profile == "256" {
					dark, bright = ui.PaletteColor(236), ui.PaletteColor(255)
				} else if profile == "truecolor" {
					dark, bright = ui.NewRGBColor(40, 40, 40), ui.NewRGBColor(238, 238, 238)
				}
				darkStyle := ui.StyleDefault.Background(dark).Underline(true)
				s.Fill('R', darkStyle)
				s.Put(11, 7, "B", ui.StyleDefault.Background(bright))
				view, err := ui.NewShadowView(ui.NewBox(), p, ui.ShadowOptions{Mode: ui.ShadowAuto, HideTopCap: true})
				if err != nil {
					t.Fatal(err)
				}
				view.SetRect(2, 1, 10, 7)
				view.ASCII = ascii
				view.Draw(s)
				s.Show()
				if got := outputCell(t, s, 11, 1, "R"); got != darkStyle {
					t.Fatal("hidden cap changed backdrop", theme, profile, got)
				}
				if ascii {
					outputCell(t, s, 11, 2, ".")
					outputCell(t, s, 11, 7, ".")
					continue
				}
				_, side, _ := outputCell(t, s, 11, 6, " ").Decompose()
				ink, backdrop, _ := outputCell(t, s, 11, 7, "▀").Decompose()
				if ink != side || backdrop != bright || ink == backdrop {
					t.Fatal("corner does not join side while preserving backdrop", theme, profile, ink, side, backdrop)
				}
			}
		}
	}
}
