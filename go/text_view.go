package tuivory

import (
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

func TextKey(e *tcell.EventKey) (string, string) {
	action, text := "", ""
	switch e.Key() {
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
	case tcell.KeyEnter:
		action = "newline"
	case tcell.KeyBackspace, tcell.KeyBackspace2:
		action = "backspace"
	case tcell.KeyDelete:
		action = "delete"
	case tcell.KeyCtrlA:
		action = "select_all"
	case tcell.KeyCtrlC:
		action = "copy"
	case tcell.KeyCtrlX:
		action = "cut"
	case tcell.KeyCtrlZ:
		action = "undo"
	case tcell.KeyCtrlY:
		action = "redo"
	case tcell.KeyPgUp:
		action = "page_up"
	case tcell.KeyPgDn:
		action = "page_down"
	case tcell.KeyRune:
		action = "insert"
		text = string(e.Rune())
	}
	if e.Modifiers()&tcell.ModShift != 0 && (action == "left" || action == "right" || action == "up" || action == "down" || action == "home" || action == "end") {
		action = "select_" + action
	}
	if e.Modifiers()&tcell.ModAlt != 0 {
		if action == "left" {
			action = "scroll_left"
		}
		if action == "right" {
			action = "scroll_right"
		}
	}
	return action, text
}

// NewEditorView and NewTextViewView share the same literal renderer. Read-only
// is a buffer state, not a second editor implementation. Clipboard events are
// delivered to the host and never executed by the library.
func NewEditorView(doc *TextDocument, palette Palette, onEvent func(TextEvent)) (*RowsView, error) {
	v, e := NewRowsView(doc.Layout, palette)
	if e != nil {
		return nil, e
	}
	emit := func(a, t string) {
		event := doc.Handle(a, t)
		if onEvent != nil && event.Kind != "" {
			onEvent(event)
		}
	}
	v.Key = func(key *tcell.EventKey) { a, t := TextKey(key); emit(a, t) }
	v.Paste = func(text string) { emit("paste", text) }
	// Viewport selection is mapped to original grapheme positions below.
	dragging := false
	v.Mouse = func(a tview.MouseAction, event *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		x, y := event.Position()
		inside := v.InRect(x, y)
		if !inside && !dragging {
			return false, nil
		}
		if doc.Buffer.State.Disabled {
			dragging = false
			return true, nil
		}
		if a == tview.MouseScrollUp {
			emit("scroll_up", "")
			return true, nil
		}
		if a == tview.MouseScrollDown {
			emit("scroll_down", "")
			return true, nil
		}
		if a == tview.MouseLeftDown || a == tview.MouseMove && dragging || a == tview.MouseLeftUp && dragging {
			if a == tview.MouseLeftDown {
				focus(v)
				dragging = true
			}
			left, top, w, h := v.GetInnerRect()
			doc.Point(x-left, y-top, w, h, a != tview.MouseLeftDown)
			if a == tview.MouseLeftUp {
				dragging = false
				return true, nil
			}
			return true, v
		}
		return true, nil
	}
	return v, nil
}
func NewTextViewView(doc *TextDocument, palette Palette, onEvent func(TextEvent)) (*RowsView, error) {
	return NewEditorView(doc, palette, onEvent)
}
