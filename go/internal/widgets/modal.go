package widgets

import (
	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go/internal/drawing"
	"github.com/rivo/tview"
)

// Modal retains the backend's focus, input, mouse and callback machinery while
// fitting its message and wrapping buttons to the current terminal size.
// The embedded Modal is available for explicit backend interoperability.
type Modal struct {
	*tview.Modal
	form      *tview.Form
	text      string
	textColor tcell.Color
	done      func(int, string)
}

func NewModal() *Modal {
	m := &Modal{Modal: tview.NewModal(), textColor: tview.Styles.PrimaryTextColor}
	m.Modal.Focus(func(p tview.Primitive) { m.form = p.(*tview.Form) })
	m.form.SetHorizontal(true)
	return m
}

func (m *Modal) SetText(text string) *Modal { m.text = text; m.Modal.SetText(text); return m }
func (m *Modal) SetTextColor(color tcell.Color) *Modal {
	m.textColor = color
	m.Modal.SetTextColor(color)
	return m
}
func (m *Modal) SetBackgroundColor(color tcell.Color) *Modal {
	m.Modal.SetBackgroundColor(color)
	m.Box.SetBackgroundColor(color)
	return m
}
func (m *Modal) SetButtonBackgroundColor(color tcell.Color) *Modal {
	m.Modal.SetButtonBackgroundColor(color)
	return m
}
func (m *Modal) SetButtonTextColor(color tcell.Color) *Modal {
	m.Modal.SetButtonTextColor(color)
	return m
}
func (m *Modal) SetButtonStyle(style tcell.Style) *Modal { m.Modal.SetButtonStyle(style); return m }
func (m *Modal) SetButtonActivatedStyle(style tcell.Style) *Modal {
	m.Modal.SetButtonActivatedStyle(style)
	return m
}
func (m *Modal) SetDoneFunc(done func(int, string)) *Modal {
	m.done = done
	m.Modal.SetDoneFunc(done)
	return m
}
func (m *Modal) SetFocus(index int) *Modal { m.Modal.SetFocus(index); return m }
func (m *Modal) ClearButtons() *Modal      { m.Modal.ClearButtons(); return m }
func (m *Modal) AddButtons(labels []string) *Modal {
	for _, label := range labels {
		index := m.form.GetButtonCount()
		m.form.AddButton(label, func() {
			if m.done != nil {
				m.done(index, label)
			}
		})
		m.form.GetButton(index).SetInputCapture(func(e *tcell.EventKey) *tcell.EventKey {
			switch e.Key() {
			case tcell.KeyRight, tcell.KeyDown:
				return tcell.NewEventKey(tcell.KeyTab, 0, tcell.ModNone)
			case tcell.KeyLeft, tcell.KeyUp:
				return tcell.NewEventKey(tcell.KeyBacktab, 0, tcell.ModNone)
			}
			return e
		})
	}
	return m
}

// Draw prioritizes reachable buttons over message text at small heights. Form
// scrolling keeps the focused button visible when even wrapped rows cannot fit.
func (m *Modal) Draw(screen tcell.Screen) {
	screen = drawing.SafeScreen(screen)
	sw, sh := screen.Size()
	if sw <= 0 || sh <= 0 {
		m.SetRect(0, 0, 0, 0)
		return
	}
	total := 0
	for i := 0; i < m.form.GetButtonCount(); i++ {
		total += tview.TaggedStringWidth(m.form.GetButton(i).GetLabel()) + 5
	}
	width := min(sw, max(1, max(sw/3, total+3)))
	contentWidth := max(1, width-4)
	lines := tview.WordWrap(m.text, contentWidth)
	rows, used := 1, 0
	for i := 0; i < m.form.GetButtonCount(); i++ {
		w := min(contentWidth, tview.TaggedStringWidth(m.form.GetButton(i).GetLabel())+4)
		if used > 0 && used+w > contentWidth {
			rows++
			used = 0
		}
		used += w + 1
	}
	height := min(sh, max(1, len(lines)+6+2*(rows-1)))
	m.SetRect((sw-width)/2, (sh-height)/2, width, height)
	m.Box.DrawForSubclass(screen, m)
	x, y, w, h := m.GetInnerRect()
	if w <= 0 || h <= 0 {
		// A one-cell terminal cannot show borders and content simultaneously.
		x, y, w, h = m.GetRect()
	}
	if w > 2 {
		x++
		w -= 2
	}
	if h > 2 {
		y++
		h -= 2
	}
	if w <= 0 || h <= 0 {
		return
	}
	lines = tview.WordWrap(m.text, w)
	buttonsHeight := 0
	if m.form.GetButtonCount() > 0 {
		buttonsHeight = min(h, 2*rows-1)
	}
	messageHeight := max(0, h-buttonsHeight)
	if messageHeight > 0 && buttonsHeight > 0 {
		messageHeight--
	}
	for i, line := range lines {
		if i >= messageHeight {
			break
		}
		tview.Print(screen, line, x, y+i, w, tview.AlignCenter, m.textColor)
	}
	if buttonsHeight > 0 {
		m.form.SetRect(x, y+h-buttonsHeight, w, buttonsHeight)
		m.form.Draw(screen)
	}
}
