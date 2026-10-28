package tuivory

import (
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

// RowsView renders literal, cell-clipped semantic lines and delegates actions.
type RowsView struct {
	*tview.Box
	Rows    func(int, int) []ComponentLine
	Key     func(*tcell.EventKey)
	Click   func(ComponentLine)
	palette Palette
	visible []ComponentLine
}

func NewRowsView(rows func(int, int) []ComponentLine, palette Palette) (*RowsView, error) {
	p, e := componentPalette(palette, "surface", "body", "hint", "field", "button", "error", "selection", "disabled", "edited")
	if e != nil {
		return nil, e
	}
	return &RowsView{Box: tview.NewBox(), Rows: rows, palette: p}, nil
}
func (v *RowsView) Draw(screen tcell.Screen) {
	x, y, w, h := v.GetInnerRect()
	fillComponent(screen, x, y, w, h, v.palette["surface"].Style())
	v.visible = v.Rows(w, h)
	for i, line := range v.visible {
		if i >= h {
			break
		}
		pair, ok := v.palette[line.Role]
		if !ok {
			panic("component: missing row role " + line.Role)
		}
		drawTreeText(screen, x, y+i, w, 0, line.Text, pair.Style().Underline(line.Focused && v.HasFocus()))
	}
}
func (v *RowsView) InputHandler() func(*tcell.EventKey, func(tview.Primitive)) {
	return v.WrapInputHandler(func(e *tcell.EventKey, _ func(tview.Primitive)) {
		if v.Key != nil {
			v.Key(e)
		}
	})
}
func (v *RowsView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return v.WrapMouseHandler(func(a tview.MouseAction, e *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		x, y := e.Position()
		if a != tview.MouseLeftClick || !v.InRect(x, y) {
			return false, nil
		}
		_, top, _, _ := v.GetInnerRect()
		row := y - top
		if row >= 0 && row < len(v.visible) && v.Click != nil {
			focus(v)
			v.Click(v.visible[row])
		}
		return true, v
	})
}
func FormKey(form *Form, e *tcell.EventKey) FormEvent {
	action := ""
	text := ""
	switch e.Key() {
	case tcell.KeyTab:
		action = "next"
	case tcell.KeyBacktab:
		action = "previous"
	case tcell.KeyEnter:
		action = "activate"
	case tcell.KeyEscape:
		action = "cancel"
	case tcell.KeyLeft:
		action = "left"
	case tcell.KeyRight:
		action = "right"
	case tcell.KeyUp:
		action = "up"
	case tcell.KeyDown:
		action = "down"
	case tcell.KeyHome:
		action = "home"
	case tcell.KeyEnd:
		action = "end"
	case tcell.KeyBackspace, tcell.KeyBackspace2:
		action = "backspace"
	case tcell.KeyDelete:
		action = "delete"
	case tcell.KeyRune:
		action = "insert"
		text = string(e.Rune())
		if e.Rune() == ' ' {
			for _, field := range form.Fields() {
				if field.ID == form.Focused() && field.Kind != "text" && field.Kind != "textarea" {
					action = "toggle"
				}
			}
		}
	}
	return form.Handle(action, text)
}
func NewFormView(form *Form, palette Palette, onEvent func(FormEvent)) (*RowsView, error) {
	v, e := NewRowsView(form.Layout, palette)
	if e != nil {
		return nil, e
	}
	v.Key = func(key *tcell.EventKey) {
		event := FormKey(form, key)
		if onEvent != nil && event.Kind != "" {
			onEvent(event)
		}
	}
	v.Click = func(line ComponentLine) {
		event := form.Click(line.ID, line.Value)
		if onEvent != nil && event.Kind != "" {
			onEvent(event)
		}
	}
	return v, nil
}
