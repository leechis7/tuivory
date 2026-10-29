package tuivory_test

import (
	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
	"strings"
	"testing"
)

func TestDisabledPresentationUsesRolesWithoutExtraMarkers(t *testing.T) {
	h, _ := ui.NewHelp([]ui.Shortcut{{Key: "Ctrl+S", Text: "Save", Disabled: true}})
	if row := h.Layout(40, 1)[0]; row.Text != "[Ctrl+S] Save" || row.Role != "disabled" {
		t.Fatal(row)
	}
	list, _ := ui.NewList([]ui.ListItem{{ID: "off", Label: "Unavailable", Secondary: "Reason", Disabled: true}, {ID: "on", Label: "Enabled"}})
	if list.Focus("off") {
		t.Fatal("disabled item focused")
	}
	rows := list.Layout(50, 10, false)
	if strings.Contains(rows[0].Text, "[-]") || rows[1].Role != "disabled" {
		t.Fatal(rows)
	}
	form, err := ui.NewForm([]ui.FormField{
		{ID: "text", Kind: "text", Label: "Name", Value: "Retained", State: ui.ControlState{Disabled: true}},
		{ID: "button", Kind: "button", Label: "Save", State: ui.ControlState{Disabled: true}},
		{ID: "choice", Kind: "radio", Label: "Choice", Options: []ui.FormOption{{ID: "no", Label: "Unavailable", Disabled: true}, {ID: "yes", Label: "Available"}}},
	})
	if err != nil {
		t.Fatal(err)
	}
	rows = form.Layout(60, 20)
	for _, r := range rows {
		if r.ID == "text" || r.ID == "button" {
			if r.Role != "disabled" {
				t.Fatal("active appearance", r)
			}
		}
		if r.Value == "no" && (strings.Contains(r.Text, "[-]") || r.Role != "disabled") {
			t.Fatal(r)
		}
	}
	if strings.HasPrefix(rows[0].Text, "[-]") || !strings.Contains(rows[1].Text, "Retained") {
		t.Fatal(rows)
	}
}

func TestDisabledMenuBarLabelAndHitRegion(t *testing.T) {
	menu, err := ui.NewMenu([]ui.MenuItem{{ID: "on", Label: "File"}, {ID: "off", Label: "Edit", Disabled: true}})
	if err != nil {
		t.Fatal(err)
	}
	bar := menu.BarLayout(40)
	for _, c := range bar.Cells {
		if c.ID == "off" {
			if strings.Contains(c.Text, "- Edit") || c.Width != 6 {
				t.Fatal(c)
			}
			if e := menu.BarClick(c.Start, 40); e.Kind != "" {
				t.Fatal(e)
			}
			return
		}
	}
	t.Fatal("missing disabled bar item")
}

func TestDisabledNoticeActionCue(t *testing.T) {
	q, _ := ui.NewNoticeQueue(2)
	q.Push(ui.Notice{ID: "n", Text: "Ready", Severity: "info", Actions: []ui.NoticeAction{{ID: "save", Label: "Save", Disabled: true}}})
	if row := q.Layout(60, 2, 0)[0]; strings.Contains(row.Text, "[-]") || len(row.Spans) != 1 || row.Spans[0].Role != "disabled" {
		t.Fatal(row)
	}
}

func TestDisabledClickDoesNotMoveFocusOrActivate(t *testing.T) {
	f, _ := ui.NewForm([]ui.FormField{
		{ID: "on", Kind: "button", Label: "Run"},
		{ID: "off", Kind: "button", Label: "Unavailable", State: ui.ControlState{Disabled: true}},
		{ID: "options", Kind: "radio", Label: "Options", Options: []ui.FormOption{{ID: "no", Label: "Unavailable", Disabled: true}, {ID: "yes", Label: "Available"}}},
	})
	before := f.Focused()
	for _, c := range [][2]string{{"off", ""}, {"options", "no"}} {
		if e := f.Click(c[0], c[1]); e.Kind != "" || f.Focused() != before {
			t.Fatal("disabled click changed state", e, f.Focused())
		}
	}
	doc, _ := ui.CandidateTokens()
	raw, _ := doc.Palette("dark", "256")
	p, _ := ui.Resolve(raw)
	events, focusCalls := 0, 0
	view, _ := ui.NewFormView(f, p, func(ui.FormEvent) { events++ })
	view.SetRect(0, 0, 60, 20)
	screen := drawingScreen(t)
	view.Draw(screen)
	screen.Show()
	for y, row := range f.Layout(60, 20) {
		if row.Role == "disabled" {
			view.MouseHandler()(tview.MouseLeftClick, tcell.NewEventMouse(2, y, tcell.Button1, tcell.ModNone), func(tview.Primitive) { focusCalls++ })
		}
	}
	if events != 0 || focusCalls != 0 || f.Focused() != before {
		t.Fatal("disabled pointer reached active handlers", events, focusCalls, f.Focused())
	}
}

func TestDisabledStyleDistinctInEveryPaletteAfterShow(t *testing.T) {
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			doc, _ := ui.CandidateTokens()
			raw, _ := doc.Palette(theme, profile)
			p, _ := ui.Resolve(raw)
			view, _ := ui.NewRowsView(func(w, h int) []ui.ComponentLine {
				return []ui.ComponentLine{{Text: "Enabled", Role: "body"}, {Text: "Disabled", Role: "disabled"}}
			}, p)
			view.SetRect(0, 0, 30, 2)
			screen := drawingScreen(t)
			view.Draw(screen)
			screen.Show()
			activeFG, activeBG, activeAttr := outputCell(t, screen, 0, 0, "E").Decompose()
			disabledFG, disabledBG, disabledAttr := outputCell(t, screen, 0, 1, "D").Decompose()
			if activeBG != disabledBG || activeFG == disabledFG && activeAttr == disabledAttr {
				t.Fatal(theme, profile, "disabled indistinguishable")
			}
			if profile == "8" && disabledAttr&tcell.AttrDim == 0 {
				t.Fatal(theme, "missing 8-color Dim")
			}
			styler, _ := ui.New(theme, profile)
			fg, _, attrs := styler.Styles.DisabledStyle().Decompose()
			if fg != disabledFG || attrs&tcell.AttrDim != disabledAttr&tcell.AttrDim {
				t.Fatal("adapter mismatch", theme, profile)
			}
		}
	}
}
