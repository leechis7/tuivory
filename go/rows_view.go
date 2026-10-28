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
	Pointer func(ComponentLine, int)
	palette Palette
	visible []ComponentLine
}

func NewRowsView(rows func(int, int) []ComponentLine, palette Palette) (*RowsView, error) {
	p, e := componentPalette(palette, "surface", "body", "hint", "field", "button", "error", "selection", "disabled", "edited", "header", "info", "success", "warning")
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
		for _, span := range line.Spans {
			start := max(0, min(w, span.Start))
			width := min(max(0, span.Width), w-start)
			pair, ok := v.palette[span.Role]
			if !ok {
				panic("component: missing span role " + span.Role)
			}
			style := pair.Style().Underline(span.Focused && v.HasFocus())
			fillComponent(screen, x+start, y+i, width, 1, style)
			drawTreeText(screen, x+start, y+i, width, 0, span.Text, style)
		}
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
		if row >= 0 && row < len(v.visible) && (v.Click != nil || v.Pointer != nil) {
			focus(v)
			if v.Pointer != nil {
				left, _, _, _ := v.GetInnerRect()
				v.Pointer(v.visible[row], x-left)
			} else {
				v.Click(v.visible[row])
			}
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

func NavigationKey(e *tcell.EventKey) string {
	switch e.Key() {
	case tcell.KeyUp:
		return "previous"
	case tcell.KeyDown:
		return "next"
	case tcell.KeyHome:
		return "first"
	case tcell.KeyEnd:
		return "last"
	case tcell.KeyPgUp:
		return "page_up"
	case tcell.KeyPgDn:
		return "page_down"
	case tcell.KeyEnter:
		return "activate"
	case tcell.KeyEscape:
		return "cancel"
	case tcell.KeyRune:
		if e.Rune() == ' ' {
			return "select"
		}
	}
	return ""
}
func NewListView(model *ListModel, palette Palette, ascii bool, onEvent func(ListEvent)) (*RowsView, error) {
	height := 1
	v, e := NewRowsView(func(w, h int) []ComponentLine { height = h; return model.Layout(w, h, ascii) }, palette)
	if e != nil {
		return nil, e
	}
	emit := func(event ListEvent) {
		if onEvent != nil && event.Kind != "" {
			onEvent(event)
		}
	}
	v.Key = func(key *tcell.EventKey) { emit(model.Handle(NavigationKey(key), height)) }
	v.Click = func(line ComponentLine) {
		if model.Focus(line.ID) {
			emit(model.Handle("activate", height))
		}
	}
	return v, nil
}
func NewSearchPickerView(model *SearchPicker, palette Palette, ascii bool, onEvent func(ListEvent)) (*RowsView, error) {
	height := 1
	v, e := NewRowsView(func(w, h int) []ComponentLine { height = h; return model.Layout(w, h, ascii) }, palette)
	if e != nil {
		return nil, e
	}
	emit := func(event ListEvent) {
		if onEvent != nil && event.Kind != "" {
			onEvent(event)
		}
	}
	v.Key = func(key *tcell.EventKey) {
		action := NavigationKey(key)
		value := ""
		if key.Key() == tcell.KeyRune {
			action = "insert"
			value = string(key.Rune())
		}
		if key.Key() == tcell.KeyBackspace || key.Key() == tcell.KeyBackspace2 {
			action = "backspace"
		}
		emit(model.Handle(action, value, height))
	}
	v.Click = func(line ComponentLine) {
		if !model.Open {
			emit(model.Handle("open", "", height))
		} else {
			emit(model.Click(line.ID))
		}
	}
	return v, nil
}

func GridKey(e *tcell.EventKey) string {
	switch e.Key() {
	case tcell.KeyLeft:
		return "left"
	case tcell.KeyRight:
		return "right"
	case tcell.KeyUp:
		return "up"
	case tcell.KeyDown:
		return "down"
	case tcell.KeyCtrlC:
		return "copy"
	case tcell.KeyF6:
		return "row_mode"
	case tcell.KeyF7:
		return "widen"
	case tcell.KeyF8:
		return "narrow"
	case tcell.KeyF9:
		return "sort"
	case tcell.KeyRune:
		if e.Rune() == ' ' {
			return "select"
		}
	}
	return NavigationKey(e)
}
func NewGridView(model *Grid, palette Palette, onEvent func(GridEvent)) (*RowsView, error) {
	width, height := 1, 1
	v, e := NewRowsView(func(w, h int) []ComponentLine { width, height = w, h; return model.Layout(w, h) }, palette)
	if e != nil {
		return nil, e
	}
	emit := func(e GridEvent) {
		if onEvent != nil && e.Kind != "" {
			onEvent(e)
		}
	}
	v.Key = func(e *tcell.EventKey) {
		if e.Key() == tcell.KeyF5 {
			emit(model.RequestFilter("sample"))
		} else {
			emit(model.Handle(GridKey(e), height))
		}
	}
	v.Pointer = func(line ComponentLine, x int) { emit(model.Click(line.ID, line.Value, x, width, height)) }
	return v, nil
}

func NewNoticeView(queue *NoticeQueue, palette Palette, now func() uint64, onEvent func(NoticeEvent)) (*RowsView, error) {
	height := 1
	clock := func() uint64 {
		if now != nil {
			return now()
		}
		return 0
	}
	v, e := NewRowsView(func(w, h int) []ComponentLine { height = h; return queue.Layout(w, h, clock()) }, palette)
	if e != nil {
		return nil, e
	}
	v.Key = func(key *tcell.EventKey) {
		action := NavigationKey(key)
		if key.Key() == tcell.KeyDelete || key.Key() == tcell.KeyEscape {
			action = "dismiss"
		}
		event := queue.Handle(action, clock(), height)
		if onEvent != nil && event.Kind != "" {
			onEvent(event)
		}
	}
	v.Click = func(line ComponentLine) {
		if line.ID != "" {
			queue.Focused = line.ID
		}
	}
	return v, nil
}
func NewProgressView(progress *Progress, palette Palette, frame func() uint64, onEvent func(NoticeEvent)) (*RowsView, error) {
	v, e := NewRowsView(func(w, h int) []ComponentLine {
		tick := uint64(0)
		if frame != nil {
			tick = frame()
		}
		return progress.Layout(w, tick)
	}, palette)
	if e != nil {
		return nil, e
	}
	v.Key = func(key *tcell.EventKey) {
		if key.Key() == tcell.KeyEscape || key.Key() == tcell.KeyRune && key.Rune() == 'c' {
			event := progress.RequestCancel()
			if onEvent != nil && event.Kind != "" {
				onEvent(event)
			}
		}
	}
	return v, nil
}
func NewDataStateView(state *DataState, palette Palette) (*RowsView, error) {
	return NewRowsView(func(w, h int) []ComponentLine { return state.Layout(w) }, palette)
}
