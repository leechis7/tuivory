package tuivory_test

import (
	"encoding/json"
	"os"
	"reflect"
	"testing"

	ui "github.com/leechis7/tuivory/go"
	tcell "github.com/leechis7/tuivory/go/terminal"
	tview "github.com/leechis7/tuivory/go/ui"
)

func TestLayerInputSharedGestures(t *testing.T) {
	data, err := os.ReadFile("testdata/layer-input-cases.json")
	if err != nil {
		t.Fatal(err)
	}
	var cases [][]any
	if err := json.Unmarshal(data, &cases); err != nil {
		t.Fatal(err)
	}
	var state ui.LayerInput
	for _, step := range cases {
		switch step[0] {
		case "front":
			got := state.SetFront(step[1].(string))
			var want []string
			if id := step[2].(string); id != "" {
				want = []string{id}
			}
			if !reflect.DeepEqual(got, want) {
				t.Fatalf("%v: %v", step, got)
			}
		case "invalidate":
			if got := state.Invalidate(); !reflect.DeepEqual(got, []string{step[1].(string)}) {
				t.Fatalf("%v: %v", step, got)
			}
		case "key":
			if got := state.KeyboardTarget(step[1].(string)); got != step[2] {
				t.Fatalf("%v: %v", step, got)
			}
		case "pointer":
			got := state.Pointer(step[1].(string), int(step[2].(float64)), step[3].(string), step[4].(bool))
			if got.Target != step[5] || got.Action != step[6] {
				t.Fatalf("%v: %+v", step, got)
			}
		}
	}
}

type layerInputProbe struct {
	*tview.Box
	mouse                 []tview.MouseAction
	keys, pastes, cancels int
	capture               bool
}

func (p *layerInputProbe) CancelPointer() { p.cancels++ }
func (p *layerInputProbe) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return func(a tview.MouseAction, _ *tcell.EventMouse, _ func(tview.Primitive)) (bool, tview.Primitive) {
		p.mouse = append(p.mouse, a)
		if p.capture && a == tview.MouseLeftDown {
			return false, p
		}
		return false, nil
	}
}
func (p *layerInputProbe) InputHandler() func(*tcell.EventKey, func(tview.Primitive)) {
	return func(*tcell.EventKey, func(tview.Primitive)) { p.keys++ }
}
func (p *layerInputProbe) PasteHandler() func(string, func(tview.Primitive)) {
	return func(string, func(tview.Primitive)) { p.pastes++ }
}
func TestFrontLayerViewConsumesRejectedAndCancelledInput(t *testing.T) {
	doc, _ := ui.CandidateTokens()
	tokens, _ := doc.Palette("dark", "256")
	p, _ := ui.Resolve(tokens)
	editor := &layerInputProbe{Box: tview.NewBox(), capture: true}
	tabs := &layerInputProbe{Box: tview.NewBox()}
	modal := &layerInputProbe{Box: tview.NewBox()}
	a := ui.ContainerChild{Item: ui.LayoutItem{ID: "editor"}, Child: editor}
	b := ui.ContainerChild{Item: ui.LayoutItem{ID: "tabs", Area: ui.CellRect{X: 2, Y: 2, Width: 10, Height: 5}}, Child: tabs}
	c := ui.ContainerChild{Item: ui.LayoutItem{ID: "modal", Area: ui.CellRect{X: 2, Y: 2, Width: 4, Height: 3}}, Child: modal}
	layers, err := ui.NewLayerStack([]ui.ContainerChild{a}, p)
	if err != nil {
		t.Fatal(err)
	}
	layers.SetRect(0, 0, 25, 14)
	layers.SetFrontInput(true, func(x, y int) bool { return x == 9 && y == 3 })
	screen := drawingScreen(t)
	focus := func(p tview.Primitive) { p.Focus(func(tview.Primitive) {}) }
	focus(layers)
	layers.Draw(screen)
	send := func(action tview.MouseAction, x, y int) tview.Primitive {
		t.Helper()
		used, capture := layers.MouseHandler()(action, tcell.NewEventMouse(x, y, 0, 0), focus)
		if !used {
			t.Fatal("layer let input escape", action)
		}
		return capture
	}
	if send(tview.MouseLeftDown, 4, 3) != layers {
		t.Fatal("root did not retain capture")
	}
	if err := layers.SetChildren([]ui.ContainerChild{a, b}); err != nil {
		t.Fatal(err)
	}
	layers.Draw(screen)
	send(tview.MouseMove, 4, 3)
	send(tview.MouseLeftUp, 4, 3)
	send(tview.MouseLeftClick, 4, 3)
	if editor.cancels != 1 || len(editor.mouse) != 1 || len(tabs.mouse) != 0 || !tabs.HasFocus() {
		t.Fatalf("scope change leaked input: editor=%+v tabs=%+v", editor, tabs)
	}
	send(tview.MouseScrollDown, 18, 3) // outside tabs, must not reach the editor
	send(tview.MouseLeftDown, 4, 3)
	send(tview.MouseLeftUp, 4, 3)
	send(tview.MouseLeftClick, 4, 3)
	if len(editor.mouse) != 1 || len(tabs.mouse) != 3 {
		t.Fatal("unhandled front input fell through")
	}
	send(tview.MouseLeftDown, 9, 3)
	send(tview.MouseLeftUp, 9, 3)
	send(tview.MouseLeftClick, 9, 3)
	layers.InputHandler()(tcell.NewEventKey(tcell.KeyEnter, 0, 0), focus)
	layers.PasteHandler()("한글", focus)
	if len(editor.mouse) != 4 || editor.HasFocus() || editor.pastes != 0 || editor.keys != 0 || tabs.keys != 1 || tabs.pastes != 1 {
		t.Fatal("pass-through did not stay pointer-only")
	}
	if err := layers.SetChildren([]ui.ContainerChild{a, b, c}); err != nil {
		t.Fatal(err)
	}
	layers.Draw(screen)
	modal.Blur()
	layers.PasteHandler()("ignore", focus)
	if modal.pastes != 0 || tabs.pastes != 1 {
		t.Fatal("paste with no front focus leaked")
	}
	if err := layers.SetChildren([]ui.ContainerChild{a, b}); err != nil {
		t.Fatal(err)
	}
	if !tabs.HasFocus() {
		t.Fatal("closing nested layer did not restore tabs")
	}
	if err := layers.SetChildren([]ui.ContainerChild{a}); err != nil {
		t.Fatal(err)
	}
	if !editor.HasFocus() {
		t.Fatal("closing tabs did not restore editor")
	}
}
