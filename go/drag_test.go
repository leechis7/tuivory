package tuivory_test

import (
	"encoding/json"
	"fmt"
	ui "github.com/leechis7/tuivory/go"
	"os"
	"reflect"
	"testing"
)

func TestSharedDropRequests(t *testing.T) {
	var f struct {
		TabRevision  uint64 `json:"tab_revision"`
		TreeRevision uint64 `json:"tree_revision"`
		Tabs         []ui.TabItem
		Tree         []ui.TreeNode
		Cases        []struct {
			Kind, Source, Target, Position, Error, Parent string
			Order, Locked                                 []string
			Deny                                          bool
		}
	}
	b, e := os.ReadFile("testdata/drag-cases.json")
	if e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(b, &f); e != nil {
		t.Fatal(e)
	}
	for _, c := range f.Cases {
		t.Run(c.Kind+"/"+c.Source+"/"+c.Target+"/"+c.Position+"/"+c.Error, func(t *testing.T) {
			options := ui.DragOptions{Locked: c.Locked}
			policy := func(ui.DropRequest) bool { return !c.Deny }
			var order []string
			var err error
			if c.Kind == "tabs" {
				model, _ := ui.NewTabs(f.Tabs)
				before := model.Items()
				var r ui.DropRequest
				r, err = model.RequestDrop(c.Source, c.Target, ui.DropPosition(c.Position), options, policy)
				if err == nil {
					if r.Revision != f.TabRevision {
						t.Fatal("Go/Rust tab revision", r.Revision, f.TabRevision)
					}
					next, e := model.ApplyDrop(r)
					if e != nil {
						t.Fatal(e)
					}
					for _, i := range next.Items() {
						order = append(order, i.ID)
					}
					if !reflect.DeepEqual(before, model.Items()) {
						t.Fatal("mutated original")
					}
				}
			} else {
				model, _ := ui.NewTree(f.Tree)
				before := model.Nodes()
				var r ui.DropRequest
				r, err = model.RequestDrop(c.Source, c.Target, ui.DropPosition(c.Position), options, policy)
				if err == nil {
					if r.Revision != f.TreeRevision {
						t.Fatal("Go/Rust tree revision", r.Revision, f.TreeRevision)
					}
					next, e := model.ApplyDrop(r)
					if e != nil {
						t.Fatal(e)
					}
					for _, n := range next.Nodes() {
						order = append(order, n.ID)
						if n.ID == c.Source && n.Parent != c.Parent {
							t.Fatal("parent", n.Parent)
						}
					}
					if !reflect.DeepEqual(before, model.Nodes()) {
						t.Fatal("mutated original")
					}
				}
			}
			if c.Error != "" {
				if err == nil || err.Error() != c.Error {
					t.Fatalf("got %v expected %s", err, c.Error)
				}
			} else if err != nil || !reflect.DeepEqual(order, c.Order) {
				t.Fatalf("order %v error %v", order, err)
			}
		})
	}
}

