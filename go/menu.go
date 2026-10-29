package tuivory

import (
	"fmt"
	"strings"
)

// MenuItem is host-supplied content and eligibility. Parent IDs describe groups;
// Shortcut is display text, not an application-global key binding.
type MenuItem struct {
	ID, Parent, Label, Secondary, Shortcut, Mnemonic, Icon, ASCIIIcon string
	Disabled, Separator                                               bool
}
type MenuEvent struct{ Kind, ID, ReturnID string }
type MenuBarCell struct {
	ID, Text, Role string
	Start, Width   int
	Focused        bool
}
type MenuBarLayout struct {
	Cells          []MenuBarCell
	Previous, Next bool
}
type Menu struct {
	items                 []MenuItem
	index                 map[string]int
	children              map[string][]string
	opened, context       bool
	path                  []string
	focus                 map[string]string
	top                   map[string]int
	caller, bar           string
	barFirst              int
	BackLabel, EmptyLabel string
}

func NewMenu(items []MenuItem) (*Menu, error) {
	m := &Menu{BackLabel: "Back", EmptyLabel: "(empty)", focus: map[string]string{}, top: map[string]int{}}
	if _, e := m.SetItems(items); e != nil {
		return nil, e
	}
	return m, nil
}
func menuData(items []MenuItem) (map[string]int, map[string][]string, error) {
	if len(items) > 10000 {
		return nil, nil, fmt.Errorf("too many menu items")
	}
	index := map[string]int{}
	children := map[string][]string{}
	keys := map[string]bool{}
	for n, i := range items {
		if i.ID == "" || strings.HasPrefix(i.ID, "@") {
			return nil, nil, fmt.Errorf("invalid menu ID")
		}
		if _, ok := index[i.ID]; ok {
			return nil, nil, fmt.Errorf("duplicate menu ID")
		}
		index[i.ID] = n
		if i.Mnemonic != "" {
			k := strings.ToLower(i.Mnemonic)
			if len(k) != 1 || !strings.Contains("abcdefghijklmnopqrstuvwxyz0123456789", k) || i.Separator {
				return nil, nil, fmt.Errorf("invalid menu mnemonic")
			}
			key := i.Parent + "\x00" + k
			if keys[key] {
				return nil, nil, fmt.Errorf("duplicate sibling mnemonic")
			}
			keys[key] = true
		}
		children[i.Parent] = append(children[i.Parent], i.ID)
	}
	for _, i := range items {
		if i.Separator && len(children[i.ID]) > 0 {
			return nil, nil, fmt.Errorf("separator cannot have children")
		}
		at := i.Parent
		depth := 1
		seen := map[string]bool{i.ID: true}
		for at != "" {
			n, ok := index[at]
			if !ok || seen[at] || items[n].Separator {
				return nil, nil, fmt.Errorf("invalid menu parent/cycle")
			}
			seen[at] = true
			depth++
			if depth > 32 {
				return nil, nil, fmt.Errorf("menu depth exceeds 32")
			}
			at = items[n].Parent
		}
	}
	return index, children, nil
}
func (m *Menu) Items() []MenuItem { return append([]MenuItem(nil), m.items...) }

