package tuivory

import (
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
	"github.com/rivo/uniseg"
	"strings"
)

// RowsView renders literal, cell-clipped semantic lines and delegates actions.
type RowsView struct {
	*tview.Box
	Rows        func(int, int) []ComponentLine
	Key         func(*tcell.EventKey)
	Paste       func(string)
	TabBoundary func(bool) bool
	Click       func(ComponentLine)
	Pointer     func(ComponentLine, int)
	palette     Palette
	visible     []ComponentLine
	hideFocus   bool
	// PreserveBackgrounds keeps explicit row/span backgrounds for grid or custom composition.
	PreserveBackgrounds bool
	Mouse               func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive)
}

func (v *RowsView) AtTabBoundary(previous bool) bool {
	return v.TabBoundary == nil || v.TabBoundary(previous)
}

func NewRowsView(rows func(int, int) []ComponentLine, palette Palette) (*RowsView, error) {
	p, e := componentPalette(GridPalette(palette), "surface", "body", "hint", "field", "button", "error", "selection", "disabled", "edited", "header", "info", "success", "warning")
	if e != nil {
		return nil, e
	}
	return &RowsView{Box: tview.NewBox(), Rows: rows, palette: p}, nil
}
func (v *RowsView) Draw(screen tcell.Screen) {
	screen = WideSafeScreen(screen)
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
		if strings.HasPrefix(line.Role, "grid.") {
			fillComponent(screen, x, y+i, w, 1, pair.Style())
		}
		style := disabledCue(v.palette, line.Role, pair.Style())
		if !v.PreserveBackgrounds {
			style = componentStyle(v.palette, line.Role)
		}
		drawTreeText(screen, x, y+i, w, 0, line.Text, style.Underline(line.Focused && !v.hideFocus && v.HasFocus()))
		for _, span := range line.Spans {
			start := max(0, min(w, span.Start))
			width := min(max(0, span.Width), w-start)
			pair, ok := v.palette[span.Role]
			if !ok {
				panic("component: missing span role " + span.Role)
			}
			style := disabledCue(v.palette, span.Role, pair.Style())
			if !v.PreserveBackgrounds {
				style = componentStyle(v.palette, span.Role)
			}
			style = style.Underline(span.Focused && !v.hideFocus && v.HasFocus())
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
func (v *RowsView) PasteHandler() func(string, func(tview.Primitive)) {
	return v.WrapPasteHandler(func(text string, _ func(tview.Primitive)) {
		if v.Paste != nil {
			v.Paste(text)
		}
	})
}
func (v *RowsView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return v.WrapMouseHandler(func(a tview.MouseAction, e *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		if v.Mouse != nil {
			return v.Mouse(a, e, focus)
		}
		x, y := e.Position()
		if a != tview.MouseLeftClick || !v.InRect(x, y) {
			return false, nil
		}
		_, top, _, _ := v.GetInnerRect()
		row := y - top
		if row >= 0 && row < len(v.visible) && (v.Click != nil || v.Pointer != nil) {
			line := v.visible[row]
			if line.Role == "disabled" {
				return true, v
			}
			left, _, _, _ := v.GetInnerRect()
			for _, span := range line.Spans {
				if span.Role == "disabled" && x-left >= span.Start && x-left < span.Start+span.Width {
					return true, v
				}
			}
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
				if field.ID == form.Focused() && field.Kind != "text" && field.Kind != "textarea" && field.Kind != "password" {
					action = "toggle"
				}
			}
		}
	}
	if e.Modifiers()&tcell.ModShift != 0 && (action == "left" || action == "right" || action == "home" || action == "end" || action == "up" || action == "down") {
		action = "select_" + action
	}
	return form.Handle(action, text)
}
func NewFormView(form *Form, palette Palette, onEvent func(FormEvent)) (*RowsView, error) {
	v, e := NewRowsView(form.Layout, palette)
	if e != nil {
		return nil, e
	}
	v.TabBoundary = form.AtTabBoundary
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
	v.Paste = func(text string) {
		e := form.Handle("paste", text)
		if onEvent != nil && e.Kind != "" {
			onEvent(e)
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
	if e.Modifiers()&tcell.ModAlt != 0 {
		if e.Key() == tcell.KeyLeft {
			return "cell_pan_left"
		}
		if e.Key() == tcell.KeyRight {
			return "cell_pan_right"
		}
	}
	if e.Modifiers()&tcell.ModShift != 0 {
		switch e.Key() {
		case tcell.KeyLeft:
			return "extend_left"
		case tcell.KeyRight:
			return "extend_right"
		case tcell.KeyUp:
			return "extend_up"
		case tcell.KeyDown:
			return "extend_down"
		}
	}
	switch e.Key() {
	case tcell.KeyF10:
		return "range_mode"
	case tcell.KeyF11:
		return "autofit"
	case tcell.KeyF12:
		return "details"
	}
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
	if v != nil {
		v.PreserveBackgrounds = true
	}
	if e != nil {
		return nil, e
	}
	emit := func(e GridEvent) {
		if onEvent != nil && e.Kind != "" {
			onEvent(e)
		}
	}
	v.Key = func(e *tcell.EventKey) {
		if model.options.DisableKeyboard {
			return
		}
		if e.Key() == tcell.KeyF5 {
			emit(model.RequestFilter(model.Status.Filter))
		} else {
			emit(model.Handle(GridKey(e), height))
		}
	}
	v.Pointer = func(line ComponentLine, x int) { emit(model.Click(line.ID, line.Value, x, width, height)) }
	v.Mouse = func(a tview.MouseAction, e *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		if model.options.DisableMouse {
			return false, nil
		}
		x, y := e.Position()
		left, top, w, h := v.GetInnerRect()
		action := ""
		switch a {
		case tview.MouseLeftDown:
			action = "down"
		case tview.MouseLeftUp:
			action = "up"
		case tview.MouseMove:
			action = "move"
		case tview.MouseLeftClick:
			action = "click"
		case tview.MouseLeftDoubleClick:
			action = "double"
		case tview.MouseScrollUp:
			action = "wheel_up"
		case tview.MouseScrollDown:
			action = "wheel_down"
		case tview.MouseScrollLeft:
			action = "wheel_left"
		case tview.MouseScrollRight:
			action = "wheel_right"
		}
		if action == "" || (action == "move" && model.dragColumn == "" && model.dragAnchor.AnchorRow == "") {
			return false, nil
		}
		if !v.InRect(x, y) && model.dragColumn == "" && model.dragAnchor.AnchorRow == "" {
			return false, nil
		}
		if action != "up" {
			focus(v)
		}
		emit(model.Pointer(action, x-left, y-top, w, h, e.Modifiers()&tcell.ModShift != 0))
		if model.dragColumn != "" || model.dragAnchor.AnchorRow != "" {
			return true, v
		}
		return true, nil
	}

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

func NewBadgeView(badge *Badge, palette Palette) (*RowsView, error) {
	return NewRowsView(func(w, h int) []ComponentLine { return []ComponentLine{badge.Line(w)} }, palette)
}
func NewChipView(chip *Chip, palette Palette, onEvent func(ComponentEvent)) (*RowsView, error) {
	v, e := NewRowsView(func(w, h int) []ComponentLine { return []ComponentLine{chip.Line(w)} }, palette)
	if e != nil {
		return nil, e
	}
	emit := func() {
		event := chip.RequestRemove()
		if onEvent != nil && event.Kind != "" {
			onEvent(event)
		}
	}
	v.Key = func(e *tcell.EventKey) {
		if e.Key() == tcell.KeyDelete || e.Key() == tcell.KeyRune && e.Rune() == 'x' {
			emit()
		}
	}
	v.Pointer = func(line ComponentLine, x int) {
		if strings.HasSuffix(line.Text, " x") && x == uniseg.StringWidth(line.Text)-1 {
			emit()
		}
	}
	return v, nil
}
func NewHelpView(help *Help, palette Palette) (*RowsView, error) {
	return NewRowsView(help.Layout, palette)
}
func (v *RowsView) SetPalette(palette Palette) error {
	copy, e := componentPalette(GridPalette(palette), "surface", "body", "hint", "field", "button", "error", "selection", "disabled", "edited", "header", "info", "success", "warning")
	if e != nil {
		return e
	}
	v.palette = copy
	return nil
}
