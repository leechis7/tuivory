package tuivory

import (
	"fmt"
	"github.com/rivo/uniseg"
	"sort"
	"strings"
)

// CellText clips literal text at grapheme boundaries. A trailing ~ marks loss.
func CellText(text string, width int) string {
	text = cleanTreeText(text)
	width = max(0, width)
	if uniseg.StringWidth(text) <= width {
		return text
	}
	if width == 0 {
		return ""
	}
	var out strings.Builder
	used := 0
	g := uniseg.NewGraphemes(text)
	for g.Next() {
		if used+g.Width() > width-1 {
			break
		}
		out.WriteString(g.Str())
		used += g.Width()
	}
	return out.String() + "~"
}
func tailCells(text string, width int) string {
	text = cleanTreeText(text)
	if uniseg.StringWidth(text) <= max(0, width) {
		return text
	}
	if width <= 0 {
		return ""
	}
	var clusters []string
	g := uniseg.NewGraphemes(text)
	for g.Next() {
		clusters = append(clusters, g.Str())
	}
	used := 0
	start := len(clusters)
	for start > 0 {
		w := uniseg.StringWidth(clusters[start-1])
		if used+w > width-1 {
			break
		}
		used += w
		start--
	}
	return "~" + strings.Join(clusters[start:], "")
}

type TabItem struct {
	ID, Title                  string
	Edited, Closable, Disabled bool
}
type TabState struct {
	Active, Focused string
	First           int
}
type TabAction uint8

const (
	TabPrevious TabAction = iota
	TabNext
	TabFirst
	TabLast
	TabActivate
	TabClose
)

type TabEvent struct{ Kind, ID string }
type TabCell struct {
	ID, Text                  string
	Start, Width              int
	Active, Focused, Disabled bool
}
type TabLayout struct {
	Cells          []TabCell
	Previous, Next bool
}
type Tabs struct{ items []TabItem }

func NewTabs(items []TabItem) (*Tabs, error) {
	seen := map[string]bool{}
	for _, item := range items {
		if item.ID == "" || seen[item.ID] {
			return nil, fmt.Errorf("tabs: empty/duplicate ID %q", item.ID)
		}
		seen[item.ID] = true
	}
	return &Tabs{items: append([]TabItem(nil), items...)}, nil
}
func (t *Tabs) Reconcile(s *TabState) {
	active, focus := false, false
	first := ""
	for _, item := range t.items {
		if !item.Disabled {
			if first == "" {
				first = item.ID
			}
			active = active || item.ID == s.Active
			focus = focus || item.ID == s.Focused
		}
	}
	if !active {
		s.Active = first
	}
	if !focus {
		s.Focused = s.Active
	}
	s.First = min(max(0, s.First), max(0, len(t.items)-1))
}
func (t *Tabs) Handle(s *TabState, action TabAction) TabEvent {
	t.Reconcile(s)
	var enabled []int
	current := 0
	for i, item := range t.items {
		if !item.Disabled {
			if item.ID == s.Focused {
				current = len(enabled)
			}
			enabled = append(enabled, i)
		}
	}
	if len(enabled) == 0 {
		return TabEvent{}
	}
	item := t.items[enabled[current]]
	switch action {
	case TabActivate:
		s.Active = item.ID
		return TabEvent{"activate", item.ID}
	case TabClose:
		if item.Closable {
			return TabEvent{"close", item.ID}
		}
		return TabEvent{}
	case TabPrevious:
		current = max(0, current-1)
	case TabNext:
		current = min(len(enabled)-1, current+1)
	case TabFirst:
		current = 0
	case TabLast:
		current = len(enabled) - 1
	}
	target := t.items[enabled[current]].ID
	if target != s.Focused {
		s.Focused = target
		return TabEvent{"focus", target}
	}
	return TabEvent{}
}
func tabText(item TabItem, width int, active, focused bool) string {
	left, right := " ", " "
	if active {
		left, right = "[", "]"
	}
	mark := " "
	if focused {
		mark = ">"
	}
	suffix := ""
	if item.Edited {
		suffix += " *"
	}
	if item.Closable {
		suffix += " x"
	}
	// Always reserve state markers before truncating a long title.
	return CellText(mark+left+CellText(item.Title, max(0, width-3-len(suffix)))+suffix+right, width)
}
func (t *Tabs) Layout(s *TabState, width int) TabLayout {
	t.Reconcile(s)
	out := TabLayout{}
	if width <= 2 || len(t.items) == 0 {
		return out
	}
	target := 0
	for i, item := range t.items {
		if item.ID == s.Focused {
			target = i
			break
		}
	}
	s.First = min(s.First, target)
	available := width - 2
	widths := func(first int) int {
		total := 0
		for i := first; i <= target; i++ {
			total += min(24, max(6, uniseg.StringWidth(cleanTreeText(t.items[i].Title))+5))
		}
		return total
	}
	for s.First < target && widths(s.First) > available {
		s.First++
	}
	for s.First > 0 && widths(s.First-1) <= available {
		s.First--
	}
	x := 1
	for i := s.First; i < len(t.items) && x < width-1; i++ {
		item := t.items[i]
		w := min(width-1-x, min(24, max(6, uniseg.StringWidth(cleanTreeText(item.Title))+5)))
		if w < 4 && len(out.Cells) > 0 {
			break
		}
		cell := TabCell{ID: item.ID, Start: x, Width: w, Active: item.ID == s.Active, Focused: item.ID == s.Focused, Disabled: item.Disabled}
		cell.Text = tabText(item, w, cell.Active, cell.Focused)
		out.Cells = append(out.Cells, cell)
		x += w
	}
	out.Previous = s.First > 0
	out.Next = s.First+len(out.Cells) < len(t.items)
	return out
}

