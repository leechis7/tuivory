package tuivory_test

import (
	"encoding/json"
	ui "github.com/leechis7/tuivory/go"
	terminal "github.com/leechis7/tuivory/go/terminal"
	widgets "github.com/leechis7/tuivory/go/ui"
	"os"
	"reflect"
	"testing"
)

func TestSharedInputEnvelope(t *testing.T) {
	raw, err := os.ReadFile("testdata/ui-input-cases.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Cases []struct {
			Name, Raw, Action, Text string
			Event                   ui.InputEvent
		}
	}
	if err = json.Unmarshal(raw, &fixture); err != nil {
		t.Fatal(err)
	}
	for _, c := range fixture.Cases {
		t.Run(c.Name, func(t *testing.T) {
			event := c.Event
			key := func(k terminal.Key, r rune, m terminal.ModMask) ui.InputEvent {
				return ui.InputFromKey(terminal.NewEventKey(k, r, m))
			}
			switch c.Raw {
			case "unicode":
				event = key(terminal.KeyRune, '한', terminal.ModNone)
			case "ctrl_c":
				event = key(terminal.KeyCtrlC, 0, terminal.ModNone)
			case "ctrl_shift_c":
				event = key(terminal.KeyRune, 'C', terminal.ModCtrl|terminal.ModShift)
			case "shift_left":
				event = key(terminal.KeyLeft, 0, terminal.ModShift)
			case "alt_right":
				event = key(terminal.KeyRight, 0, terminal.ModAlt)
			case "backtab":
				event = key(terminal.KeyBacktab, 0, terminal.ModNone)
			case "enter":
				event = key(terminal.KeyEnter, 0, terminal.ModNone)
			case "f10":
				event = key(terminal.KeyF10, 0, terminal.ModNone)
			case "paste":
				event = ui.PasteInput(c.Event.Text)
			case "resize":
				event = ui.ResizeInput(8, 3)
			case "drag":
				event = ui.InputFromMouse(widgets.MouseMove, terminal.NewEventMouse(6, 3, terminal.Button1, terminal.ModShift))
			case "wheel":
				event = ui.InputFromMouse(widgets.MouseScrollDown, terminal.NewEventMouse(6, 3, terminal.WheelDown, terminal.ModNone))
			}
			if !reflect.DeepEqual(event, c.Event) {
				t.Fatalf("input %+v expected %+v", event, c.Event)
			}
			action, text := event.EditingAction()
			if action != c.Action || text != c.Text {
				t.Fatalf("action %q text %q", action, text)
			}
		})
	}
}

func TestHostLexerByteOffsets(t *testing.T) {
	raw, err := os.ReadFile("testdata/ui-input-cases.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Offsets struct {
			Text       string
			Boundaries [][2]int
			Invalid    []int
		} `json:"byte_offsets"`
	}
	if err = json.Unmarshal(raw, &fixture); err != nil {
		t.Fatal(err)
	}
	for _, pair := range fixture.Offsets.Boundaries {
		index, err := ui.GraphemeIndex(fixture.Offsets.Text, pair[0])
		if err != nil || index != pair[1] {
			t.Fatal(pair, index, err)
		}
	}
	d := ui.NewEditor(fixture.Offsets.Text)
	if err = d.SetByteSyntax([]ui.ByteSyntaxSpan{{Start: 1, End: 7, Role: "info"}}); err != nil {
		t.Fatal(err)
	}
	for _, offset := range fixture.Offsets.Invalid {
		if _, err := ui.GraphemeIndex(fixture.Offsets.Text, offset); err == nil {
			t.Fatal("invalid byte offset", offset)
		}
		if err = d.SetByteSyntax([]ui.ByteSyntaxSpan{{Start: offset, End: offset, Role: "info"}}); err == nil {
			t.Fatal("invalid lexer span", offset)
		}
		if d.Syntax[0].Start != 1 || d.Syntax[0].End != 3 {
			t.Fatal("non-atomic lexer conversion")
		}
	}
}

func TestFacadeGlobalsAndNativeComposition(t *testing.T) {
	old := widgets.GetBorders()
	defer widgets.SetBorders(old)
	borders := old
	borders.TopLeft = '+'
	widgets.SetBorders(borders)
	screen := terminal.NewSimulationScreen("UTF-8")
	if err := screen.Init(); err != nil {
		t.Fatal(err)
	}
	defer screen.Fini()
	screen.SetSize(40, 12)
	form := widgets.NewForm().AddInputField("Name", "한글", 10, nil, nil).AddPasswordField("Password", "secret", 10, '*', nil)
	if form.GetFormItem(1).(*widgets.InputField).GetText() != "secret" {
		t.Fatal("compatibility mask/raw getter")
	}
	area := widgets.NewTextArea().SetText("한글 é\nOriginal", false)
	area.SetClipboard(func(string) {}, func() string { return "paste" })
	layout := widgets.NewFlex().AddItem(form, 20, 0, true).AddItem(area, 0, 1, false)
	pages := widgets.NewPages().AddPage("main", layout, true, true)
	app := widgets.NewApplication().SetScreen(screen).SetRoot(pages, true)
	app.SetInputCapture(func(event *terminal.EventKey) *terminal.EventKey { return event })
	box := widgets.NewBox().SetBorder(true)
	box.SetRect(0, 0, 8, 4)
	box.Draw(screen)
	screen.Show()
	cells, _, _ := screen.GetContents()
	if cells[0].Runes[0] != '+' {
		t.Fatal("global setter failed to configure native drawing")
	}
	app.SetFocus(area)
	if app.GetFocus() != area {
		t.Fatal("focus composition")
	}
}
