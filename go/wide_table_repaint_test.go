package tuivory_test

import (
	"fmt"
	"testing"

	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/uniseg"
)

func TestTableWideTextSurvivesProtectedRestyling(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, wrapper := range []string{"safe", "surface", "shadow-surface"} {
				t.Run(fmt.Sprintf("%s/%s/%s", theme, profile, wrapper), func(t *testing.T) {
					screen := drawingScreen(t)
					screen.SetSize(80, 18)
					doc, _ := ui.CandidateTokens()
					raw, _ := doc.Palette(theme, profile)
					palette, _ := ui.Resolve(raw)
					table := ui.NewTable().SetSelectable(true, true).SetSelectedStyle(palette["selection"].Style().Underline(true))
					texts := []string{"한글 SQL 전체 선택", "界面 é 👩‍💻 🇰🇷 😀"}
					for row, text := range texts {
						table.SetCell(row, 0, ui.NewTableCell(text).SetStyle(palette["field"].Style()).SetTransparency(false))
					}
					var view ui.Primitive = table
					if wrapper != "safe" {
						view, _ = ui.NewSurfaceView(view, palette)
					}
					if wrapper == "shadow-surface" {
						view, _ = ui.NewShadowView(view, palette, ui.ShadowOptions{Mode: ui.ShadowDim})
					}
					view.SetRect(3, 2, 60, 10)
					safe := ui.WideSafeScreen(screen)
					for _, selected := range []int{0, 1, 0} {
						table.Select(selected, 0)
						view.Draw(safe)
						screen.Show()
						for row, text := range texts {
							x, y, _ := table.GetCell(row, 0).GetLastPosition()
							clusters := uniseg.NewGraphemes(text)
							for clusters.Next() {
								st := outputCell(t, screen, x, y, clusters.Str())
								want := palette["field"].Style()
								if row == selected {
									want = palette["selection"].Style().Underline(true)
								}
								fg, bg, attrs := st.Decompose()
								wantFG, wantBG, wantAttrs := want.Decompose()
								if fg != wantFG || bg != wantBG || attrs != wantAttrs {
									t.Fatalf("row %d style: got %v want %v", row, st, want)
								}
								x += clusters.Width()
							}
						}
						screen.Sync()
						x, y, _ := table.GetCell(0, 0).GetLastPosition()
						outputCell(t, screen, x, y, "한")
					}
				})
			}
		}
	}
}

func TestReadModifyWritePreservesWholeWideGlyph(t *testing.T) {
	for _, glyph := range []string{"한", "界", "😀", "👩‍💻", "🇰🇷"} {
		for _, tail := range []bool{false, true} {
			t.Run(fmt.Sprintf("%s/tail=%t", glyph, tail), func(t *testing.T) {
				screen := drawingScreen(t)
				safe := ui.WideSafeScreen(screen)
				base := ui.StyleDefault.Foreground(ui.ColorWhite).Background(ui.ColorBlue)
				safe.Put(2, 1, glyph, base)
				x := 2
				if tail {
					x++
				}
				m, c, st, _ := safe.GetContent(x, 1)
				safe.SetContent(x, 1, m, c, st.Background(ui.ColorGreen).Underline(true))
				screen.Show()
				if got := outputCell(t, screen, 2, 1, glyph); got != st.Background(ui.ColorGreen).Underline(true) {
					t.Fatal("style-only update lost attributes")
				}
				// A real replacement must still clear the old wide glyph.
				safe.GetContent(3, 1)
				safe.SetContent(3, 1, '│', nil, base)
				screen.Show()
				outputCell(t, screen, 2, 1, " ")
				outputCell(t, screen, 3, 1, "│")
			})
		}
	}
}

func TestWideBlankReplacementAndStaleRead(t *testing.T) {
	for _, operation := range []string{"plain-space", "explicit-erase", "show", "sync", "other-write"} {
		t.Run(operation, func(t *testing.T) {
			screen := drawingScreen(t)
			safe := ui.WideSafeScreen(screen)
			style := ui.StyleDefault.Background(ui.ColorBlue)
			safe.Put(2, 1, "한", style)
			if operation != "plain-space" {
				safe.Get(3, 1)
			}
			switch operation {
			case "explicit-erase":
				safe.SetCell(3, 1, style)
			case "show":
				safe.Show()
				safe.Put(3, 1, " ", style)
			case "sync":
				safe.Sync()
				safe.Put(3, 1, " ", style)
			case "other-write":
				safe.Put(8, 1, "X", style)
				safe.Put(3, 1, " ", style)
			default:
				safe.Put(3, 1, " ", style)
			}
			screen.Show()
			outputCell(t, screen, 2, 1, " ")
			outputCell(t, screen, 3, 1, " ")
		})
	}
}