// Click requests closing only on the x marker; removal/unsaved confirmation is
// a host decision. Overflow arrows move focus without changing the active tab.
func (t *Tabs) Click(s *TabState, column, width int) TabEvent {
	layout := t.Layout(s, width)
	if column == 0 && layout.Previous {
		return t.Handle(s, TabPrevious)
	}
	if column == width-1 && layout.Next {
		return t.Handle(s, TabNext)
	}
	for _, cell := range layout.Cells {
		if column >= cell.Start && column < cell.Start+cell.Width && !cell.Disabled {
			s.Focused = cell.ID
			for _, item := range t.items {
				if item.ID == cell.ID && item.Closable && (strings.HasSuffix(cell.Text, "x]") || strings.HasSuffix(cell.Text, "x ")) && column == cell.Start+uniseg.StringWidth(cell.Text)-2 {
					return TabEvent{"close", cell.ID}
				}
			}
			s.Active = cell.ID
			return TabEvent{"activate", cell.ID}
		}
	}
	return TabEvent{}
}

// SplitState retains the user's preference even when the viewport is compact.
type SplitState struct{ Preferred int }
type SplitSpec struct{ FirstMin, SecondMin int }
type SplitLayout struct {
	First, Divider, Second int
	Compact                bool
}

func (c SplitSpec) Layout(s *SplitState, total int) SplitLayout {
	total = max(0, total)
	a, b := max(1, c.FirstMin), max(1, c.SecondMin)
	if total < a+b+1 {
		return SplitLayout{Second: total, Compact: true}
	}
	first := s.Preferred
	if first <= 0 {
		first = (total - 1) / 2
	}
	first = min(max(a, first), total-1-b)
	return SplitLayout{First: first, Divider: 1, Second: total - first - 1}
}
func (c SplitSpec) Resize(s *SplitState, total, position int) bool {
	layout := c.Layout(s, total)
	if layout.Compact {
		return false
	}
	next := min(max(max(1, c.FirstMin), position), total-1-max(1, c.SecondMin))
	changed := next != layout.First
	s.Preferred = next
	return changed
}