func TestDragCaptureCancellationAndStaleData(t *testing.T) {
	tabs, _ := ui.NewTabs([]ui.TabItem{{ID: "a", Title: "A", Edited: true}, {ID: "b", Title: "B", Closable: true}, {ID: "c", Title: "C"}})
	s := ui.TabState{Active: "b", Focused: "a"}
	tabs.Layout(&s, 40)
	original := s
	d := ui.DragState{}
	o := ui.DragOptions{AutoScroll: true}
	p := func(action string, x, y, width int) *ui.DropRequest {
		return tabs.Drag(&s, &d, ui.DragPointer{Action: action, X: x, Y: y, Width: width, Height: 1}, o, nil)
	}
	p("down", 2, 0, 40)
	if !d.Captured() {
		t.Fatal("no capture")
	}
	p("move", 3, 0, 40)
	if d.Phase != "armed" {
		t.Fatal("threshold")
	}
	p("move", 17, 0, 40)
	if !d.Allowed || d.TargetID != "c" {
		t.Fatalf("feedback %+v", d)
	}
	r := p("up", 17, 0, 40)
	if r == nil || d.Captured() || d.Result != "drop" {
		t.Fatal("drop/release")
	}
	if s != original {
		t.Fatal("state changed")
	}
	next, e := tabs.ApplyDrop(*r)
	if e != nil {
		t.Fatal(e)
	}
	next.Reconcile(&s)
	if s.Active != "b" || s.Focused != "a" || !next.Items()[2].Edited {
		t.Fatal("stable state/metadata")
	}
	s = original
	p("down", 2, 0, 40)
	p("move", 17, 0, 40)
	if p("up", -5, 5, 40) != nil || d.Result != "reject" || s != original {
		t.Fatal("outside drop")
	}
	p("down", 2, 0, 40)
	p("move", 17, 0, 40)
	d.Cancel()
	if d.Captured() || s != original {
		t.Fatal("cancel")
	}
	p("down", 2, 0, 40)
	p("move", 17, 0, 39)
	if d.Captured() || d.Result != "stale" {
		t.Fatal("resize")
	}
	p("down", 2, 0, 40)
	changed := tabs.Items()
	changed[2].Title = "updated"
	replacement, _ := ui.NewTabs(changed)
	replacement.Drag(&s, &d, ui.DragPointer{Action: "up", X: 17, Width: 40, Height: 1}, o, nil)
	if d.Result != "stale" || d.Captured() {
		t.Fatal("stale data")
	}
	if _, e = replacement.ApplyDrop(*r); e == nil {
		t.Fatal("stale request")
	}
	request, e := tabs.KeyboardDrop(&ui.TabState{Focused: "b"}, ui.DragNext, ui.DragOptions{}, nil)
	if e != nil || request.SourceID != "b" || request.TargetID != "c" {
		t.Fatal("keyboard", e)
	}
	p("down", 2, 0, 40)
	p("move", 17, 0, 40)
	revoked := ui.DragOptions{Locked: []string{"c"}}
	if tabs.Drag(&s, &d, ui.DragPointer{Action: "up", X: 17, Width: 40, Height: 1}, revoked, nil) != nil || d.Result != "reject" {
		t.Fatal("policy not rechecked")
	}
	p("down", 2, 0, 40)
	s.Focused = "b"
	if p("up", 17, 0, 40) != nil || d.Result != "stale" || s.Focused != "b" {
		t.Fatal("external focus update")
	}
}

func TestTreeDragPreviewAndKeyboard(t *testing.T) {
	tree, _ := ui.NewTree([]ui.TreeNode{{ID: "r", Name: "Root"}, {ID: "a", Parent: "r", Name: "A"}, {ID: "a1", Parent: "a", Name: "A1"}, {ID: "b", Parent: "r", Name: "B"}, {ID: "c", Parent: "r", Name: "C", Branch: true}})
	s := ui.TreeState{Selected: "a1", Expanded: map[string]bool{"r": true, "a": true}}
	tree.Reconcile(&s, 8)
	original := ui.TreeState{Selected: s.Selected, Expanded: map[string]bool{"r": true, "a": true}}
	d := ui.DragState{}
	o := ui.DragOptions{HoverExpand: true, AutoScroll: true}
	pointer := func(a string, x, y int) *ui.DropRequest {
		return tree.Drag(&s, &d, ui.DragPointer{Action: a, X: x, Y: y, Width: 30, Height: 8}, o, nil)
	}
	pointer("down", 4, 3)
	pointer("move", 10, 4)
	if !d.Allowed || d.Position != ui.DropInside {
		t.Fatalf("feedback %+v", d)
	}
	rows, _ := tree.DragRows(&s, &d, 8)
	if len(rows) != 5 {
		t.Fatal("rows")
	}
	if !reflect.DeepEqual(s, original) {
		t.Fatal("preview changed state")
	}
	r := pointer("up", 10, 4)
	if r == nil {
		t.Fatal("missing request")
	}
	if !reflect.DeepEqual(s, original) {
		t.Fatal("drop changed state")
	}
	moved, e := tree.ApplyDrop(*r)
	if e != nil {
		t.Fatal(e)
	}
	for _, n := range moved.Nodes() {
		if n.ID == "b" && n.Parent != "c" {
			t.Fatal("reparent")
		}
	}
	r2, e := tree.KeyboardDrop(&ui.TreeState{Selected: "b"}, ui.DragInside, o, nil)
	if e != nil || r2.TargetID != "a" {
		t.Fatal("keyboard inside", e)
	}
	r3, e := tree.KeyboardDrop(&ui.TreeState{Selected: "a1"}, ui.DragOutside, o, nil)
	if e != nil || r3.TargetID != "a" || r3.Position != ui.DropAfter {
		t.Fatal("keyboard outside", e)
	}
	pointer("down", 4, 1)
	pointer("move", 10, 2)
	if d.Allowed || d.Reason != "cycle" {
		t.Fatal("cycle feedback", d.Reason)
	}
	d.Cancel()
	if !reflect.DeepEqual(s, original) {
		t.Fatal("reject changed state")
	}
	pointer("down", 4, 3)
	s.Expanded["c"] = true
	if pointer("up", 10, 5) != nil || d.Result != "stale" || !s.Expanded["c"] {
		t.Fatal("external expansion update")
	}
}

