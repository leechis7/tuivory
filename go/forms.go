package tuivory

import (
	"fmt"
	"github.com/rivo/uniseg"
	"strings"
	"unicode"
)

// ComponentLine is literal presentation data; ID identifies a hit-tested item.
type ComponentSpan struct {
	Start, Width int
	Text, Role   string
	Focused      bool
}

type ComponentLine struct {
	ID, Text, Role, Value string
	Focused               bool
	Spans                 []ComponentSpan
}
type FormOption struct {
	ID, Label string
	Disabled  bool
}
type FormField struct {
	ID, Kind, Label, Help, Error, Value, Choice, Action string
	Options                                             []FormOption
	State                                               ControlState
	Required, Checked, Open                             bool
	Pending                                             string
	Cursor                                              int // Grapheme index, never a byte offset.
}
type FormEvent struct {
	Kind, ID string
	Missing  []string
}
type Form struct {
	fields []FormField
	focus  *FocusStack
}

func clusters(s string) []string {
	g := uniseg.NewGraphemes(s)
	out := []string{}
	for g.Next() {
		out = append(out, g.Str())
	}
	return out
}
func fieldCopy(fields []FormField) []FormField {
	out := append([]FormField(nil), fields...)
	for i := range out {
		out[i].Options = append([]FormOption(nil), out[i].Options...)
	}
	return out
}
func NewForm(fields []FormField) (*Form, error) {
	fields = fieldCopy(fields)
	targets := []FocusTarget{}
	for i := range fields {
		f := &fields[i]
		switch f.Kind {
		case "text", "textarea", "button", "checkbox", "radio", "select":
		default:
			return nil, fmt.Errorf("unknown field kind %q", f.Kind)
		}
		if f.Open {
			return nil, fmt.Errorf("initial select must be closed")
		}
		seen := map[string]bool{}
		valid := f.Choice == ""
		for _, o := range f.Options {
			if o.ID == "" || seen[o.ID] {
				return nil, fmt.Errorf("invalid option ID")
			}
			seen[o.ID] = true
			if o.ID == f.Choice {
				valid = true
			}
		}
		if !valid {
			return nil, fmt.Errorf("unknown choice")
		}
		f.Cursor = len(clusters(f.Value))
		targets = append(targets, FocusTarget{ID: f.ID, State: f.State})
	}
	focus, err := NewFocusStack("form", targets)
	if err != nil {
		return nil, err
	}
	return &Form{fields: fields, focus: focus}, nil
}
func (f *Form) Fields() []FormField { return fieldCopy(f.fields) }
func (f *Form) Focused() string     { return f.focus.Focused() }
func (f *Form) Focus(id string) bool {
	for i := range f.fields {
		f.fields[i].Open = false
	}
	return f.focus.Focus(id)
}
func (f *Form) SetState(id string, state ControlState) bool {
	found := false
	targets := []FocusTarget{}
	for i := range f.fields {
		field := &f.fields[i]
		if field.ID == id {
			field.State = state
			if !state.Visual().Editable {
				field.Open = false
			}
			found = true
		}
		targets = append(targets, FocusTarget{ID: field.ID, State: field.State})
	}
	if found {
		_ = f.focus.Update("form", targets)
	}
	return found
}
func (f *Form) SetFeedback(id, help, message string) bool {
	for i := range f.fields {
		if f.fields[i].ID == id {
			f.fields[i].Help = help
			f.fields[i].Error = message
			f.fields[i].State.Invalid = message != ""
			return true
		}
	}
	return false
}
func (f *Form) Missing() []string {
	out := []string{}
	for _, field := range f.fields {
		if field.State.Disabled {
			continue
		}
		empty := false
		switch field.Kind {
		case "text", "textarea":
			empty = strings.TrimSpace(field.Value) == ""
		case "checkbox":
			empty = !field.Checked
		case "radio", "select":
			empty = field.Choice == ""
		}
		if field.State.Invalid || field.Error != "" || field.Required && empty {
			out = append(out, field.ID)
		}
	}
	return out
}
func (f *Form) Handle(action, text string) FormEvent {
	event := FormEvent{}
	if action == "next" || action == "previous" {
		for i := range f.fields {
			f.fields[i].Open = false
		}
		f.focus.Move(action == "previous")
		return event
	}
	if action == "submit" {
		missing := f.Missing()
		if len(missing) > 0 {
			return FormEvent{Kind: "invalid", Missing: missing}
		}
		return FormEvent{Kind: "submit"}
	}
	for i := range f.fields {
		field := &f.fields[i]
		if field.ID != f.Focused() {
			continue
		}
		event.ID = field.ID
		if action == "cancel" {
			if field.Open {
				field.Open = false
				return FormEvent{}
			}
			return FormEvent{Kind: "cancel", ID: field.ID}
		}
		navigate := (field.Kind == "text" || field.Kind == "textarea") && (action == "left" || action == "right" || action == "home" || action == "end") && !field.State.Disabled
		if !field.State.Visual().Activatable && !navigate {
			return FormEvent{}
		}
		if field.Kind == "button" && action == "activate" {
			switch field.Action {
			case "submit":
				return f.Handle("submit", "")
			case "cancel":
				return FormEvent{Kind: "cancel", ID: field.ID}
			default:
				return FormEvent{Kind: "activate", ID: field.ID}
			}
		}
		if !field.State.Visual().Editable && !navigate {
			return FormEvent{}
		}
		if field.Kind == "checkbox" && (action == "activate" || action == "toggle") {
			field.Checked = !field.Checked
			field.State.Edited = true
			event.Kind = "change"
			return event
		}
		if field.Kind == "radio" || field.Kind == "select" {
			if action == "activate" || action == "toggle" {
				if field.Kind == "select" {
					if field.Open {
						field.Choice = field.Pending
						field.Open = false
						field.State.Edited = true
						event.Kind = "change"
						return event
					}
					field.Open = true
					field.Pending = field.Choice
					if field.Pending == "" {
						for _, o := range field.Options {
							if !o.Disabled {
								field.Pending = o.ID
								break
							}
						}
					}
					return FormEvent{}
				}
			}
			if action == "left" || action == "right" || action == "up" || action == "down" || action == "activate" || action == "toggle" {
				ids := []string{}
				for _, o := range field.Options {
					if !o.Disabled {
						ids = append(ids, o.ID)
					}
				}
				if len(ids) == 0 {
					return FormEvent{}
				}
				current := field.Choice
				if field.Kind == "select" {
					if !field.Open {
						return FormEvent{}
					}
					current = field.Pending
				}
				at := -1
				for j, id := range ids {
					if id == current {
						at = j
					}
				}
				if action == "left" || action == "up" {
					if at < 0 {
						at = 0
					}
					at = (at + len(ids) - 1) % len(ids)
				} else {
					at = (at + 1) % len(ids)
				}
				if field.Kind == "select" {
					field.Pending = ids[at]
				} else {
					field.Choice = ids[at]
					field.State.Edited = true
					event.Kind = "change"
				}
				return event
			}
			return FormEvent{}
		}
		if field.Kind != "text" && field.Kind != "textarea" {
			return FormEvent{}
		}
		g := clusters(field.Value)
		field.Cursor = max(0, min(field.Cursor, len(g)))
		at := field.Cursor
		switch action {
		case "left":
			field.Cursor = max(0, at-1)
		case "right":
			field.Cursor = min(len(g), at+1)
		case "home":
			field.Cursor = 0
		case "end":
			field.Cursor = len(g)
		case "backspace":
			if at > 0 {
				g = append(g[:at-1], g[at:]...)
				field.Cursor--
				event.Kind = "change"
			}
		case "delete":
			if at < len(g) {
				g = append(g[:at], g[at+1:]...)
				event.Kind = "change"
			}
		case "activate":
			if field.Kind == "text" {
				return f.Handle("submit", "")
			}
			text = "\n"
			fallthrough
		case "insert":
			text = strings.Map(func(r rune) rune {
				if unicode.IsControl(r) && !(r == '\n' && field.Kind == "textarea") {
					return -1
				}
				return r
			}, text)
			if text != "" {
				addition := clusters(text)
				next := append([]string(nil), g[:at]...)
				next = append(next, addition...)
				g = append(next, g[at:]...)
				field.Cursor += len(addition)
				event.Kind = "change"
			}
		}
		if event.Kind == "change" {
			field.Value = strings.Join(g, "")
			field.State.Edited = true
		}
		return event
	}
	return FormEvent{}
}
func editDisplay(value string, cursor, width int, focused bool) string {
	g := clusters(value)
	cursor = max(0, min(cursor, len(g)))
	if !focused {
		return CellText(value, width)
	}
	before := strings.Join(g[:cursor], "")
	after := strings.Join(g[cursor:], "")
	before = tailCells(before, max(0, width-1))
	if width <= 0 {
		return ""
	}
	return before + "|" + CellText(after, max(0, width-uniseg.StringWidth(before)-1))
}