// LineRun is a literal cell range. Empty IDs are decorations, never actions.
type LineRun struct {
	Text, Role, ID string
	Start, Width   int
}

func lineRun(text, role, id string, start int) LineRun {
	text = cleanTreeText(text)
	return LineRun{text, role, id, start, uniseg.StringWidth(text)}
}

type PathItem struct{ ID, Label string }

func Breadcrumbs(items []PathItem, width int) []LineRun {
	if len(items) == 0 || width <= 0 {
		return nil
	}
	width = max(0, width)
	var out []LineRun
	x := 0
	add := func(text, id, role string) { run := lineRun(text, role, id, x); out = append(out, run); x += run.Width }
	full := 0
	for i, item := range items {
		full += uniseg.StringWidth(cleanTreeText(item.Label))
		if i > 0 {
			full += 3
		}
	}
	if full <= width {
		for i, item := range items {
			if i > 0 {
				add(" / ", "", "hint")
			}
			role := "hint"
			if i == len(items)-1 {
				role = "body"
			}
			add(item.Label, item.ID, role)
		}
		return out
	}
	last := items[len(items)-1]
	prefix := ""
	if len(items) > 2 && uniseg.StringWidth(cleanTreeText(items[0].Label))+9+uniseg.StringWidth(cleanTreeText(last.Label)) <= width {
		add(items[0].Label, items[0].ID, "hint")
		prefix = " / ... / "
	} else if len(items) > 1 && width >= 7 {
		prefix = "... / "
	}
	add(prefix, "", "hint")
	add(tailCells(last.Label, width-x), last.ID, "body")
	return out
}

type StatusItem struct {
	ID, Text, Role string
	Priority       int
}
type StatusLayout struct {
	Runs    []LineRun
	Omitted int
}

func statusText(item StatusItem) string {
	prefix := ""
	switch item.Role {
	case "warning", "error":
		prefix = "! "
	case "edited":
		prefix = "* "
	case "success":
		prefix = "+ "
	case "info":
		prefix = "i "
	}
	return prefix + cleanTreeText(item.Text)
}

// StatusLine keeps high priority entries first and lower priority entries whole.
// Tiny widths preserve the highest priority cue before an omission counter.
func StatusLine(items []StatusItem, width int) StatusLayout {
	sorted := append([]StatusItem(nil), items...)
	sort.SliceStable(sorted, func(i, j int) bool { return sorted[i].Priority > sorted[j].Priority })
	out := StatusLayout{Omitted: len(sorted)}
	if width <= 0 {
		return out
	}
	x := 0
	included := 0
	for i, item := range sorted {
		reserve := 0
		if i+1 < len(sorted) {
			reserve = len(fmt.Sprintf(" +%d", len(sorted)-i-1))
		}
		separator := ""
		if included > 0 {
			separator = " | "
		}
		text := statusText(item)
		needed := uniseg.StringWidth(separator + text)
		if needed+reserve > width-x {
			if included > 0 {
				break
			}
			available := width - reserve
			if available <= 0 {
				available = width
			}
			if available == 1 && (item.Role == "warning" || item.Role == "error" || item.Role == "edited" || item.Role == "success" || item.Role == "info") {
				text = text[:1]
			} else {
				text = CellText(text, available)
			}
			separator = ""
		}
		if separator != "" {
			out.Runs = append(out.Runs, lineRun(separator, "hint", "", x))
			x += 3
		}
		role := item.Role
		if role == "" {
			role = "body"
		}
		run := lineRun(text, role, item.ID, x)
		out.Runs = append(out.Runs, run)
		x += run.Width
		included++
		if needed+reserve > width {
			break
		}
	}
	out.Omitted = len(sorted) - included
	if out.Omitted > 0 {
		marker := fmt.Sprintf(" +%d", out.Omitted)
		if x+len(marker) <= width {
			out.Runs = append(out.Runs, lineRun(marker, "hint", "", x))
		}
	}
	return out
}
