package tuivory_test

import (
	"encoding/json"
	ui "github.com/leechis7/tuivory/go"
	tcell "github.com/leechis7/tuivory/go/terminal"
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
			view.SetRect(0, 0, 60, 3)
			view.Draw(screen)
			screen.Show()
			active := layout.Cells[0]
			frame, stride, _ := screen.GetContents()
			for _, point := range []struct {
				x, y int
				want rune
			}{
				{active.Start, 0, '┌'}, {active.Start, 1, '│'}, {active.Start + 1, 2, ' '},
				{cell.Start, 0, '┌'}, {cell.Start, 2, '─'},
			} {
				got := frame[point.y*stride+point.x].Runes
				if len(got) != 1 || got[0] != point.want {
					t.Fatalf("%s/%s: (%d,%d) %q want %q", theme, profile, point.x, point.y, got, point.want)
				}
			}
			closeCol := cell.Start + uniseg.StringWidth(cell.Text) - 2
			event := tabs.Click(state, closeCol, 60)
			if event.Kind != "close" || event.ID != cell.ID || state.Active != before.Active {
				t.Fatal(event, state)
			}
			view.SetRect(0, 0, 60, 1)
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

type splitInputPane struct {
	*tview.Box
	hovered, keys int
	paste         string
}

func (p *splitInputPane) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return func(action tview.MouseAction, _ *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		if action == tview.MouseMove {
			p.hovered++
			focus(p) // A passive hover must not transfer focus.
		}
		if action == tview.MouseLeftClick {
			focus(p)
		}
		return true, nil
	}
}
func (p *splitInputPane) InputHandler() func(*tcell.EventKey, func(tview.Primitive)) {
	return func(*tcell.EventKey, func(tview.Primitive)) { p.keys++ }
}
func (p *splitInputPane) PasteHandler() func(string, func(tview.Primitive)) {
	return func(text string, _ func(tview.Primitive)) { p.paste += text }
}

func TestSplitKeyboardAndPasteFollowFocusAcrossPointerMovement(t *testing.T) {
	doc, _ := ui.CandidateTokens()
	tokens, _ := doc.Palette("dark", "256")
	p, _ := ui.Resolve(tokens)
	left, right := &splitInputPane{Box: tview.NewBox()}, &splitInputPane{Box: tview.NewBox()}
	split, err := ui.NewSplitView(left, right, &ui.SplitState{Preferred: 20}, ui.SplitSpec{FirstMin: 5, SecondMin: 5}, p)
	if err != nil {
		t.Fatal(err)
	}
	split.SetRect(0, 0, 50, 12)
	focus := func(p tview.Primitive) { left.Blur(); right.Blur(); p.Focus(func(tview.Primitive) {}) }
	key := tcell.NewEventKey(tcell.KeyEnter, 0, 0)
	mouse := tcell.NewEventMouse(4, 4, 0, 0)
	focus(right)
	split.MouseHandler()(tview.MouseMove, mouse, focus)
	split.InputHandler()(key, focus)
	split.PasteHandler()("한글", focus)
	if left.hovered != 1 || left.keys != 0 || left.paste != "" || right.keys != 1 || right.paste != "한글" {
		t.Fatalf("hover changed keyboard routing: left=%+v right=%+v", left, right)
	}
	split.MouseHandler()(tview.MouseLeftClick, mouse, focus)
	split.InputHandler()(key, focus)
	if left.keys != 1 || right.keys != 1 {
		t.Fatal("click did not move focus")
	}
	left.Blur()
	split.InputHandler()(key, focus)
	split.PasteHandler()("discard", focus)
	if left.keys != 1 || right.keys != 1 || left.paste != "" || right.paste != "한글" {
		t.Fatal("keyboard input went to a pane without actual focus")
	}
}

func TestTabTitleRowReceivesClicksInCompactAndOutlinedLayouts(t *testing.T) {
	screen := drawingScreen(t)
	screen.SetSize(80, 10)
	doc, _ := ui.CandidateTokens()
	raw, _ := doc.Palette("dark", "256")
	palette, _ := ui.Resolve(raw)
	for _, height := range []int{1, 3} {
		tabs, _ := ui.NewTabs([]ui.TabItem{{ID: "a", Title: "Overview"}, {ID: "b", Title: "한글", Closable: true}})
		state := &ui.TabState{Active: "a", Focused: "b"}
		v, err := ui.NewTabView(tabs, state, palette)
		if err != nil {
			t.Fatal(err)
		}
		v.SetRect(2, 2, 40, height)
		focus := func(tview.Primitive) {}
		v.Focus(focus)
		v.Draw(screen)
		screen.Show()
		layout := tabs.Layout(state, 40)
		active, candidate := layout.Cells[0], layout.Cells[1]
		y := 2
		if height == 3 {
			y++
		}
		cells, width, _ := screen.GetContents()
		_, activeBackground, _ := cells[y*width+2+active.Start+1].Style.Decompose()
		_, _, candidateAttrs := cells[y*width+2+candidate.Start+1].Style.Decompose()
		if activeBackground != palette["selection"].BG || candidateAttrs&tcell.AttrUnderline == 0 {
			t.Fatalf("height %d lost active or focus styling", height)
		}
		var got ui.TabEvent
		v.OnEvent = func(e ui.TabEvent) { got = e }
		click := func(x, row int) {
			v.MouseHandler()(tview.MouseLeftClick, tcell.NewEventMouse(2+x, row, 0, 0), focus)
		}
		if height == 3 {
			click(candidate.Start+1, y-1)
			click(candidate.Start+1, y+1)
			if got.Kind != "" || state.Active != "a" {
				t.Fatalf("decorative rows handled a click: %+v", got)
			}
		}
		click(candidate.Start+uniseg.StringWidth(candidate.Text)-2, y)
		if got.Kind != "close" || got.ID != "b" || state.Active != "a" {
			t.Fatalf("height %d close: %+v", height, got)
		}
		click(candidate.Start+1, y)
		if got.Kind != "activate" || state.Active != "b" {
			t.Fatalf("height %d activate: %+v", height, got)
		}
	}
}
