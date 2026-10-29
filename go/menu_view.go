package tuivory

import (
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

// MenuKey maps component-local keys only. Hosts assign F10, Alt and global keys.
func MenuKey(e *tcell.EventKey) (string, string) {
	switch e.Key() {
	case tcell.KeyUp:
		return "previous", ""
	case tcell.KeyDown:
		return "next", ""
	case tcell.KeyLeft:
		return "left", ""
	case tcell.KeyRight:
		return "right", ""
	case tcell.KeyHome:
		return "first", ""
	case tcell.KeyEnd:
		return "last", ""
	case tcell.KeyPgUp:
		return "page_up", ""
	case tcell.KeyPgDn:
		return "page_down", ""
	case tcell.KeyEscape:
		return "cancel", ""
	case tcell.KeyEnter:
		return "activate", ""
	case tcell.KeyRune:
		if e.Modifiers()&(tcell.ModCtrl|tcell.ModAlt) == 0 {
			return "mnemonic", string(e.Rune())
		}
	}
	return "", ""
}

// MenuView uses selection cues without separate focus decoration.
// NewPanelView renders a directly wrapped MenuView with a single border.
type MenuView struct {
	*RowsView
	ASCII bool
}

func NewMenuView(model *Menu, palette Palette, ascii bool, onEvent func(MenuEvent)) (*MenuView, error) {
	height := 1
	v := &MenuView{ASCII: ascii}
	rows, e := NewRowsView(func(w, h int) []ComponentLine { height = h; return model.Layout(w, h, v.ASCII) }, palette)
	v.RowsView = rows
	if rows != nil {
		rows.hideFocus = true
	}
	if e != nil {
		return nil, e
	}
	emit := func(e MenuEvent) {
		if onEvent != nil && e.Kind != "" {
			onEvent(e)
		}
	}
	v.Key = func(e *tcell.EventKey) { action, value := MenuKey(e); emit(model.Handle(action, value, height)) }
	v.Click = func(l ComponentLine) { emit(model.Click(l.ID)) }
	v.Mouse = func(a tview.MouseAction, e *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		x, y := e.Position()
		if !v.InRect(x, y) {
			return false, nil
		}
		switch a {
		case tview.MouseScrollUp:
			emit(model.Handle("previous", "", height))
		case tview.MouseScrollDown:
			emit(model.Handle("next", "", height))
		case tview.MouseLeftDoubleClick:
			return true, nil
		case tview.MouseMove, tview.MouseLeftClick:
			_, top, _, _ := v.GetInnerRect()
			at := y - top
			if at >= 0 && at < len(v.visible) {
				line := v.visible[at]
				if line.Role == "disabled" {
					return true, nil
				}
				if a == tview.MouseMove {
					model.Focus(line.ID)
				} else {
					focus(v)
					emit(model.Click(line.ID))
				}
			}
		default:
			return false, nil
		}
		return true, nil
	}
	return v, nil
}
func NewMenuBarView(model *Menu, palette Palette, onEvent func(MenuEvent)) (*RowsView, error) {
	width := 1
	v, e := NewRowsView(func(w, h int) []ComponentLine {
		width = w
		if h <= 0 {
			return nil
		}
		l := model.BarLayout(w)
		line := ComponentLine{Role: "header"}
		if l.Previous {
			line.Text = "<"
		}
		for _, c := range l.Cells {
			line.Spans = append(line.Spans, ComponentSpan{Start: c.Start, Width: c.Width, Text: c.Text, Role: c.Role, Focused: c.Focused})
		}
		if l.Next && w > 0 {
			line.Spans = append(line.Spans, ComponentSpan{Start: w - 1, Width: 1, Text: ">", Role: "hint"})
		}
		return []ComponentLine{line}
	}, palette)
	if e != nil {
		return nil, e
	}
	v.hideFocus = true
	emit := func(e MenuEvent) {
		if onEvent != nil && e.Kind != "" {
			onEvent(e)
		}
	}
	v.Key = func(e *tcell.EventKey) {
		a, s := MenuKey(e)
		if a == "next" {
			a = "activate"
		}
		if e.Key() == tcell.KeyUp {
			return
		}
		emit(model.HandleBar(a, s))
	}
	v.Pointer = func(_ ComponentLine, x int) { emit(model.BarClick(x, width)) }
	v.Mouse = func(a tview.MouseAction, e *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		x, y := e.Position()
		if !v.InRect(x, y) {
			return false, nil
		}
		if a == tview.MouseLeftDoubleClick {
			return true, nil
		}
		if a != tview.MouseLeftClick {
			return false, nil
		}
		left, _, w, _ := v.GetInnerRect()
		event := model.BarClick(x-left, w)
		if event.Kind != "" {
			focus(v)
			emit(event)
		}
		return true, nil
	}

	return v, nil
}
