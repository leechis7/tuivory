package tuivory_test

import (
	"encoding/json"
	"fmt"
	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
	"github.com/rivo/uniseg"
	"os"
	"reflect"
	"strings"
	"testing"
)

type menuScenario struct {
	Root, Caller string
	Steps        []struct {
		Action, Value, Event, ID, Focus string
		Path                            []string
		Closed                          bool
	}
}

func menuFixture(t *testing.T) ([]ui.MenuItem, []menuScenario) {
	t.Helper()
	var data struct {
		Items     []ui.MenuItem
		Scenarios []menuScenario
	}
	b, e := os.ReadFile("testdata/menu-cases.json")
	if e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(b, &data); e != nil {
		t.Fatal(e)
	}
	return data.Items, data.Scenarios
}
func TestMenuSharedNavigation(t *testing.T) {
	items, scenarios := menuFixture(t)
	for _, s := range scenarios {
		m, e := ui.NewMenu(items)
		if e != nil {
			t.Fatal(e)
		}
		if e := m.Open(s.Root, s.Caller); e.Kind != "open" {
			t.Fatal("open")
		}
		for _, step := range s.Steps {
			e := m.Handle(step.Action, step.Value, 5)
			if e.Kind != step.Event || e.ID != step.ID || e.ReturnID != s.Caller {
				t.Fatalf("%s: %+v", step.Action, e)
			}
			if m.Opened() == step.Closed {
				t.Fatal("open state")
			}
			if !step.Closed {
				if m.FocusedID() != step.Focus || strings.Join(m.Path(), "/") != strings.Join(step.Path, "/") {
					t.Fatal("state", m.FocusedID(), m.Path())
				}
			}
		}
	}
}
func TestMenuValidationAndStateUpdate(t *testing.T) {
	items, _ := menuFixture(t)
	m, _ := ui.NewMenu(items)
	m.Open("file", "origin")
	m.Handle("next", "", 4)
	m.Handle("activate", "", 4)
	m.Handle("next", "", 4)
	before := m.Path()
	bad := append(append([]ui.MenuItem{}, items...), items[0])
	if _, e := m.SetItems(bad); e == nil || !reflect.DeepEqual(m.Path(), before) {
		t.Fatal("non-atomic update")
	}
	if _, e := m.SetItems(items); e != nil || m.FocusedID() != "deep" {
		t.Fatal("stable IDs")
	}
	updated := append([]ui.MenuItem{}, items...)
	updated[4].Disabled = true
	e, err := m.SetItems(updated)
	if err != nil || e.Kind != "close" || e.ReturnID != "origin" || m.Opened() {
		t.Fatal("removed/disabled ancestor must restore caller", e, err)
	}
	for _, invalid := range [][]ui.MenuItem{{{ID: "@back"}}, {{ID: "a", Parent: "b"}, {ID: "b", Parent: "a"}}, {{ID: "a", Parent: "missing"}}, {{ID: "a", Mnemonic: "f"}, {ID: "b", Mnemonic: "F"}}, {{ID: "a", Separator: true}, {ID: "b", Parent: "a"}}} {
		if _, e := ui.NewMenu(invalid); e == nil {
			t.Fatal("invalid tree accepted")
		}
	}
	disabled, _ := ui.NewMenu([]ui.MenuItem{{ID: "g"}, {ID: "a", Parent: "g", Disabled: true}})
	disabled.Open("g", "origin")
	if disabled.Handle("activate", "", 5).Kind != "" || disabled.Handle("right", "", 5).Kind != "" {
		t.Fatal("disabled child activated")
	}
}
func TestMenuLiteralLayoutAndBounds(t *testing.T) {
	items, _ := menuFixture(t)
	items[1].Secondary = "[red] literal 界"
	items[1].Icon = "◆"
	items[1].ASCIIIcon = "*"
	m, _ := ui.NewMenu(items)
	m.Open("file", "origin")
	for _, ascii := range []bool{false, true} {
		for w := 0; w < 90; w++ {
			for h := 0; h < 12; h++ {
				out := m.Layout(w, h, ascii)
				if len(out) > h {
					t.Fatal("height")
				}
				for _, line := range out {
					if uniseg.StringWidth(line.Text) > w {
						t.Fatal("line")
					}
					for _, s := range line.Spans {
						if s.Start+s.Width > w || uniseg.StringWidth(s.Text) > s.Width {
							t.Fatalf("%dx%d %+v", w, h, s)
						}
					}
				}
				b := m.BarLayout(w)
				for _, c := range b.Cells {
					if c.Start+c.Width > w || uniseg.StringWidth(c.Text) > c.Width {
						t.Fatal("bar overflow")
					}
				}
			}
		}
	}
	for w := 0; w < 80; w++ {
		for h := 0; h < 20; h++ {
			r := ui.MenuPlacement(ui.CellRect{X: 70, Y: 18, Width: 1, Height: 1}, ui.CellRect{Width: w, Height: h}, 40, 20)
			if r.X < 0 || r.Y < 0 || r.X+r.Width > w || r.Y+r.Height > h {
				t.Fatal("popup escaped viewport", r)
			}
		}
	}
	m.Open("recent", "origin")
	m.Focus("deep")
	if m.Click("off").Kind != "" || m.Click("line").Kind != "" {
		t.Fatal("out of level click")
	}
	if m.Click("@back").Kind != "back" || m.FocusedID() != "recent" {
		t.Fatal("parent selection")
	}
}

