package tuivory

import (
	"fmt"
	"strings"
	"unicode"
)

type ListItem struct {
	ID, Label, Secondary, Shortcut, Icon, ASCIIIcon string
	Disabled, Separator                             bool
}
type ListEvent struct{ Kind, ID, Query string }
type ListModel struct {
	items                    []ListItem
	Focused, Selected, Query string
	Empty                    string
}

func NewList(items []ListItem) (*ListModel, error) {
	m := &ListModel{Empty: "(empty)"}
	if e := m.SetItems(items); e != nil {
		return nil, e
	}
	return m, nil
}
func (m *ListModel) Items() []ListItem { return append([]ListItem(nil), m.items...) }
func (m *ListModel) SetItems(items []ListItem) error {
	seen := map[string]bool{}
	for _, i := range items {
		if i.ID == "" || seen[i.ID] {
			return fmt.Errorf("empty or duplicate list ID")
		}
		seen[i.ID] = true
	}
	m.items = append([]ListItem(nil), items...)
	if !seen[m.Selected] {
		m.Selected = ""
	}
	m.reconcile()
	return nil
}
func (m *ListModel) visible() []ListItem {
	out := []ListItem{}
	q := strings.ToLower(m.Query)
	for _, i := range m.items {
		if q != "" && (i.Separator || !strings.Contains(strings.ToLower(i.Label+" "+i.Secondary), q)) {
			continue
		}
		out = append(out, i)
	}
	return out
}
func (m *ListModel) Focus(id string) bool {
	for _, i := range m.visible() {
		if i.ID == id && !i.Disabled && !i.Separator {
			m.Focused = id
			return true
		}
	}
	return false
}
func (m *ListModel) reconcile() {
	if m.Focus(m.Focused) {
		return
	}
	m.Focused = ""
	for _, i := range m.visible() {
		if !i.Disabled && !i.Separator {
			m.Focused = i.ID
			break
		}
	}
}
func (m *ListModel) SetQuery(query string) ListEvent {
	m.Query = strings.Map(func(r rune) rune {
		if unicode.IsControl(r) {
			return -1
		}
		return r
	}, query)
	m.reconcile()
	return ListEvent{Kind: "query", Query: m.Query}
}
func (m *ListModel) Handle(action string, height int) ListEvent {
	m.reconcile()
	ids := []string{}
	at := 0
	for _, i := range m.visible() {
		if !i.Disabled && !i.Separator {
			if i.ID == m.Focused {
				at = len(ids)
			}
			ids = append(ids, i.ID)
		}
	}
	if len(ids) == 0 {
		return ListEvent{}
	}
	switch action {
	case "activate", "select":
		m.Selected = m.Focused
		return ListEvent{Kind: action, ID: m.Focused}
	case "next":
		at = min(len(ids)-1, at+1)
	case "previous":
		at = max(0, at-1)
	case "first":
		at = 0
	case "last":
		at = len(ids) - 1
	case "page_down":
		at = min(len(ids)-1, at+max(1, height-1))
	case "page_up":
		at = max(0, at-max(1, height-1))
	default:
		return ListEvent{}
	}
	m.Focused = ids[at]
	return ListEvent{Kind: "focus", ID: m.Focused}
}
func (m *ListModel) Layout(width, height int, ascii bool) []ComponentLine {
	rows := []ComponentLine{}
	anchor := 0
	for _, i := range m.visible() {
		if i.ID == m.Focused {
			anchor = len(rows)
		}
		if i.Separator {
			rows = append(rows, ComponentLine{ID: i.ID, Text: "--- " + i.Label + " ---", Role: "hint"})
			continue
		}
		role := "body"
		if i.Disabled {
			role = "disabled"
		} else if i.ID == m.Selected {
			role = "selection"
		}
		mark := "  "
		if i.ID == m.Focused {
			mark = "> "
		}
		if i.ID == m.Selected {
			mark += "* "
		}
		icon := i.Icon
		if ascii {
			icon = i.ASCIIIcon
		}
		if icon != "" {
			icon += " "
		}
		shortcut := ""
		if i.Shortcut != "" {
			shortcut = " [" + i.Shortcut + "]"
		}
		rows = append(rows, ComponentLine{ID: i.ID, Text: mark + icon + i.Label + shortcut, Role: role, Focused: i.ID == m.Focused, Value: i.ID})
		if i.Secondary != "" {
			rows = append(rows, ComponentLine{ID: i.ID, Text: "    " + i.Secondary, Role: "hint", Value: i.ID})
		}
	}
	if len(rows) == 0 {
		rows = append(rows, ComponentLine{Text: m.Empty, Role: "hint"})
	}
	start := min(max(0, anchor-max(0, height-2)), max(0, len(rows)-height))
	end := min(len(rows), start+max(0, height))
	out := append([]ComponentLine(nil), rows[start:end]...)
	for i := range out {
		out[i].Text = CellText(out[i].Text, width)
	}
	return out
}

// SearchPicker composes query entry, a list and pending choice. The host owns
// remote search and popup placement; cancel never changes Value.
type SearchPicker struct {
	List  *ListModel
	Open  bool
	Value string
}

func NewSearchPicker(items []ListItem) (*SearchPicker, error) {
	m, e := NewList(items)
	if e != nil {
		return nil, e
	}
	return &SearchPicker{List: m}, nil
}
func (p *SearchPicker) Handle(action, text string, height int) ListEvent {
	switch action {
	case "open":
		p.Open = true
		p.List.SetQuery("")
		p.List.Focus(p.Value)
		return ListEvent{Kind: "open"}
	case "cancel":
		p.Open = false
		return ListEvent{Kind: "cancel"}
	case "insert", "backspace":
		if !p.Open {
			p.Handle("open", "", height)
		}
		query := p.List.Query
		if action == "insert" {
			query += text
		} else {
			g := clusters(query)
			if len(g) > 0 {
				query = strings.Join(g[:len(g)-1], "")
			}
		}
		return p.List.SetQuery(query)
	case "activate":
		if !p.Open {
			return p.Handle("open", "", height)
		}
		event := p.List.Handle("activate", height)
		if event.ID != "" {
			p.Value = event.ID
			p.Open = false
			event.Kind = "change"
		}
		return event
	}
	if !p.Open {
		return ListEvent{}
	}
	return p.List.Handle(action, height)
}
func (p *SearchPicker) Click(id string) ListEvent {
	if !p.List.Focus(id) {
		return ListEvent{}
	}
	return p.Handle("activate", "", 1)
}
func (p *SearchPicker) Layout(width, height int, ascii bool) []ComponentLine {
	if height <= 0 {
		return nil
	}
	if !p.Open {
		label := p.List.Empty
		for _, i := range p.List.Items() {
			if i.ID == p.Value {
				label = i.Label
			}
		}
		return []ComponentLine{{Text: CellText("v "+label, width), Role: "field"}}
	}
	out := []ComponentLine{{Text: CellText("? "+editDisplay(p.List.Query, len(clusters(p.List.Query)), max(0, width-2), true), width), Role: "field"}}
	return append(out, p.List.Layout(width, height-1, ascii)...)
}
