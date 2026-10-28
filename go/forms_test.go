package tuivory_test

import (
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/uniseg"
	"strings"
	"testing"
)

func TestFormEditingAndRequests(t *testing.T) {
	f, e := ui.NewForm([]ui.FormField{{ID: "text", Kind: "text", Required: true}, {ID: "read", Kind: "text", Value: "keep", State: ui.ControlState{ReadOnly: true}}, {ID: "check", Kind: "checkbox", Required: true}, {ID: "submit", Kind: "button", Action: "submit"}})
	if e != nil {
		t.Fatal(e)
	}
	if f.Handle("submit", "").Kind != "invalid" {
		t.Fatal("required")
	}
	f.Handle("insert", "가👩‍💻é")
	f.Handle("backspace", "")
	if f.Fields()[0].Value != "가👩‍💻" {
		t.Fatal("grapheme delete", f.Fields()[0].Value)
	}
	f.Handle("left", "")
	f.Handle("delete", "")
	if f.Fields()[0].Value != "가" {
		t.Fatal("cursor delete")
	}
	f.Handle("next", "")
	f.Handle("insert", "bad")
	if f.Fields()[1].Value != "keep" {
		t.Fatal("read-only")
	}
	f.Focus("check")
	f.Handle("toggle", "")
	f.Focus("submit")
	if f.Handle("activate", "").Kind != "submit" {
		t.Fatal("submission request")
	}
	f.SetFeedback("text", "", "host error")
	if f.Handle("submit", "").Kind != "invalid" {
		t.Fatal("host validation")
	}
	f.SetState("text", ui.ControlState{Disabled: true})
	if f.Handle("submit", "").Kind != "submit" {
		t.Fatal("disabled excluded")
	}
}
func TestFormSelectAndViewport(t *testing.T) {
	f, _ := ui.NewForm([]ui.FormField{{ID: "select", Kind: "select", Choice: "a", Options: []ui.FormOption{{ID: "a", Label: "A"}, {ID: "x", Disabled: true}, {ID: "b", Label: "B"}}}, {ID: "long", Kind: "text", Value: strings.Repeat("한", 30)}})
	f.Handle("activate", "")
	f.Handle("down", "")
	if f.Fields()[0].Choice != "a" || f.Fields()[0].Pending != "b" {
		t.Fatal("pending selection")
	}
	f.Handle("cancel", "")
	if f.Fields()[0].Choice != "a" {
		t.Fatal("cancel")
	}
	f.Handle("activate", "")
	f.Handle("down", "")
	f.Handle("activate", "")
	if f.Fields()[0].Choice != "b" {
		t.Fatal("confirm")
	}
	f.SetState("select", ui.ControlState{ReadOnly: true})
	f.Click("select", "a")
	if f.Fields()[0].Choice != "b" {
		t.Fatal("read-only click")
	}
	f.Focus("long")
	seen := false
	for _, line := range f.Layout(12, 4) {
		if uniseg.StringWidth(line.Text) > 12 {
			t.Fatal("overflow")
		}
		seen = seen || strings.Contains(line.Text, "|")
	}
	if !seen {
		t.Fatal("caret must remain visible")
	}
	if _, e := ui.NewForm([]ui.FormField{{ID: "a", Kind: "unknown"}}); e == nil {
		t.Fatal("kind")
	}
}
