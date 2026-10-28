package tuivory

import (
	"fmt"
	"sort"
	"strings"
)

type NoticeAction struct {
	ID, Label string
	Disabled  bool
}
type Notice struct {
	ID, Text, Detail, Severity string
	Priority                   int
	Persistent                 bool
	ExpiresAt                  uint64
	Actions                    []NoticeAction
}
type NoticeEvent struct{ Kind, ID, Action string }
type NoticeQueue struct {
	items    []Notice
	capacity int
	Focused  string
}

func severity(s string) int {
	switch s {
	case "error":
		return 3
	case "warning":
		return 2
	case "success":
		return 1
	case "info":
		return 0
	}
	return -1
}
func pinned(n Notice) bool              { return n.Persistent || n.Severity == "error" || len(n.Actions) > 0 }
func expired(n Notice, now uint64) bool { return !pinned(n) && n.ExpiresAt > 0 && now >= n.ExpiresAt }
func NewNoticeQueue(capacity int) (*NoticeQueue, error) {
	if capacity <= 0 {
		return nil, fmt.Errorf("positive notice capacity required")
	}
	return &NoticeQueue{capacity: capacity}, nil
}
func (q *NoticeQueue) Push(n Notice) error {
	if n.ID == "" || severity(n.Severity) < 0 {
		return fmt.Errorf("invalid notice ID or severity")
	}
	seen := map[string]bool{}
	for _, a := range n.Actions {
		if a.ID == "" || seen[a.ID] {
			return fmt.Errorf("invalid notice action")
		}
		seen[a.ID] = true
	}
	n.Actions = append([]NoticeAction(nil), n.Actions...)
	for i, old := range q.items {
		if old.ID == n.ID {
			q.items[i] = n
			return nil
		}
	}
	if len(q.items) >= q.capacity {
		candidate := -1
		for i, old := range q.items {
			if pinned(old) {
				continue
			}
			if candidate < 0 || severity(old.Severity) < severity(q.items[candidate].Severity) || severity(old.Severity) == severity(q.items[candidate].Severity) && old.Priority < q.items[candidate].Priority {
				candidate = i
			}
		}
		if candidate < 0 || (severity(q.items[candidate].Severity) > severity(n.Severity) || severity(q.items[candidate].Severity) == severity(n.Severity) && q.items[candidate].Priority > n.Priority) {
			return fmt.Errorf("notice queue full; important notices retained")
		}
		q.items = append(q.items[:candidate], q.items[candidate+1:]...)
	}
	q.items = append(q.items, n)
	if q.Focused == "" || n.Severity == "error" {
		q.Focused = n.ID
	}
	return nil
}
func (q *NoticeQueue) Visible(now uint64) []Notice {
	out := []Notice{}
	for _, n := range q.items {
		if !expired(n, now) {
			copy := n
			copy.Actions = append([]NoticeAction(nil), n.Actions...)
			out = append(out, copy)
		}
	}
	sort.SliceStable(out, func(i, j int) bool {
		a, b := severity(out[i].Severity), severity(out[j].Severity)
		if a != b {
			return a > b
		}
		return out[i].Priority > out[j].Priority
	})
	return out
}
func (q *NoticeQueue) Dismiss(id string) bool {
	for i, n := range q.items {
		if n.ID == id {
			q.items = append(q.items[:i], q.items[i+1:]...)
			if q.Focused == id {
				q.Focused = ""
			}
			return true
		}
	}
	return false
}
func (q *NoticeQueue) Expire(now uint64) []NoticeEvent {
	out := []NoticeEvent{}
	keep := q.items[:0]
	for _, n := range q.items {
		if expired(n, now) {
			out = append(out, NoticeEvent{Kind: "expired", ID: n.ID})
		} else {
			keep = append(keep, n)
		}
	}
	q.items = keep
	return out
}
func (q *NoticeQueue) Handle(action string, now uint64, height int) NoticeEvent {
	items := q.Visible(now)
	limit := max(0, height)
	if len(items) > limit {
		if height > 0 {
			limit = max(1, limit-1)
		}
	}
	items = items[:min(len(items), limit)]
	if len(items) == 0 {
		return NoticeEvent{}
	}
	at := 0
	for i, n := range items {
		if n.ID == q.Focused {
			at = i
		}
	}
	if action == "next" {
		at = min(len(items)-1, at+1)
	}
	if action == "previous" {
		at = max(0, at-1)
	}
	q.Focused = items[at].ID
	n := items[at]
	if action == "dismiss" {
		return NoticeEvent{Kind: "dismiss", ID: n.ID}
	}
	if action == "activate" {
		for _, a := range n.Actions {
			if !a.Disabled {
				return NoticeEvent{Kind: "action", ID: n.ID, Action: a.ID}
			}
		}
	}
	return NoticeEvent{}
}
func (q *NoticeQueue) Layout(width, height int, now uint64) []ComponentLine {
	items := q.Visible(now)
	limit := max(0, height)
	if len(items) > limit {
		if height > 0 {
			limit = max(1, limit-1)
		}
	}
	out := []ComponentLine{}
	for _, n := range items[:min(len(items), limit)] {
		mark := map[string]string{"error": "[!]", "warning": "[?]", "success": "[+]", "info": "[i]"}[n.Severity]
		prefix := "  "
		if q.Focused == n.ID {
			prefix = "> "
		}
		value := prefix + mark + " " + n.Text
		if n.Detail != "" {
			value += " / " + n.Detail
		}
		for _, a := range n.Actions {
			value += " [" + a.Label + "]"
		}
		out = append(out, ComponentLine{ID: n.ID, Text: CellText(value, width), Role: n.Severity, Focused: n.ID == q.Focused})
	}
	if len(items) > limit && height > len(out) {
		out = append(out, ComponentLine{Text: CellText(fmt.Sprintf("+%d", len(items)-limit), width), Role: "hint"})
	}
	return out
}

