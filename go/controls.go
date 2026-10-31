package tuivory

// Control is a standalone input, check, select or button backed by the same
// form model. Data, eligibility and activation remain host-owned.
type Control struct {
	*Form
	ID string
}

func NewControl(field FormField) (*Control, error) {
	f, e := NewForm([]FormField{field})
	if e != nil {
		return nil, e
	}
	return &Control{Form: f, ID: field.ID}, nil
}
func NewInput(id, label, value string, secret bool) (*Control, error) {
	kind := "text"
	if secret {
		kind = "password"
	}
	return NewControl(FormField{ID: id, Kind: kind, Label: label, Value: value})
}
func NewButton(id, label string) (*Control, error) {
	return NewControl(FormField{ID: id, Kind: "button", Label: label})
}
func NewCheck(id, label string, checked bool) (*Control, error) {
	return NewControl(FormField{ID: id, Kind: "checkbox", Label: label, Checked: checked})
}
func NewSelect(id, label string, options []FormOption, choice string) (*Control, error) {
	return NewControl(FormField{ID: id, Kind: "select", Label: label, Options: options, Choice: choice})
}
func NewControlView(control *Control, palette Palette, onEvent func(FormEvent)) (*RowsView, error) {
	v, e := NewFormView(control.Form, palette, onEvent)
	if e != nil {
		return nil, e
	}
	v.Rows = control.Layout
	return v, nil
}
func (c *Control) Layout(w, h int) []ComponentLine {
	fields := c.Fields()
	if len(fields) == 1 && fields[0].Kind == "button" {
		field := fields[0]
		if w <= 0 || h <= 0 {
			return nil
		}
		role := "button"
		label := field.Label
		if field.State.Busy {
			role = "hint"
			label += " ~"
		}
		if field.State.Disabled {
			role = "disabled"
		}
		return []ComponentLine{{ID: field.ID, Text: CellText("[ "+label+" ]", w), Role: role, Focused: true}}
	}
	return c.Form.Layout(w, h)
}
