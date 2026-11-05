package tuivory_test

import (
	ui "github.com/leechis7/tuivory/go"
	"testing"
)

func TestPasteSafeScreenOnlyNormalizesBracketedLines(t *testing.T) {
	base := ui.NewSimulationScreen("UTF-8")
	base.Init()
	defer base.Fini()
	s := ui.PasteSafeScreen(base)
	if ui.PasteSafeScreen(s) != s || ui.PasteSafeScreen(nil) != nil {
		t.Fatal("wrapper identity")
	}
	events := []ui.Event{ui.NewEventKey(ui.KeyCtrlJ, 0, 0), ui.NewEventPaste(true), ui.NewEventKey(ui.KeyCtrlJ, 0, 0), ui.NewEventKey(ui.KeyEnter, 0, 0), ui.NewEventKey(ui.KeyCtrlJ, 0, 0), ui.NewEventKey(ui.KeyRune, 'x', 0), ui.NewEventPaste(false), ui.NewEventKey(ui.KeyCtrlJ, 0, 0)}
	for _, e := range events {
		if err := base.PostEvent(e); err != nil {
			t.Fatal(err)
		}
	}
	if s.PollEvent().(*ui.EventKey).Key() != ui.KeyCtrlJ {
		t.Fatal("outside paste")
	}
	if !s.PollEvent().(*ui.EventPaste).Start() {
		t.Fatal("start")
	}
	for i := 0; i < 2; i++ {
		if s.PollEvent().(*ui.EventKey).Key() != ui.KeyEnter {
			t.Fatal("LF/CR")
		}
	}
	if s.PollEvent().(*ui.EventKey).Rune() != 'x' {
		t.Fatal("CRLF double counted")
	}
	if s.PollEvent().(*ui.EventPaste).Start() {
		t.Fatal("end")
	}
	if s.PollEvent().(*ui.EventKey).Key() != ui.KeyCtrlJ {
		t.Fatal("outside after end")
	}
}