type Progress struct {
	ID, Label, Status, Message, CancelLabel string
	Current, Total                          uint64
	Cancellable                             bool
}

func (p Progress) RequestCancel() NoticeEvent {
	if p.ID != "" && p.Cancellable && (p.Status == "" || p.Status == "loading") {
		return NoticeEvent{Kind: "cancel", ID: p.ID}
	}
	return NoticeEvent{}
}
func (p Progress) Layout(width int, frame uint64) []ComponentLine {
	status := p.Status
	if status == "" {
		status = "loading"
	}
	role := "info"
	if status != "loading" && status != "ready" && status != "success" && status != "empty" && status != "cancelled" {
		role = "error"
	}
	if status == "ready" {
		role = "body"
	}
	if status == "error" {
		role = "error"
	} else if status == "success" {
		role = "success"
	} else if status == "empty" || status == "cancelled" {
		role = "hint"
	}
	value := status
	if status == "loading" {
		if p.Total == 0 {
			value = string([]rune{'|', '/', '-', '\\'}[frame%4])
		} else {
			ratio := float64(min(p.Current, p.Total)) / float64(p.Total)
			size := max(0, min(30, width-10))
			done := int(ratio * float64(size))
			value = fmt.Sprintf("[%s%s] %d%%", strings.Repeat("#", done), strings.Repeat("-", size-done), int(ratio*100))
		}
	}
	if p.Message != "" {
		value += " " + p.Message
	}
	out := []ComponentLine{{ID: p.ID, Text: CellText(p.Label, width), Role: role}, {ID: p.ID, Text: CellText(value, width), Role: role}}
	if p.RequestCancel().Kind != "" && p.CancelLabel != "" {
		out = append(out, ComponentLine{ID: p.ID, Text: CellText(p.CancelLabel, width), Role: "hint"})
	}
	return out
}

// DataState is a reusable loading/empty/error/ready view without fetching data.
type DataState struct{ Kind, Text, Detail string }

func (s DataState) Layout(width int) []ComponentLine {
	role := "body"
	switch s.Kind {
	case "error":
		role = "error"
	case "loading":
		role = "info"
	case "empty":
		role = "hint"
	case "ready":
	default:
		role = "error"
	}
	return []ComponentLine{{Text: CellText(s.Text, width), Role: role}, {Text: CellText(s.Detail, width), Role: "hint"}}
}