// Layout follows the focused field vertically. The visible caret is presentation
// only; it is never inserted into Value or copied data.
func (f *Form) Layout(width, height int) []ComponentLine {
	rows := []ComponentLine{}
	anchor := 0
	for _, field := range f.fields {
		focused := field.ID == f.Focused()
		v := field.State.Visual()
		required := ""
		if field.Required {
			required = " *"
		}
		prefix := "  "
		if focused {
			prefix = "> "
		}
		markers := v.Markers
		if field.State.Disabled {
			markers = strings.TrimPrefix(markers, "-")
		}
		rows = append(rows, ComponentLine{ID: field.ID, Text: prefix + field.Label + required + " " + markers, Role: v.Role, Focused: focused})
		if focused {
			anchor = len(rows) - 1
		}
		value := field.Value
		switch field.Kind {
		case "text", "textarea":
			valueRole := "field"
			if field.State.Disabled {
				valueRole = "disabled"
			}
			position := 0
			for _, line := range strings.Split(value, "\n") {
				count := len(clusters(line))
				caret := focused && field.Cursor >= position && field.Cursor <= position+count
				display := editDisplay(line, field.Cursor-position, max(0, width-2), caret)
				rows = append(rows, ComponentLine{ID: field.ID, Text: "  " + display, Role: valueRole})
				position += count + 1
			}
		case "checkbox":
			value = "[ ]"
			if field.Checked {
				value = "[x]"
			}
			rows = append(rows, ComponentLine{ID: field.ID, Text: "  " + value, Role: v.Role})
		case "radio", "select":
			for _, o := range field.Options {
				current := field.Choice
				if field.Open {
					current = field.Pending
				}
				mark := "( ) "
				if o.ID == current {
					mark = "(*) "
				}
				role := v.Role
				if o.Disabled || field.State.Disabled {
					role = "disabled"
				}
				if field.Kind == "select" && !field.Open && o.ID != field.Choice {
					continue
				}
				rows = append(rows, ComponentLine{ID: field.ID, Text: "  " + mark + o.Label, Role: role, Value: o.ID})
			}
		case "button":
			valueRole := "button"
			if field.State.Disabled {
				valueRole = "disabled"
			}
			rows = append(rows, ComponentLine{ID: field.ID, Text: "  [ " + field.Label + " ]", Role: valueRole, Focused: focused})
		}
		if field.Error != "" {
			rows = append(rows, ComponentLine{ID: field.ID, Text: "! " + field.Error, Role: "error"})
		} else if field.Help != "" {
			rows = append(rows, ComponentLine{ID: field.ID, Text: "  " + field.Help, Role: "hint"})
		}
	}
	start := max(0, anchor-max(0, height-2))
	start = min(start, max(0, len(rows)-height))
	end := min(len(rows), start+max(0, height))
	out := append([]ComponentLine(nil), rows[start:end]...)
	for i := range out {
		out[i].Text = CellText(out[i].Text, width)
	}
	return out
}

// Click commits an enabled option, or activates a button/check/select. Text clicks focus only.
func (f *Form) Click(id, option string) FormEvent {
	for _, field := range f.fields {
		if field.ID == id {
			if field.State.Disabled {
				return FormEvent{}
			}
			if option != "" {
				for _, o := range field.Options {
					if o.ID == option && o.Disabled {
						return FormEvent{}
					}
				}
			}
			break
		}
	}
	if f.Focused() != id && !f.Focus(id) {
		return FormEvent{}
	}
	for i := range f.fields {
		field := &f.fields[i]
		if field.ID != id {
			continue
		}
		if !field.State.Visual().Editable {
			return FormEvent{}
		}
		if field.Kind == "select" && !field.Open {
			return f.Handle("activate", "")
		}
		if option != "" && (field.Kind == "radio" || field.Kind == "select") {
			for _, o := range field.Options {
				if o.ID == option && !o.Disabled {
					field.Choice = option
					field.Open = false
					field.State.Edited = true
					return FormEvent{Kind: "change", ID: id}
				}
			}
			return FormEvent{}
		}
		if field.Kind == "button" || field.Kind == "checkbox" || field.Kind == "select" {
			return f.Handle("activate", "")
		}
	}
	return FormEvent{}
}