func TestDragTemporaryEdgeScroll(t *testing.T) {
	var items []ui.TabItem
	for i := 0; i < 30; i++ {
		items = append(items, ui.TabItem{ID: fmt.Sprint(i), Title: fmt.Sprint(i)})
	}
	tabs, _ := ui.NewTabs(items)
	s := ui.TabState{Active: "0", Focused: "0"}
	tabs.Layout(&s, 20)
	before := s
	d := ui.DragState{}
	o := ui.DragOptions{AutoScroll: true}
	tabs.Drag(&s, &d, ui.DragPointer{Action: "down", X: 2, Width: 20, Height: 1}, o, nil)
	for i := 0; i < 6; i++ {
		tabs.Drag(&s, &d, ui.DragPointer{Action: "move", X: 19, Width: 20, Height: 1}, o, nil)
	}
	layout := tabs.DragLayout(&s, &d, 20)
	if len(layout.Cells) == 0 || layout.Cells[0].ID == "0" || s != before {
		t.Fatal("tab edge preview/state")
	}
	d.Cancel()
	if s != before {
		t.Fatal("tab cancel scroll")
	}
	nodes := []ui.TreeNode{{ID: "r"}}
	for i := 0; i < 30; i++ {
		nodes = append(nodes, ui.TreeNode{ID: fmt.Sprint(i), Parent: "r"})
	}
	tree, _ := ui.NewTree(nodes)
	state := ui.TreeState{Selected: "0", Expanded: map[string]bool{"r": true}}
	tree.Reconcile(&state, 4)
	scroll := state.Scroll
	tree.Drag(&state, &d, ui.DragPointer{Action: "down", X: 4, Y: 1, Width: 20, Height: 4}, o, nil)
	for i := 0; i < 6; i++ {
		tree.Drag(&state, &d, ui.DragPointer{Action: "move", X: 15, Y: 3, Width: 20, Height: 4}, o, nil)
	}
	_, preview := tree.DragRows(&state, &d, 4)
	if preview <= scroll || state.Scroll != scroll || state.Selected != "0" {
		t.Fatal("tree edge preview/state")
	}
	d.Cancel()
	if state.Scroll != scroll {
		t.Fatal("tree cancel scroll")
	}
}

