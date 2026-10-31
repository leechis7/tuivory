package tuivory_test

import (
	"encoding/json"
	"fmt"
	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
	"os"
	"strings"
	"testing"
)

func TestLongDocumentScrollAndEdit(t *testing.T) {
	raw := strings.Repeat("line 界 é [literal]\n", 10000)
	d := ui.NewTextView(raw)
	d.ScrollY = 9995
	if rows := d.Layout(40, 5); len(rows) != 5 || !strings.Contains(rows[0].Text, "literal") {
		t.Fatal("long document viewport")
	}
	d.Buffer.Handle("select_all", "")
	if got := d.Handle("copy", "").Text; got != raw {
		t.Fatal("long document original copy")
	}
	d.Buffer.State.ReadOnly = false
	d.Handle("paste", "replacement")
	d.Handle("undo", "")
	if d.Buffer.Text() != raw {
		t.Fatal("long document undo")
	}
}

func TestSharedTextAndContainerRules(t *testing.T) {
	raw, e := os.ReadFile("testdata/controls-cases.json")
	if e != nil {
		t.Fatal(e)
	}
	var data struct {
		Text []struct {
			Name, Text, Expected string
			Secret               bool
			SingleLine           bool `json:"single_line"`
			ReadOnly             bool `json:"read_only"`
			Cursor               int
			Ops                  []struct {
				Action, Text, Kind string
				EventText          string `json:"event_text"`
			}
		}
		Layout []struct {
			Name     string
			Bounds   ui.CellRect
			Options  ui.ContainerOptions
			Items    []ui.LayoutItem
			Expected [][]any
		}
	}
	if e = json.Unmarshal(raw, &data); e != nil {
		t.Fatal(e)
	}
	for _, c := range data.Text {
		t.Run(c.Name, func(t *testing.T) {
			b := ui.NewTextBuffer(c.Text)
			b.Secret = c.Secret
			b.SingleLine = c.SingleLine
			b.State.ReadOnly = c.ReadOnly
			for _, op := range c.Ops {
				event := b.Handle(op.Action, op.Text)
				if event.Kind != op.Kind || event.Text != op.EventText {
					t.Fatalf("%s: %#v", op.Action, event)
				}
			}
			if b.Text() != c.Expected || b.Cursor != c.Cursor {
				t.Fatalf("text/cursor: %q %d", b.Text(), b.Cursor)
			}
			if c.Secret {
				encoded, _ := json.Marshal(b)
				for _, value := range []string{string(encoded), fmt.Sprintf("%+v", b), fmt.Sprintf("%#v", b)} {
					if strings.Contains(value, c.Text) {
						t.Fatal("secret leaked", value)
					}
				}
			}
		})
	}
	for _, c := range data.Layout {
		t.Run(c.Name, func(t *testing.T) {
			rects, e := ui.ComputeContainer(c.Bounds, c.Items, c.Options)
			if e != nil {
				t.Fatal(e)
			}
			if len(rects) != len(c.Expected) {
				t.Fatal(rects)
			}
			for i, r := range rects {
				want := c.Expected[i]
				if r.ID != want[0] || r.Rect.X != int(want[1].(float64)) || r.Rect.Y != int(want[2].(float64)) || r.Rect.Width != int(want[3].(float64)) || r.Rect.Height != int(want[4].(float64)) {
					t.Fatal(r, want)
				}
			}
		})
	}
}
func TestSecretFormsAndStandaloneControls(t *testing.T) {
	secret := "sëcret秘密😀"
	form, e := ui.NewForm([]ui.FormField{{ID: "secret", Kind: "password", Value: secret, Required: true}, {ID: "button", Kind: "button", Label: "Save"}})
	if e != nil {
		t.Fatal(e)
	}
	for _, v := range []any{form, form.Fields(), form.Layout(60, 10)} {
		bytes, _ := json.Marshal(v)
		if strings.Contains(string(bytes), secret) || strings.Contains(fmt.Sprintf("%+v", v), secret) {
			t.Fatal("secret leaked", v)
		}
	}
	value, ok := form.Value("secret")
	if !ok || value != secret {
		t.Fatal("explicit raw value")
	}
	form.Handle("select_all", "")
	if form.Handle("copy", "").Text != "" {
		t.Fatal("secret copy")
	}
	form.Handle("paste", "new")
	value, _ = form.Value("secret")
	if value != "new" {
		t.Fatal(value)
	}
	form.Focus("button")
	form.Handle("left", "")
	if form.Focused() != "secret" {
		t.Fatal("button navigation")
	}
	form.Handle("select_all", "")
	form.Handle("paste", "   ")
	if form.Handle("submit", "").Kind != "invalid" {
		t.Fatal("required secret validates raw value")
	}
	button, _ := ui.NewButton("b", "동작 Action")
	button.SetState("b", ui.ControlState{Busy: true})
	if button.Handle("activate", "").Kind != "" {
		t.Fatal("busy activated")
	}
	button.SetState("b", ui.ControlState{Disabled: true})
	if button.Click("b", "").Kind != "" {
		t.Fatal("disabled activated")
	}
	empty, _ := ui.NewForm([]ui.FormField{{ID: "pw", Kind: "password", Required: true}})
	if empty.Handle("submit", "").Kind != "invalid" {
		t.Fatal("required password")
	}
}
func TestTextViewsLiteralSelectionAndResize(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			doc, _ := ui.CandidateTokens()
			raw, _ := doc.Palette(theme, profile)
			p, _ := ui.Resolve(raw)
			d := ui.NewTextView("[red]界é😀\nsecond\nthird")
			d.Buffer.Select(0, 6)
			d.Syntax = []ui.SyntaxSpan{{Start: 0, End: 2, Role: "accent"}}
			view, e := ui.NewEditorView(d, p, nil)
			if e != nil {
				t.Fatal(e)
			}
			s := drawingScreen(t)
			s.SetSize(40, 10)
			view.SetRect(1, 1, 20, 4)
			view.Focus(func(tview.Primitive) {})
			view.Draw(s)
			s.Show()
			outputCell(t, s, 1, 1, "[")
			view.PasteHandler()("bad", func(tview.Primitive) {})
			if strings.Contains(d.Buffer.Text(), "bad") {
				t.Fatal("read-only paste")
			}
			for _, size := range [][2]int{{1, 1}, {0, 0}, {30, 8}} {
				view.SetRect(1, 1, size[0], size[1])
				view.Draw(s)
				s.Show()
			}
			original := d.Buffer.Text()
			d.Handle("select_all", "")
			if d.Handle("copy", "").Text != original {
				t.Fatal("original copy")
			}
		}
	}
	editor := ui.NewEditor("a\n" + strings.Repeat("界", 100))
	editor.Handle("insert", "x")
	rows := editor.Layout(12, 1)
	if len(rows) != 1 || editor.ScrollY == 0 || editor.ScrollX == 0 {
		t.Fatal("cursor not revealed", rows, editor.ScrollX, editor.ScrollY)
	}
	editor.Point(2, 0, 12, 1, false)
	editor.Point(8, 0, 12, 1, true)
	lo, hi := editor.Buffer.Selection()
	if hi <= lo {
		t.Fatal("drag selection")
	}
}
func TestContainersRouteModalInputAndPreserveState(t *testing.T) {
	doc, _ := ui.CandidateTokens()
	raw, _ := doc.Palette("dark", "256")
	p, _ := ui.Resolve(raw)
	bg := tview.NewInputField()
	popup := tview.NewInputField()
	root, e := ui.NewLayerStack([]ui.ContainerChild{{Item: ui.LayoutItem{ID: "bg"}, Child: bg}, {Item: ui.LayoutItem{ID: "popup", Modal: true, Centered: true, Area: ui.CellRect{Width: 8, Height: 3}}, Child: popup}}, p)
	if e != nil {
		t.Fatal(e)
	}
	s := drawingScreen(t)
	root.SetRect(0, 0, 30, 10)
	root.Focus(func(tview.Primitive) {})
	root.Draw(s)
	root.PasteHandler()("secret", func(tview.Primitive) {})
	if bg.GetText() != "" || popup.GetText() != "secret" {
		t.Fatal("modal paste isolation")
	}
	root.InputHandler()(tcell.NewEventKey(tcell.KeyRune, 'x', 0), func(tview.Primitive) {})
	if bg.GetText() != "" {
		t.Fatal("modal key leak")
	}
	root.SetRect(0, 0, 1, 1)
	root.Draw(s)
	root.SetRect(0, 0, 30, 10)
	root.Draw(s)
	if !strings.Contains(popup.GetText(), "secret") {
		t.Fatal("resize cleared state")
	}
	before := root.State.Focused
	if root.SetChildren([]ui.ContainerChild{{Item: ui.LayoutItem{ID: "bad"}}}) == nil || root.State.Focused != before {
		t.Fatal("invalid update mutated")
	}
	if root.FocusID("bg") {
		t.Fatal("background focus escaped modal")
	}
}
func TestExplicitMarkupAndAtomicSyntax(t *testing.T) {
	d := ui.NewTextView("[info]literal[/]")
	if d.Buffer.Text() != "[info]literal[/]" {
		t.Fatal("implicit markup")
	}
	if e := d.SetMarkup("[info]界é[/][[raw]"); e != nil {
		t.Fatal(e)
	}
	if d.Buffer.Text() != "界é[raw]" || len(d.Syntax) != 1 || d.Syntax[0].End != 2 {
		t.Fatal(d.Buffer.Text(), d.Syntax)
	}
	before := d.Buffer.Text()
	for _, bad := range []string{"[unknown]x[/]", "[info]x", "[/]"} {
		if d.SetMarkup(bad) == nil || d.Buffer.Text() != before {
			t.Fatal("non-atomic markup")
		}
	}
	if d.SetSyntax([]ui.SyntaxSpan{{Start: 0, End: 999, Role: "info"}}) == nil || d.SetSyntax([]ui.SyntaxSpan{{Start: 0, End: 1, Role: "missing"}}) == nil {
		t.Fatal("invalid syntax accepted")
	}
	d.SetMarkup("e[info]́[/]")
	if d.Buffer.Text() != "é" || len(d.Syntax) != 0 {
		t.Fatal("split grapheme styling")
	}
}
func TestVirtualScrollAndModalRestore(t *testing.T) {
	doc, _ := ui.CandidateTokens()
	raw, _ := doc.Palette("dark", "256")
	p, _ := ui.Resolve(raw)
	text := tview.NewTextView().SetText("ABCDEFGH").SetWrap(false)
	row, e := ui.NewContainer(ui.ContainerOptions{Kind: "row", VirtualWidth: 8}, []ui.ContainerChild{{Item: ui.LayoutItem{ID: "text"}, Child: text}}, p)
	if e != nil {
		t.Fatal(e)
	}
	row.ScrollX = 3
	row.SetRect(0, 0, 4, 2)
	s := drawingScreen(t)
	row.Draw(s)
	s.Show()
	outputCell(t, s, 0, 0, "D")
	outputCell(t, s, 3, 0, "G")
	items := []ui.LayoutItem{{ID: "one"}, {ID: "two"}, {ID: "a", Modal: true, Hidden: true}, {ID: "b", Modal: true, Hidden: true}}
	state := ui.ContainerState{Focused: "two"}
	state.Reconcile(items)
	items[2].Hidden = false
	state.Reconcile(items)
	if state.Focused != "a" {
		t.Fatal(state)
	}
	items[3].Hidden = false
	state.Reconcile(items)
	items[3].Hidden = true
	state.Reconcile(items)
	if state.Focused != "a" {
		t.Fatal("nested restore", state)
	}
	items[2].Hidden = true
	state.Reconcile(items)
	if state.Focused != "two" {
		t.Fatal("caller restore", state)
	}
}