func TestMenuPhysicalOutputAndLocalKeys(t *testing.T) {
	items, _ := menuFixture(t)
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			for _, ascii := range []bool{false, true} {
				m, _ := ui.NewMenu(items)
				m.Open("file", "origin")
				doc, _ := ui.CandidateTokens()
				raw, _ := doc.Palette(theme, profile)
				p, _ := ui.Resolve(raw)
				v, e := ui.NewMenuView(m, p, ascii, nil)
				if e != nil {
					t.Fatal(e)
				}
				s := drawingScreen(t)
				s.SetSize(40, 12)
				for y := 0; y < 12; y++ {
					s.PutStr(0, y, strings.Repeat("Q", 40))
				}
				s.Put(2, 2, "界", tcell.StyleDefault)
				s.Put(34, 2, "한", tcell.StyleDefault)
				s.Show()
				v.SetRect(3, 1, 32, 8)
				v.Draw(s)
				s.Show()
				outputCell(t, s, 0, 2, "Q")
				outputCell(t, s, 39, 2, "Q")
				outputCell(t, s, 2, 2, " ")
				outputCell(t, s, 35, 2, " ")
				if style := outputCell(t, s, 3, 1, ">"); style != p["selection"].Style() {
					t.Fatal("selection style differs", theme, profile)
				}
				if m.FocusedID() != "new" || m.ReturnID() != "origin" {
					t.Fatal("draw mutated logical state")
				}
			}
		}
	}
	if action, _ := ui.MenuKey(tcell.NewEventKey(tcell.KeyF10, 0, 0)); action != "" {
		t.Fatal("global F10 belongs to host")
	}
}
func TestMenuBarDoesNotCaptureLaterClicks(t *testing.T) {
	items, _ := menuFixture(t)
	m, _ := ui.NewMenu(items)
	doc, _ := ui.CandidateTokens()
	raw, _ := doc.Palette("dark", "256")
	p, _ := ui.Resolve(raw)
	var event ui.MenuEvent
	v, _ := ui.NewMenuBarView(m, p, func(e ui.MenuEvent) { event = e })
	v.SetRect(0, 0, 80, 1)
	s := drawingScreen(t)
	s.SetSize(80, 8)
	v.Draw(s)
	used, capture := v.MouseHandler()(tview.MouseLeftClick, tcell.NewEventMouse(4, 0, tcell.ButtonNone, 0), func(tview.Primitive) {})
	if !used || capture != nil || event.Kind != "open_request" {
		t.Fatal("bar kept mouse capture", used, capture, event)
	}
}
func TestMenuEmptyDepthAndCountLimits(t *testing.T) {
	m, _ := ui.NewMenu(nil)
	m.Open("", "editor")
	_, h := m.ContentSize()
	if h != 1 || len(m.Layout(20, h, false)) != 1 || m.Handle("activate", "", h).Kind != "" {
		t.Fatal("empty menu must reserve its message row")
	}
	items := []ui.MenuItem{}
	parent := ""
	for n := 0; n < 32; n++ {
		id := fmt.Sprint(n)
		items = append(items, ui.MenuItem{ID: id, Parent: parent})
		parent = id
	}
	if _, e := ui.NewMenu(items); e != nil {
		t.Fatal(e)
	}
	items = append(items, ui.MenuItem{ID: "too-deep", Parent: parent})
	if _, e := ui.NewMenu(items); e == nil {
		t.Fatal("depth >32")
	}
	many := make([]ui.MenuItem, 10000)
	for n := range many {
		many[n] = ui.MenuItem{ID: fmt.Sprintf("item-%d", n)}
	}
	if _, e := ui.NewMenu(many); e != nil {
		t.Fatal("valid count boundary", e)
	}
	many = append(many, ui.MenuItem{ID: "item-10000"})
	if _, e := ui.NewMenu(many); e == nil {
		t.Fatal("count limit")
	}
}
