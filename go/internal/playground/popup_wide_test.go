package playground

import (
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
	"strings"
	"testing"
)

func TestPopupCardBordersSurviveWideBackgroundAfterShow(t *testing.T) {
	for _, glyph := range []string{"한", "界", "🙂", "👩‍💻"} {
		for _, offset := range []int{0, 1} {
			t.Run(glyph+strings.Repeat("-", offset), func(t *testing.T) {
				ui, screen := testUI(t)
				screen.SetSize(119, 36)
				ui.layers.SetRect(0, 0, 119, 36)
				ui.openPopup("Popup", "body", 0)
				_, layer := ui.layers.GetFrontPage()
				for frame := 0; frame < 2; frame++ {
					screen.Clear()
					for row := 0; row < 36; row++ {
						screen.PutStrStyled(offset, row, strings.Repeat(glyph, 59), tcell.StyleDefault)
					}
					screen.Show()
					layer.Draw(screen)
					screen.Show()
					x, y, w, h := ui.popup.card.GetRect()
					cells, cols, _ := screen.GetContents()
					for _, edge := range []int{x, x + w - 1} {
						for row := y + 1; row < y+h-1; row++ {
							c := cells[row*cols+edge]
							if string(c.Runes) != string(tview.Borders.VerticalFocus) || string(c.Bytes) != string(tview.Borders.VerticalFocus) {
								t.Fatalf("frame %d border (%d,%d) output=%q/%q", frame, edge, row, c.Runes, c.Bytes)
							}
						}
					}
				}
			})
		}
	}
}
