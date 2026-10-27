package tuivory_test

import (
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"sort"
	"strings"
	"testing"

	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
)

func TestSharedTreeNavigationContract(t *testing.T) {
	data, err := os.ReadFile("testdata/tree-navigation.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Height int
		Nodes  []struct {
			ID, Parent, Name, Secondary, Icon string
			ASCIIIcon                         string `json:"ascii_icon"`
			Count                             *uint64
			Branch                            bool
		}
		Steps []struct {
			Action, Selected, Event, ID     string
			Expanded, Visible               []string
			Scroll, Horizontal, Column, Row int
		}
	}
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	nodes := []ui.TreeNode{}
	for _, n := range fixture.Nodes {
		nodes = append(nodes, ui.TreeNode{ID: n.ID, Parent: n.Parent, Name: n.Name, Secondary: n.Secondary, Icon: n.Icon, ASCIIIcon: n.ASCIIIcon, Count: n.Count, Branch: n.Branch})
	}
	tree, err := ui.NewTree(nodes)
	if err != nil {
		t.Fatal(err)
	}
	state := &ui.TreeState{}
	actions := map[string]ui.TreeAction{"right": ui.TreeRight, "left": ui.TreeLeft, "down": ui.TreeDown, "home": ui.TreeHome, "end": ui.TreeEnd, "pan_right": ui.TreePanRight, "activate": ui.TreeActivate, "toggle": ui.TreeToggle}
	for i, step := range fixture.Steps {
		var event ui.TreeEvent
		if step.Action == "click" {
			event = tree.Click(state, step.Column, step.Row, fixture.Height)
		} else {
			event = tree.Handle(state, actions[step.Action], fixture.Height)
		}
		expanded := []string{}
		for id, open := range state.Expanded {
			if open {
				expanded = append(expanded, id)
			}
		}
		sort.Strings(expanded)
		visible := []string{}
		for _, row := range tree.Visible(state) {
			visible = append(visible, row.Node.ID)
		}
		if event.Kind != step.Event || event.ID != step.ID || state.Selected != step.Selected || state.Scroll != step.Scroll || state.Horizontal != step.Horizontal || !reflect.DeepEqual(expanded, step.Expanded) || !reflect.DeepEqual(visible, step.Visible) {
			t.Fatalf("step %d %s: state=%+v event=%+v expanded=%v visible=%v", i, step.Action, state, event, expanded, visible)
		}
	}
}

func TestTreeRejectsInvalidDataAndReconcilesStableIDs(t *testing.T) {
	for _, nodes := range [][]ui.TreeNode{{{ID: ""}}, {{ID: "a"}, {ID: "a"}}, {{ID: "a", Parent: "missing"}}, {{ID: "a", Parent: "a"}}} {
		if _, err := ui.NewTree(nodes); err == nil {
			t.Fatal("accepted invalid tree", nodes)
		}
	}
	tree, _ := ui.NewTree([]ui.TreeNode{{ID: "r"}, {ID: "a", Parent: "r"}, {ID: "b", Parent: "a"}})
	state := &ui.TreeState{Selected: "b", Expanded: map[string]bool{"r": true, "removed": true}, Scroll: 99}
	tree.Reconcile(state, 2)
	if state.Selected != "a" || state.Scroll != 0 || state.Expanded["removed"] {
		t.Fatal(state)
	}
	replacement, _ := ui.NewTree([]ui.TreeNode{{ID: "r", Name: "Renamed"}})
	replacement.Reconcile(state, 1)
	if state.Selected != "r" || !state.Expanded["r"] {
		t.Fatal(state)
	}
	empty, _ := ui.NewTree(nil)
	empty.Reconcile(state, 0)
	if state.Selected != "" || state.Scroll != 0 {
		t.Fatal(state)
	}
	var deep []ui.TreeNode
	for i := 0; i <= 129; i++ {
		parent := ""
		if i > 0 {
			parent = fmt.Sprint(i - 1)
		}
		deep = append(deep, ui.TreeNode{ID: fmt.Sprint(i), Parent: parent})
		_, err := ui.NewTree(deep)
		if (i <= 128 && err != nil) || (i == 129 && err == nil) {
			t.Fatal("depth boundary", i, err)
		}
	}
}

func TestTreeTwelvePalettesFocusLiteralTextAndWideClipping(t *testing.T) {
	tree, _ := ui.NewTree([]ui.TreeNode{{ID: "r", Name: "[red]한글 ABC", Icon: "◇", ASCIIIcon: "R", Secondary: "secondary"}})
	state := &ui.TreeState{Selected: "r"}
	doc, _ := ui.CandidateTokens()
	screen := tcell.NewSimulationScreen("UTF-8")
	if err := screen.Init(); err != nil {
		t.Fatal(err)
	}
	defer screen.Fini()
	screen.SetSize(40, 8)
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			raw, _ := doc.Palette(theme, profile)
			palette, _ := ui.Resolve(raw)
			view, err := ui.NewTreeView(tree, state, palette)
			if err != nil {
				t.Fatal(err)
			}
			view.SetRect(0, 0, 38, 7)
			before := *state
			view.Draw(screen)
			_, _, unfocused, _ := screen.GetContent(3, 1)
			view.Focus(func(tview.Primitive) {})
			view.Draw(screen)
			_, _, focused, _ := screen.GetContent(3, 1)
			fg, bg, attrs := focused.Decompose()
			_, _, plain := unfocused.Decompose()
			if fg != palette["selection"].FG || bg != palette["selection"].BG || attrs&tcell.AttrUnderline == 0 || plain&tcell.AttrUnderline != 0 || state.Selected != before.Selected || state.Scroll != before.Scroll || state.Horizontal != before.Horizontal {
				t.Fatal(theme, profile, state)
			}
		}
	}
	raw, _ := doc.Palette("dark", "truecolor")
	palette, _ := ui.Resolve(raw)
	view, _ := ui.NewTreeView(tree, state, palette)
	view.SetRect(0, 0, 38, 7)
	view.ASCII = true
	view.Draw(screen)
	var text strings.Builder
	for x := 0; x < 38; x++ {
		r, _, _, _ := screen.GetContent(x, 1)
		text.WriteRune(r)
	}
	if !strings.Contains(text.String(), "[red]") || strings.Contains(text.String(), "◇") {
		t.Fatal(text.String())
	}
	for offset := 0; offset < 30; offset++ {
		state.Horizontal = offset
		view.SetRect(0, 0, 8, 4)
		view.Draw(screen)
	}
	if err := view.SetPalette(ui.Palette{}); err == nil {
		t.Fatal("missing roles accepted")
	}
	view.SetRect(0, 0, 0, 0)
	view.Draw(screen)
}
