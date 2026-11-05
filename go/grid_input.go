package tuivory

// Input routes only grid-local keys/paste. Hosts keep global bindings and clipboard I/O.
func (g *Grid) Input(e InputEvent, width, height int) GridEvent {
	if e.Phase == "release" {
		return GridEvent{}
	}
	if e.Kind == "resize" {
		g.Layout(e.Width, e.Height)
		return GridEvent{}
	}
	if (e.Kind == "key" || e.Kind == "paste") && g.options.DisableKeyboard {
		return GridEvent{}
	}
	has := func(m string) bool {
		for _, v := range e.Modifiers {
			if v == m {
				return true
			}
		}
		return false
	}
	if g.work.detail != nil {
		if e.Key == "escape" {
			g.CloseDetails()
			return GridEvent{}
		}
		a, t := e.EditingAction()
		v := g.work.detail.Handle(a, t)
		return GridEvent{Kind: v.Kind, Text: v.Text}
	}
	if g.work.findBuffer != nil {
		if e.Key == "escape" {
			g.work.findBuffer = nil
			return GridEvent{}
		}
		if e.Key == "enter" {
			q := g.work.findBuffer.Text()
			g.work.findBuffer = nil
			g.SetFind(q, g.work.findOptions)
			if has("ctrl") {
				return g.RequestSearch(q)
			}
			r, ok := g.FindNext(false)
			if ok {
				return GridEvent{Kind: "find", RowID: r.RowID, ColumnID: r.ColumnID}
			}
			return GridEvent{Kind: "find_end"}
		}
		a, t := e.EditingAction()
		g.work.findBuffer.Handle(a, t)
		return GridEvent{}
	}
	if g.work.edit != nil {
		action, text := e.EditingAction()
		switch e.Key {
		case "enter":
			action = "submit"
		case "escape":
			action = "cancel"
		case "tab":
			action = "next"
			if has("shift") {
				action = "previous"
			}
		case "n":
			if has("ctrl") {
				action = "null"
			}
		}
		return g.EditInput(action, text)
	}
	if e.Kind == "paste" {
		p, err := g.RequestPaste(e.Text, GridPasteOptions{})
		if err != nil {
			return GridEvent{Kind: "paste_rejected", Text: err.Error()}
		}
		_ = p
		return GridEvent{Kind: "paste_request"}
	}
	if e.Kind != "key" {
		return GridEvent{}
	}
	if has("alt") {
		switch e.Key {
		case "p":
			return g.Handle("pin_column", height)
		case "h":
			return g.Handle("hide_column", height)
		case "u":
			l := g.ColumnLayout()
			for i := range l {
				l[i].Hidden = false
			}
			_ = g.SetColumnLayout(l)
			return GridEvent{Kind: "columns"}
		}
	}
	if has("ctrl") {
		if e.Key == "s" {
			return GridEvent{Kind: "view_save"}
		}
		if e.Key == "r" {
			return GridEvent{Kind: "view_restore"}
		}
		if has("shift") && (e.Key == "left" || e.Key == "right") {
			a := "column_previous"
			if e.Key == "right" {
				a = "column_next"
			}
			return g.Handle(a, height)
		}
		switch e.Key {
		case "f":
			g.work.findBuffer = NewTextBuffer(g.work.query)
			g.work.findBuffer.SingleLine = true
			return GridEvent{}
		case "p":
			return g.Handle("pin_column", height)
		case "h":
			return g.Handle("hide_column", height)
		case "c":
			return g.Handle("copy", height)
		}
	}
	action := map[string]string{"enter": "activate", "escape": "cancel", "left": "left", "right": "right", "up": "up", "down": "down", "home": "first", "end": "last", "page_up": "page_up", "page_down": "page_down", "f6": "row_mode", "f7": "widen", "f8": "narrow", "f9": "sort", "f10": "range_mode", "f11": "autofit", "f12": "details", " ": "select", "tab": "next", "f4": "find_next"}[e.Key]
	if e.Key == "f4" && has("shift") {
		action = "find_previous"
	}
	if e.Key == "tab" && has("shift") {
		action = "previous"
	}
	if has("shift") && (action == "left" || action == "right" || action == "up" || action == "down") {
		action = "extend_" + action
	}
	if has("alt") && (e.Key == "left" || e.Key == "right") {
		action = "cell_pan_" + e.Key
	}
	if e.Key == "f5" {
		return g.RequestFilter(g.Status.Filter)
	}
	if action != "" {
		return g.Handle(action, height)
	}
	if e.Text != "" && !has("ctrl") && !has("alt") && g.work.editOptions.StartTyping && g.BeginEdit(e.Text) {
		return GridEvent{Kind: "edit_begin", RowID: g.RowID, ColumnID: g.ColumnID}
	}
	return GridEvent{}
}
