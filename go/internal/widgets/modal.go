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
	form                                       *tview.Form
	text                                       string
	textColor                                  tcell.Color
	buttonStyle, activatedStyle, disabledStyle tcell.Style
	done                                       func(int, string)
}

func NewModal() *Modal {
	m := &Modal{Modal: tview.NewModal(), textColor: tview.Styles.PrimaryTextColor}
	m.Modal.Focus(func(p tview.Primitive) { m.form = p.(*tview.Form) })
	m.buttonStyle = tcell.StyleDefault.Foreground(tview.Styles.PrimaryTextColor).Background(tview.Styles.PrimitiveBackgroundColor)
	m.activatedStyle = tcell.StyleDefault.Foreground(tview.Styles.PrimitiveBackgroundColor).Background(tview.Styles.PrimaryTextColor)
	m.disabledStyle = tcell.StyleDefault.Foreground(tview.Styles.ContrastSecondaryTextColor).Background(tview.Styles.ContrastBackgroundColor)
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
	m.buttonStyle = m.buttonStyle.Background(color)
	m.activatedStyle = m.activatedStyle.Foreground(color)
	return m
}
func (m *Modal) SetButtonTextColor(color tcell.Color) *Modal {
	m.Modal.SetButtonTextColor(color)
	m.buttonStyle = m.buttonStyle.Foreground(color)
	m.activatedStyle = m.activatedStyle.Background(color)
	return m
}
func (m *Modal) SetButtonStyle(style tcell.Style) *Modal {
	m.Modal.SetButtonStyle(style)
	m.buttonStyle = style
	return m
}
func (m *Modal) SetButtonActivatedStyle(style tcell.Style) *Modal {
	m.Modal.SetButtonActivatedStyle(style)
	m.activatedStyle = style
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
	buttonWidths := make([]int, m.form.GetButtonCount())
	for i := range buttonWidths {
		buttonWidths[i] = tview.TaggedStringWidth(m.form.GetButton(i).GetLabel()) + 4
	}
	rows := buttonRowCount(PopupButtonRects(contentWidth, buttonWidths))
	height := min(sh, max(1, len(lines)+6+2*max(0, rows-1)))
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
	positions := PopupButtonRects(w, buttonWidths)
	rows = buttonRowCount(positions)
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
	buttonY := y + h - buttonsHeight
	m.form.SetRect(x, buttonY, w, buttonsHeight)
	_, focused := m.form.GetFocusedItemIndex()
	offset := 0
	if focused >= 0 && focused < len(positions) {
		offset = max(0, 2*positions[focused].Y+1-buttonsHeight)
	}
	for i, position := range positions {
		button := m.form.GetButton(i)
		row := 2*position.Y - offset
		if row < 0 || row >= buttonsHeight {
			button.SetRect(0, 0, 0, 0)
			continue
		}
		button.SetRect(x+position.X, buttonY+row, position.Width, 1)
		button.SetStyle(m.buttonStyle).SetActivatedStyle(m.activatedStyle).SetDisabledStyle(m.disabledStyle)
		button.Draw(screen)
	}
}

func buttonRowCount(positions []PopupButtonRect) int {
	if len(positions) == 0 {
		return 0
	}
	return positions[len(positions)-1].Y + 1
}

type PopupButtonRect struct{ X, Y, Width int }

func PopupButtonRects(width int, widths []int) []PopupButtonRect {
	if width <= 0 {
		return nil
	}
	positions := make([]PopupButtonRect, 0, len(widths))
	rowStart, used, row := 0, 0, 0
	center := func() {
		for i := rowStart; i < len(positions); i++ {
			positions[i].X += (width - used) / 2
		}
	}
	for _, requested := range widths {
		w := min(width, max(1, requested))
		if used > 0 && w >= width-used {
			center()
			rowStart, used, row = len(positions), 0, row+1
		}
		if used > 0 {
			used++
		}
		positions = append(positions, PopupButtonRect{used, row, w})
		used += w
	}
	center()
	return positions
}