// SetItems validates atomically and preserves surviving IDs. A removed/disabled
// open ancestor closes the popup explicitly so the host can restore its caller.
func (m *Menu) SetItems(items []MenuItem) (MenuEvent, error) {
	index, children, e := menuData(items)
	if e != nil {
		return MenuEvent{}, e
	}
	m.items = append([]MenuItem(nil), items...)
	m.index = index
	m.children = children
	for parent := range m.focus {
		if _, ok := index[parent]; parent != "" && !ok {
			delete(m.focus, parent)
			delete(m.top, parent)
		}
	}
	if !m.usable(m.bar, "") {
		m.bar = m.first("")
	}
	for n, id := range m.path {
		parent := ""
		if n > 0 {
			parent = m.path[n-1]
		}
		if !m.usable(id, parent) || len(m.children[id]) == 0 {
			return m.Close(), nil
		}
	}
	if m.opened {
		m.reconcile()
	}
	return MenuEvent{}, nil
}
func (m *Menu) usable(id, parent string) bool {
	n, ok := m.index[id]
	return ok && m.items[n].Parent == parent && !m.items[n].Disabled && !m.items[n].Separator
}
func (m *Menu) first(parent string) string {
	for _, id := range m.children[parent] {
		if m.usable(id, parent) {
			return id
		}
	}
	return ""
}
func (m *Menu) parent() string {
	if len(m.path) > 0 {
		return m.path[len(m.path)-1]
	}
	return ""
}
func (m *Menu) backAllowed() bool { return len(m.path) > 1 || (m.context && len(m.path) > 0) }
func (m *Menu) reconcile() {
	p := m.parent()
	if m.focus[p] == "@back" && m.backAllowed() {
		return
	}
	if !m.usable(m.focus[p], p) {
		m.focus[p] = m.first(p)
		if m.focus[p] == "" && m.backAllowed() {
			m.focus[p] = "@back"
		}
	}
}
func (m *Menu) Opened() bool         { return m.opened }
func (m *Menu) Path() []string       { return append([]string(nil), m.path...) }
func (m *Menu) FocusedID() string    { return m.focus[m.parent()] }
func (m *Menu) ReturnID() string     { return m.caller }
func (m *Menu) BarFocusedID() string { return m.bar }
func (m *Menu) Title() string {
	labels := []string{}
	for _, id := range m.path {
		labels = append(labels, cleanTreeText(m.items[m.index[id]].Label))
	}
	return strings.Join(labels, " / ")
}
func (m *Menu) Open(id, returnID string) MenuEvent {
	path := []string{}
	at := id
	for at != "" {
		n, ok := m.index[at]
		if !ok || m.items[n].Disabled || m.items[n].Separator {
			return MenuEvent{}
		}
		path = append([]string{at}, path...)
		at = m.items[n].Parent
	}
	m.caller = returnID
	m.path = path
	for n, child := range path {
		parent := ""
		if n > 0 {
			parent = path[n-1]
		}
		m.focus[parent] = child
	}
	m.context = id == ""
	m.opened = true
	if len(path) > 0 {
		m.bar = path[0]
	}
	if id != "" && len(m.children[id]) == 0 {
		return m.finish("activate", id)
	}
	m.reconcile()
	return MenuEvent{Kind: "open", ID: id, ReturnID: m.caller}
}
func (m *Menu) finish(kind, id string) MenuEvent {
	m.opened = false
	m.path = nil
	return MenuEvent{kind, id, m.caller}
}
func (m *Menu) Close() MenuEvent {
	if !m.opened {
		return MenuEvent{}
	}
	return m.finish("close", "")
}
func (m *Menu) choices() []string {
	ids := []string{}
	if m.backAllowed() {
		ids = append(ids, "@back")
	}
	p := m.parent()
	for _, id := range m.children[p] {
		if m.usable(id, p) {
			ids = append(ids, id)
		}
	}
	return ids
}
func (m *Menu) Back() MenuEvent {
	if !m.opened {
		return MenuEvent{}
	}
	if !m.backAllowed() {
		return m.Close()
	}
	m.path = m.path[:len(m.path)-1]
	m.reconcile()
	return MenuEvent{Kind: "back", ID: m.parent(), ReturnID: m.caller}
}
func (m *Menu) Focus(id string) bool {
	if !m.opened {
		return false
	}
	if id == "@back" && m.backAllowed() {
		m.focus[m.parent()] = id
		return true
	}
	if !m.usable(id, m.parent()) {
		return false
	}
	m.focus[m.parent()] = id
	return true
}
func (m *Menu) Click(id string) MenuEvent {
	if !m.Focus(id) {
		return MenuEvent{}
	}
	return m.Handle("activate", "", 1)
}
func (m *Menu) Handle(action, value string, height int) MenuEvent {
	if !m.opened {
		return MenuEvent{}
	}
	m.reconcile()
	p := m.parent()
	id := m.focus[p]
	switch action {
	case "cancel", "back":
		return m.Back()
	case "left":
		if m.backAllowed() {
			return m.Back()
		}
		if m.context {
			return MenuEvent{}
		}
		return m.switchRoot(-1)
	case "right":
		if m.usable(id, p) && len(m.children[id]) > 0 {
			return m.enter(id)
		}
		if !m.backAllowed() && !m.context {
			return m.switchRoot(1)
		}
		return MenuEvent{}
	case "activate":
		if id == "@back" {
			return m.Back()
		}
		if !m.usable(id, p) {
			return MenuEvent{}
		}
		if len(m.children[id]) > 0 {
			return m.enter(id)
		}
		return m.finish("activate", id)
	case "mnemonic":
		for _, candidate := range m.children[p] {
			i := m.items[m.index[candidate]]
			if m.usable(candidate, p) && i.Mnemonic != "" && strings.EqualFold(i.Mnemonic, value) {
				m.focus[p] = candidate
				return m.Handle("activate", "", height)
			}
		}
		return MenuEvent{}
	}
	ids := m.choices()
	if len(ids) == 0 {
		return MenuEvent{}
	}
	at := 0
	for n, c := range ids {
		if c == id {
			at = n
		}
	}
	switch action {
	case "previous", "up":
		at = (at + len(ids) - 1) % len(ids)
	case "next", "down":
		at = (at + 1) % len(ids)
	case "first":
		at = 0
	case "last":
		at = len(ids) - 1
	case "page_up":
		at = max(0, at-max(1, height-1))
	case "page_down":
		at = min(len(ids)-1, at+max(1, height-1))
	default:
		return MenuEvent{}
	}
	m.focus[p] = ids[at]
	return MenuEvent{Kind: "focus", ID: ids[at], ReturnID: m.caller}
}
func (m *Menu) enter(id string) MenuEvent {
	m.path = append(m.path, id)
	m.reconcile()
	return MenuEvent{Kind: "open", ID: id, ReturnID: m.caller}
}
func (m *Menu) switchRoot(delta int) MenuEvent {
	ids := []string{}
	for _, id := range m.children[""] {
		if m.usable(id, "") {
			ids = append(ids, id)
		}
	}
	if len(ids) == 0 {
		return MenuEvent{}
	}
	at := 0
	for n, id := range ids {
		if id == m.bar {
			at = n
		}
	}
	at = (at + delta + len(ids)) % len(ids)
	// Root switching opens groups; it never executes an adjacent leaf command.
	for n := 0; n < len(ids); n++ {
		if ids[at] != m.bar && len(m.children[ids[at]]) > 0 {
			return m.Open(ids[at], m.caller)
		}
		at = (at + delta + len(ids)) % len(ids)
	}
	return MenuEvent{}
}
func (m *Menu) HandleBar(action, value string) MenuEvent {
	ids := []string{}
	for _, id := range m.children[""] {
		if m.usable(id, "") {
			ids = append(ids, id)
		}
	}
	if len(ids) == 0 {
		return MenuEvent{}
	}
	at := 0
	for n, id := range ids {
		if id == m.bar {
			at = n
		}
	}
	switch action {
	case "previous", "left":
		at = (at + len(ids) - 1) % len(ids)
	case "next", "right":
		at = (at + 1) % len(ids)
	case "first":
		at = 0
	case "last":
		at = len(ids) - 1
	case "activate", "down":
		return MenuEvent{Kind: "open_request", ID: ids[at]}
	case "mnemonic":
		for _, id := range ids {
			if i := m.items[m.index[id]]; i.Mnemonic != "" && strings.EqualFold(i.Mnemonic, value) {
				m.bar = id
				return MenuEvent{Kind: "open_request", ID: id}
			}
		}
		return MenuEvent{}
	default:
		return MenuEvent{}
	}
	m.bar = ids[at]
	return MenuEvent{Kind: "focus", ID: m.bar}
}
