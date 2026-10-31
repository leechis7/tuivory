package tuivory

import (
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

func TextKey(e *tcell.EventKey) (string, string) { return InputFromKey(e).EditingAction() }

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
