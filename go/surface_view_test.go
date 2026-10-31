package tuivory_test

import (
	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
	"testing"
)

func TestOpaqueSurfaceAndPanelBorder(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			doc, _ := ui.CandidateTokens()
			raw, _ := doc.Palette(theme, profile)
			p, _ := ui.Resolve(raw)
			child := tview.NewBox()
			v, e := ui.NewSurfaceView(child, p)
			if e != nil {
				t.Fatal(e)
			}
			s := drawingScreen(t)
			s.SetSize(20, 10)
			base := p["hint"].Style()
			s.Fill('R', base)
			s.Put(2, 3, "界", base)
			s.Put(9, 3, "한", base)
			v.SetRect(3, 2, 7, 4)
			v.Draw(s)
			s.Show()
			outputCell(t, s, 3, 2, " ")
			outputCell(t, s, 9, 5, " ")
			outputCell(t, s, 2, 3, " ")
			outputCell(t, s, 10, 3, " ")
			if x, y, w, h := child.GetRect(); x != 3 || y != 2 || w != 7 || h != 4 {
				t.Fatal("surface insets", x, y, w, h)
			}
			v.SetBorder(true)
			v.Draw(s)
			s.Show()
			outputCell(t, s, 3, 2, "┌")
			v.SetBorder(false)
			v.SetRect(3, 2, 0, 0)
			v.Draw(s)
			s.Show()
		}
	}
}
func TestSurfaceForwardsPasteAndMouseCapture(t *testing.T) {
	doc, _ := ui.CandidateTokens()
	raw, _ := doc.Palette("dark", "256")
	p, _ := ui.Resolve(raw)
	input := tview.NewInputField()
	v, _ := ui.NewSurfaceView(input, p)
	v.PasteHandler()("한😀", func(tview.Primitive) {})
	if input.GetText() != "한😀" {
		t.Fatal("paste lost")
	}
	child := tview.NewBox()
	child.SetMouseCapture(func(a tview.MouseAction, e *tcell.EventMouse) (tview.MouseAction, *tcell.EventMouse) { return a, e })
	v, _ = ui.NewSurfaceView(child, p)
	v.SetRect(0, 0, 10, 4)
	v.Draw(drawingScreen(t))
	if !v.InRect(0, 0) {
		t.Fatal("surface geometry")
	}
}
