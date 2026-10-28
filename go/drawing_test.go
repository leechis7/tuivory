package tuivory_test

import (
	"fmt"
	"math"
	"strings"
	"testing"

	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
)

func drawingScreen(t *testing.T) tcell.SimulationScreen {
	t.Helper()
	s := tcell.NewSimulationScreen("UTF-8")
	if err := s.Init(); err != nil {
		t.Fatal(err)
	}
	s.SetSize(24, 8)
	s.Fill(' ', tcell.StyleDefault)
	s.Show()
	t.Cleanup(s.Fini)
	return s
}
func outputCell(t *testing.T, s tcell.SimulationScreen, x, y int, want string) tcell.Style {
	t.Helper()
	cells, w, _ := s.GetContents()
	c := cells[y*w+x]
	if string(c.Runes) != want || string(c.Bytes) != want {
		t.Fatalf("output (%d,%d): runes=%q bytes=%q want %q", x, y, string(c.Runes), string(c.Bytes), want)
	}
	return c.Style
}

func TestWideSafeScreenOutputAfterShow(t *testing.T) {
	writers := map[string]func(tcell.Screen, int, int, string, tcell.Style){
		"SetContent": func(s tcell.Screen, x, y int, text string, st tcell.Style) {
			r := []rune(text)
			s.SetContent(x, y, r[0], r[1:], st)
		},
		"SetCell":      func(s tcell.Screen, x, y int, text string, st tcell.Style) { s.SetCell(x, y, st, []rune(text)...) },
		"Put":          func(s tcell.Screen, x, y int, text string, st tcell.Style) { s.Put(x, y, text, st) },
		"PutStrStyled": func(s tcell.Screen, x, y int, text string, st tcell.Style) { s.PutStrStyled(x, y, text, st) },
		"PutStr":       func(s tcell.Screen, x, y int, text string, _ tcell.Style) { s.PutStr(x, y, text) },
	}
	for name, write := range writers {
		for _, glyph := range []string{"한", "界", "🙂", "👩‍💻", "🇰🇷"} {
			t.Run(name+"/"+glyph, func(t *testing.T) {
				s := drawingScreen(t)
				safe := ui.WideSafeScreen(s)
				if ui.WideSafeScreen(safe) != safe {
					t.Fatal("wrapping must be idempotent")
				}
				base := tcell.StyleDefault.Foreground(tcell.ColorWhite).Background(tcell.ColorBlue)
				card := tcell.StyleDefault.Foreground(tcell.ColorYellow).Background(tcell.ColorBlack)
				// Old raw content must be repaired too; callers need not repaint it safely.
				for _, x := range []int{2, 8} {
					s.Put(x+1, 2, "Z", base)
					s.Put(x, 2, glyph, base)
				}
				s.Put(12, 2, "K", base)
				s.Show()
				write(safe, 3, 2, "│", card) // overwrite the left glyph's tail
				write(safe, 8, 2, "│", card) // overwrite the right glyph's start
				s.Show()
				outputCell(t, s, 2, 2, " ")
				outputCell(t, s, 3, 2, "│")
				outputCell(t, s, 8, 2, "│")
				outputCell(t, s, 9, 2, " ")
				outputCell(t, s, 12, 2, "K")
				// Close (host redraw), reopen in the opposite order, and force Sync.
				s.Put(2, 2, glyph, base)
				s.Put(8, 2, glyph, base)
				s.Show()
				write(safe, 8, 2, "│", card)
				write(safe, 3, 2, "│", card)
				s.Show()
				s.Sync()
				outputCell(t, s, 3, 2, "│")
				outputCell(t, s, 9, 2, " ")
			})
		}
	}
}
func TestWideSafeReplacementClippingAndGraphemes(t *testing.T) {
	s := drawingScreen(t)
	safe := ui.WideSafeScreen(s)
	st := tcell.StyleDefault
	s.Put(3, 0, "界", st)
	s.Put(5, 0, "한", st)
	s.Show()
	rest, width := safe.Put(4, 0, "👩‍💻tail", st)
	if rest != "tail" || width != 2 {
		t.Fatalf("grapheme contract: %q %d", rest, width)
	}
	s.Show()
	outputCell(t, s, 3, 0, " ")
	outputCell(t, s, 4, 0, "👩‍💻")
	outputCell(t, s, 6, 0, " ")
	safe.Put(4, 0, "x", st)
	s.Show()
	outputCell(t, s, 5, 0, " ")
	safe.PutStrStyled(20, 1, "e\u0301界X", st)
	s.Show()
	outputCell(t, s, 20, 1, "e\u0301")
	outputCell(t, s, 21, 1, "界")
	outputCell(t, s, 23, 1, "X")
	safe.Put(23, 0, "한", st)
	s.Show()
	outputCell(t, s, 23, 0, " ")
	for _, p := range [][2]int{{-1, 0}, {0, -1}, {24, 0}, {0, 8}, {math.MaxInt, 0}} {
		rest, width = safe.Put(p[0], p[1], "same", st)
		if rest != "same" || width != 0 {
			t.Fatal("out of bounds")
		}
	}
	safe.SetCell(0, 0, st)
	s.Show()
	outputCell(t, s, 0, 0, " ")
}
func TestDimRegionBothBoundariesAndOutputStyles(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, glyph := range []string{"한", "界", "🙂", "👩‍💻"} {
				t.Run(fmt.Sprintf("%s/%s/%s", theme, profile, glyph), func(t *testing.T) {
					s := drawingScreen(t)
					styler, err := ui.New(theme, profile)
					if err != nil {
						t.Fatal(err)
					}
					st := styler.Styles.PopupShadowStyle().Dim(false)
					s.Put(1, 2, glyph, st)
					s.Put(4, 2, glyph, st)
					s.Put(7, 2, glyph, st)
					s.Put(10, 2, "K", st)
					s.Show()
					ui.DimRegion(s, ui.CellRect{X: 2, Y: 2, Width: 6, Height: 1})
					s.Show()
					outside := outputCell(t, s, 1, 2, " ")
					outputCell(t, s, 2, 2, " ")
					inside := outputCell(t, s, 4, 2, glyph)
					outputCell(t, s, 7, 2, " ")
					right := outputCell(t, s, 8, 2, " ")
					outputCell(t, s, 10, 2, "K")
					if outside != st || right != st || inside != st.Dim(true) {
						t.Fatal("shadow changed outside style or failed to dim interior")
					}
					s.Sync()
					outputCell(t, s, 7, 2, " ")
				})
			}
		}
	}
}
func TestDimRegionClipsAndPreservesUnrelatedCells(t *testing.T) {
	s := drawingScreen(t)
	s.Fill('.', tcell.StyleDefault)
	s.Show()
	for _, r := range []ui.CellRect{{X: math.MinInt, Y: 0, Width: math.MaxInt, Height: 2}, {Width: 0, Height: 4}, {X: 24, Width: 2, Height: 2}, {X: 0, Y: 8, Width: 2, Height: 2}} {
		ui.DimRegion(s, r)
	}
	s.Show()
	outputCell(t, s, 0, 0, ".")
	ui.DimRegion(s, ui.CellRect{X: -2, Y: -1, Width: 4, Height: 3})
	s.Show()
	if outputCell(t, s, 0, 0, ".") == tcell.StyleDefault {
		t.Fatal("clipped shadow not dimmed")
	}
	if outputCell(t, s, 2, 0, ".") != tcell.StyleDefault {
		t.Fatal("shadow escaped clipped rectangle")
	}
}
func TestPanelBorderOverWideBackgroundAfterShow(t *testing.T) {
	for _, ascii := range []bool{false, true} {
		t.Run(fmt.Sprint(ascii), func(t *testing.T) {
			s := drawingScreen(t)
			doc, _ := ui.CandidateTokens()
			raw, _ := doc.Palette("dark", "256")
			p, _ := ui.Resolve(raw)
			panel, err := ui.NewPanelView(tview.NewBox(), p)
			if err != nil {
				t.Fatal(err)
			}
			panel.ASCII = ascii
			panel.SetRect(3, 2, 8, 4)
			for row := 0; row < 8; row++ {
				s.PutStrStyled(0, row, strings.Repeat("한", 12), tcell.StyleDefault)
			}
			s.Show()
			panel.Draw(s)
			s.Show()
			border := "│"
			if ascii {
				border = "|"
			}
			outputCell(t, s, 3, 3, border)
			outputCell(t, s, 10, 3, border)
			outputCell(t, s, 2, 3, " ")
		})
	}
}
