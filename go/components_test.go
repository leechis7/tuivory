package tuivory_test

import (
	"encoding/json"
	tcell "github.com/leechis7/tuivory/go/terminal"
	ui "github.com/leechis7/tuivory/go"
	tview "github.com/leechis7/tuivory/go/ui"
	"github.com/rivo/uniseg"
	"os"
	"reflect"
	"strings"
	"testing"
)

func TestWorkspaceContract(t *testing.T) {
	data, e := os.ReadFile("testdata/components-cases.json")
	if e != nil {
		t.Fatal(e)
	}
	var f struct {
		Tabs struct {
			Items   []ui.TabItem
			Steps   []struct{ Action, Active, Focused, Event, ID string }
			Layouts []struct {
				Width, First int
				IDs          []string
			}
		}
		Paths []struct {
			Width int
			Text  string
		}
		Status []struct {
			Width   int
			Text    string
			Omitted int
		}
	}
	if e = json.Unmarshal(data, &f); e != nil {
		t.Fatal(e)
	}
	tabs, e := ui.NewTabs(f.Tabs.Items)
	if e != nil {
		t.Fatal(e)
	}
	state := &ui.TabState{}
	actions := map[string]ui.TabAction{"next": ui.TabNext, "previous": ui.TabPrevious, "first": ui.TabFirst, "last": ui.TabLast, "activate": ui.TabActivate, "close": ui.TabClose}
	for _, step := range f.Tabs.Steps {
		event := tabs.Handle(state, actions[step.Action])
		if event.Kind != step.Event || event.ID != step.ID || state.Active != step.Active || state.Focused != step.Focused {
			t.Fatal(step, state, event)
		}
	}
	for _, test := range f.Tabs.Layouts {
		state := &ui.TabState{Active: "a", Focused: "c"}
		layout := tabs.Layout(state, test.Width)
		ids := []string{}
		for _, cell := range layout.Cells {
			ids = append(ids, cell.ID)
			if cell.Start+cell.Width > test.Width || uniseg.StringWidth(cell.Text) > cell.Width {
				t.Fatal(cell)
			}
		}
		if state.First != test.First || !reflect.DeepEqual(ids, test.IDs) {
			t.Fatal(test, state, ids)
		}
	}
	path := []ui.PathItem{{ID: "r", Label: "root"}, {ID: "f", Label: "folder"}, {ID: "c", Label: "현재.sql"}}
	for _, test := range f.Paths {
		runs := ui.Breadcrumbs(path, test.Width)
		text := ""
		for _, run := range runs {
			text += run.Text
			if run.Start+run.Width > test.Width {
				t.Fatal(run)
			}
		}
		if text != test.Text {
			t.Fatal(test, text)
		}
	}
	items := []ui.StatusItem{{ID: "help", Text: "F1 Help", Role: "hint", Priority: 1}, {ID: "err", Text: "Failure", Role: "error", Priority: 100}, {ID: "draft", Text: "Draft", Role: "edited", Priority: 30}}
	for _, test := range f.Status {
		layout := ui.StatusLine(items, test.Width)
		text := ""
		for _, run := range layout.Runs {
			text += run.Text
			if run.Start+run.Width > test.Width {
				t.Fatal(run)
			}
		}
		if text != test.Text || layout.Omitted != test.Omitted {
			t.Fatal(test, text, layout.Omitted)
		}
	}
}
func TestTabsRequestsReplacementAndSplitPreservation(t *testing.T) {
	if _, e := ui.NewTabs([]ui.TabItem{{ID: "a"}, {ID: "a"}}); e == nil {
		t.Fatal("duplicate IDs accepted")
	}
	tabs, _ := ui.NewTabs([]ui.TabItem{{ID: "a", Title: "Long 한글 document", Edited: true, Closable: true}, {ID: "d", Disabled: true}})
	state := &ui.TabState{}
	layout := tabs.Layout(state, 24)
	cell := layout.Cells[0]
	before := *state
	event := tabs.Click(state, cell.Start+uniseg.StringWidth(cell.Text)-2, 24)
	if event.Kind != "close" || *state != before || !strings.Contains(cell.Text, "* x") {
		t.Fatal(event, state, cell)
	}
	empty, _ := ui.NewTabs(nil)
	empty.Reconcile(state)
	if state.Active != "" || state.Focused != "" {
		t.Fatal(state)
	}
	spec := ui.SplitSpec{FirstMin: 10, SecondMin: 15}
	s := &ui.SplitState{Preferred: 20}
	if l := spec.Layout(s, 60); l.First != 20 || l.Second != 39 {
		t.Fatal(l)
	}
	if l := spec.Layout(s, 20); !l.Compact || s.Preferred != 20 {
		t.Fatal(l, s)
	}
	if l := spec.Layout(s, 60); l.First != 20 {
		t.Fatal(l)
	}
	spec.Resize(s, 60, 99)
	if s.Preferred != 44 {
		t.Fatal(s)
	}
	if l := spec.Layout(s, 40); l.First != 24 || s.Preferred != 44 {
		t.Fatal(l, s)
	}
	for total := 0; total < 100; total++ {
		l := spec.Layout(s, total)
		if l.First+l.Second+l.Divider != total {
			t.Fatal(l)
		}
	}
}
func TestWorkspaceViewsAllPalettesAndResizeEvents(t *testing.T) {
	screen := tcell.NewSimulationScreen("UTF-8")
	if e := screen.Init(); e != nil {
		t.Fatal(e)
	}
	defer screen.Fini()
	screen.SetSize(80, 20)
	doc, _ := ui.CandidateTokens()
	tabs, _ := ui.NewTabs([]ui.TabItem{{ID: "a", Title: "Overview"}, {ID: "b", Title: "한글", Closable: true, Edited: true}})
	state := &ui.TabState{Active: "a", Focused: "b"}
	splitState := &ui.SplitState{Preferred: 20}
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			raw, _ := doc.Palette(theme, profile)
			p, _ := ui.Resolve(raw)
			view, e := ui.NewTabView(tabs, state, p)
			if e != nil {
				t.Fatal(e)
			}
			view.SetRect(0, 0, 60, 1)
			view.Focus(func(tview.Primitive) {})
			before := *state
			view.Draw(screen)
			if state.Active != before.Active || state.Focused != before.Focused {
				t.Fatal(state)
			}
			layout := tabs.Layout(state, 60)
			cell := layout.Cells[1]
			_, _, style, _ := screen.GetContent(cell.Start, 0)
			_, _, attrs := style.Decompose()
			if attrs&tcell.AttrUnderline == 0 {
				t.Fatal("focus cue missing")
			}
			panel, _ := ui.NewPanelView(view, p)
			panel.SetTitle("[red] Literal")
			panel.ASCII = true
			panel.SetRect(0, 2, 35, 7)
			panel.Draw(screen)
			r, _, _, _ := screen.GetContent(0, 2)
			if r != '+' {
				t.Fatal(r)
			}
			right := tview.NewTextView().SetText("Right")
			split, _ := ui.NewSplitView(panel, right, splitState, ui.SplitSpec{FirstMin: 10, SecondMin: 10}, p)
			split.SetRect(0, 0, 60, 15)
			split.Draw(screen)
			if !split.ResizeKey(tcell.NewEventKey(tcell.KeyRight, 0, tcell.ModCtrl)) || splitState.Preferred != 21 {
				t.Fatal(splitState)
			}
			splitState.Preferred = 20
			handler := split.MouseHandler()
			handler(tview.MouseLeftDown, tcell.NewEventMouse(20, 5, tcell.Button1, 0), func(tview.Primitive) {})
			handler(tview.MouseMove, tcell.NewEventMouse(25, 5, tcell.Button1, 0), func(tview.Primitive) {})
			handler(tview.MouseLeftUp, tcell.NewEventMouse(25, 5, 0, 0), func(tview.Primitive) {})
			if splitState.Preferred != 25 {
				t.Fatal(splitState)
			}
			splitState.Preferred = 20
			split.SetRect(0, 0, 8, 5)
			split.ActiveSecond = true
			split.Draw(screen)
			if splitState.Preferred != 20 {
				t.Fatal(splitState)
			}
			crumbs, _ := ui.NewBreadcrumbView([]ui.PathItem{{ID: "r", Label: "root"}, {ID: "last", Label: "현재.sql"}}, p)
			crumbs.SetRect(0, 16, 12, 1)
			crumbs.Draw(screen)
			hit := ""
			crumbs.OnNavigate = func(id string) { hit = id }
			crumbs.MouseHandler()(tview.MouseLeftClick, tcell.NewEventMouse(10, 16, 0, 0), func(tview.Primitive) {})
			if hit != "last" {
				t.Fatal(hit)
			}
			status, _ := ui.NewStatusView([]ui.StatusItem{{ID: "e", Text: "Failure", Role: "error", Priority: 9}}, p)
			status.SetRect(0, 18, 30, 1)
			status.Draw(screen)
			_, _, st, _ := screen.GetContent(0, 18)
			fg, bg, _ := st.Decompose()
			if fg != p["error"].FG || bg != p["surface"].BG {
				t.Fatal(st)
			}
			for _, v := range []tview.Primitive{view, panel, split, crumbs, status} {
				v.SetRect(0, 0, 0, 0)
				v.Draw(screen)
			}
		}
	}
}
