package tuivory_test

import (
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/uniseg"
	"strings"
	"testing"
)

func TestNoticeLifetimePriorityAndRequests(t *testing.T) {
	q, _ := ui.NewNoticeQueue(3)
	_ = q.Push(ui.Notice{ID: "info", Text: "Transient", Severity: "info", ExpiresAt: 5})
	_ = q.Push(ui.Notice{ID: "error", Text: "Important", Severity: "error", ExpiresAt: 1, Actions: []ui.NoticeAction{{ID: "disabled", Disabled: true}, {ID: "retry", Label: "Retry"}}})
	if len(q.Visible(100)) != 1 || q.Visible(100)[0].ID != "error" {
		t.Fatal("error auto expired")
	}
	rows := q.Layout(20, 1, 0)
	if len(rows) != 1 || rows[0].Role != "error" {
		t.Fatal("critical hidden")
	}
	if e := q.Handle("activate", 100, 2); e.Kind != "action" || e.Action != "retry" {
		t.Fatal(e)
	}
	if q.Handle("dismiss", 100, 2).Kind != "dismiss" || len(q.Visible(100)) != 1 {
		t.Fatal("request mutated queue")
	}
	if len(q.Expire(100)) != 1 {
		t.Fatal("host clock")
	}
	q.Dismiss("error")
	if len(q.Visible(100)) != 0 {
		t.Fatal("explicit dismiss")
	}
	full, _ := ui.NewNoticeQueue(1)
	_ = full.Push(ui.Notice{ID: "a", Severity: "error"})
	if full.Push(ui.Notice{ID: "b", Severity: "error"}) == nil || full.Visible(0)[0].ID != "a" {
		t.Fatal("pinned eviction")
	}
}
func TestProgressAndDataState(t *testing.T) {
	p := ui.Progress{ID: "p", Status: "loading", Cancellable: true, Current: 200, Total: 100}
	if p.RequestCancel().Kind != "cancel" || p.Status != "loading" {
		t.Fatal("cancel must be request")
	}
	if !strings.Contains(p.Layout(40, 0)[1].Text, "100%") {
		t.Fatal("percentage clamp")
	}
	p.Total = 0
	if p.Layout(40, 0)[1].Text == p.Layout(40, 1)[1].Text {
		t.Fatal("host frame not used")
	}
	p.Status = "success"
	if p.RequestCancel().Kind != "" {
		t.Fatal("cancel completed")
	}
	for _, line := range p.Layout(3, 0) {
		if uniseg.StringWidth(line.Text) > 3 {
			t.Fatal("clip")
		}
	}
	if (ui.DataState{Kind: "error", Text: "failure"}).Layout(20)[0].Role != "error" {
		t.Fatal("error state")
	}
}