func TestDragViewsPhysicalFeedback(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, ascii := range []bool{false, true} {
				tokens, _ := ui.CandidateTokens()
				raw, _ := tokens.Palette(theme, profile)
				palette, _ := ui.Resolve(raw)
				tabs, _ := ui.NewTabs([]ui.TabItem{{ID: "a", Title: "한글 A"}, {ID: "b", Title: "界 B"}, {ID: "c", Title: "😀 C"}})
				state := ui.TabState{Active: "b", Focused: "a"}
				view, _ := ui.NewTabView(tabs, &state, palette)
				view.Drag = &ui.DragState{}
				view.ASCII = ascii
				view.SetRect(0, 0, 60, 1)
				screen := ui.NewSimulationScreen("UTF-8")
				screen.Init()
				screen.SetSize(60, 10)
				focus := func(ui.Primitive) {}
				view.Draw(screen)
				screen.Show()
				layout := tabs.Layout(&state, 60)
				target := layout.Cells[2]
				dropX := target.Start + target.Width - 1
				handler := view.MouseHandler()
				_, capture := handler(ui.MouseLeftDown, ui.NewEventMouse(2, 0, ui.Button1, 0), focus)
				if capture != view {
					t.Fatal("capture")
				}
				handler(ui.MouseMove, ui.NewEventMouse(dropX, 0, ui.Button1, 0), focus)
				view.Draw(screen)
				screen.Show()
				cells, _, _ := screen.GetContents()
				want := "│"
				if ascii {
					want = "|"
				}
				if string(cells[dropX].Runes) != want {
					t.Fatal("marker", theme, profile, ascii, string(cells[dropX].Runes))
				}
				_, _, attrs := cells[dropX].Style.Decompose()
				if attrs&ui.AttrUnderline == 0 {
					t.Fatal("non-color feedback")
				}
				requests := 0
				view.OnDrop = func(r ui.DropRequest) {
					requests++
					if r.SourceID != "a" || r.TargetID != "c" {
						t.Fatal("request")
					}
				}
				handler(ui.MouseLeftUp, ui.NewEventMouse(dropX, 0, 0, 0), focus)
				handler(ui.MouseLeftClick, ui.NewEventMouse(dropX, 0, 0, 0), focus)
				if requests != 1 || state.Active != "b" || state.Focused != "a" {
					t.Fatal("drop/click changed selection")
				}
				handler(ui.MouseLeftDown, ui.NewEventMouse(2, 0, ui.Button1, 0), focus)
				handler(ui.MouseMove, ui.NewEventMouse(-5, 5, ui.Button1, 0), focus)
				view.Draw(screen)
				screen.Show()
				cells, _, _ = screen.GetContents()
				if string(cells[0].Runes) != "!" {
					t.Fatalf("invalid feedback: %q %+v", string(cells[0].Runes), view.Drag)
				}
				view.SetPalette(palette)
				if view.Drag.Captured() {
					t.Fatal("restyle capture")
				}
				tree, _ := ui.NewTree([]ui.TreeNode{{ID: "r", Name: "한글 Root"}, {ID: "a", Parent: "r", Name: "A"}, {ID: "a1", Parent: "a", Name: "界 😀"}, {ID: "b", Parent: "r", Name: "B"}, {ID: "c", Parent: "r", Name: "C", Branch: true}})
				ts := ui.TreeState{Selected: "a1", Expanded: map[string]bool{"r": true, "a": true}}
				tv, _ := ui.NewTreeView(tree, &ts, palette)
				tv.SetBorder(false)
				tv.SetRect(0, 1, 30, 8)
				tv.ASCII = ascii
				tv.Drag = &ui.DragState{}
				tv.Draw(screen)
				screen.Show()
				th := tv.MouseHandler()
				th(ui.MouseLeftDown, ui.NewEventMouse(4, 4, ui.Button1, 0), focus)
				th(ui.MouseMove, ui.NewEventMouse(10, 5, ui.Button1, 0), focus)
				tv.Draw(screen)
				screen.Show()
				cells, sw, _ := screen.GetContents()
				marker := "↳"
				if ascii {
					marker = "+"
				}
				if string(cells[5*sw].Runes) != marker || string(cells[3*sw+8].Runes) != "界" {
					t.Fatal("tree marker/wide glyph", theme, profile, ascii)
				}
				tv.InputHandler()(ui.NewEventKey(ui.KeyEscape, 0, 0), focus)
				th(ui.MouseLeftUp, ui.NewEventMouse(10, 5, 0, 0), focus)
				th(ui.MouseLeftClick, ui.NewEventMouse(10, 5, 0, 0), focus)
				if ts.Selected != "a1" {
					t.Fatal("tree cancel selection")
				}
				th(ui.MouseLeftDown, ui.NewEventMouse(4, 2, ui.Button1, 0), focus)
				th(ui.MouseMove, ui.NewEventMouse(10, 3, ui.Button1, 0), focus)
				tv.Draw(screen)
				screen.Show()
				cells, sw, _ = screen.GetContents()
				if string(cells[3*sw].Runes) != "!" || tv.Drag.Allowed {
					t.Fatal("tree cycle feedback")
				}
				tv.SetRect(0, 1, 0, 0)
				if tv.Drag.Captured() {
					t.Fatal("hidden capture")
				}
				screen.Fini()
			}
		}
	}
}
