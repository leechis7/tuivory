package widgets

import (
	"testing"

	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

func TestFormReapplyPreservesStateAndReadOnlyText(t *testing.T) {
	terminal := tcell.NewSimulationScreen("UTF-8")
	if err := terminal.Init(); err != nil {
		t.Fatal(err)
	}
	defer terminal.Fini()
	terminal.SetSize(90, 20)
	form := tview.NewForm().AddTextView("", "Read-only 안내문", 0, 2, true, false).
		AddInputField("Name", "keep 한글", 20, nil, nil).AddCheckbox("Enabled", true, nil).AddButton("Save", nil)
	input := form.GetFormItem(1).(*tview.InputField)
	check := form.GetFormItem(2).(*tview.Checkbox)
	form.SetFocus(1)
	for _, theme := range []string{"dark", "light", "blackwhite", "dark"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			s, err := New(theme, profile)
			if err != nil {
				t.Fatal(err)
			}
			s.Form(form)
			form.SetRect(0, 0, 90, 20)
			terminal.Clear()
			form.Draw(terminal)
			if input.GetText() != "keep 한글" || !check.IsChecked() {
				t.Fatal("style changed user data")
			}
			item, button := form.GetFocusedItemIndex()
			if item != 1 || button != -1 {
				t.Fatal("style moved form focus")
			}
			found := false
			for y := 0; y < 20; y++ {
				for x := 0; x < 90; x++ {
					r, _, st, _ := terminal.GetContent(x, y)
					if r == 'R' {
						fg, bg, _ := st.Decompose()
						if fg != s.Styles.Text || bg != s.Styles.Surface {
							t.Fatalf("read-only form colors leaked: %s/%s", theme, profile)
						}
						found = true
					}
				}
			}
			if !found {
				t.Fatal("read-only text not drawn")
			}
		}
	}
}
