package tuivory_test

import (
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/uniseg"
	"strings"
	"testing"
)

func TestListAndPicker(t *testing.T) {
	items := []ui.ListItem{{ID: "g", Separator: true}, {ID: "go", Label: "Go", Secondary: "module"}, {ID: "x", Label: "disabled", Disabled: true}, {ID: "rust", Label: "Rust", Secondary: "crate"}}
	m, _ := ui.NewList(items)
	if m.Focused != "go" {
		t.Fatal(m.Focused)
	}
	m.Handle("next", 3)
	if m.Focused != "rust" || m.Selected != "" {
		t.Fatal("focus != selection")
	}
	m.Handle("select", 3)
	m.SetQuery("GO")
	if m.Focused != "go" || m.Selected != "rust" {
		t.Fatal("filtered selection")
	}
	if m.SetItems([]ui.ListItem{{ID: "a"}, {ID: "a"}}) == nil || m.Focused != "go" {
		t.Fatal("atomic invalid update")
	}
	p, _ := ui.NewSearchPicker(items)
	p.Handle("open", "", 4)
	p.Handle("insert", "Rust", 4)
	if p.Value != "" || p.List.Focused != "rust" {
		t.Fatal("pending")
	}
	if p.Handle("activate", "", 4).Kind != "change" || p.Value != "rust" || p.Open {
		t.Fatal("commit")
	}
	p.Handle("open", "", 4)
	p.Handle("insert", "Go", 4)
	p.Handle("cancel", "", 4)
	if p.Value != "rust" {
		t.Fatal("cancel changed value")
	}
	p.Handle("open", "", 4)
	p.Handle("insert", strings.Repeat("한", 40), 4)
	rows := p.Layout(12, 4, true)
	if !strings.Contains(rows[0].Text, "|") {
		t.Fatal("query caret")
	}
	for _, r := range rows {
		if uniseg.StringWidth(r.Text) > 12 {
			t.Fatal("wide clip")
		}
	}
	if p.Click("x").Kind != "" {
		t.Fatal("disabled click")
	}
}
