package tuivory_test

import (
	"fmt"
	"testing"

	tcell "github.com/leechis7/tuivory/go/terminal"
	"github.com/leechis7/tuivory/go"
	tview "github.com/leechis7/tuivory/go/ui"
)

// Exercise the public contract using only the root TUIVORY import, including types
// that appear in callback signatures and host role bindings.
func TestSingleImportWorkflow(t *testing.T) {
	input := tview.NewInputField().SetText("keep 한글")
	choice := tuivory.NewChoice("Choice", []string{"one", "two"}, 1, nil)
	form := tview.NewForm().AddFormItem(input).AddFormItem(choice)
	message := tview.NewTextView().SetText("warning")
	pages := tview.NewPages().AddPage("form", form, true, true).AddPage("message", message, true, false)
	roles := tuivory.Roles{
		Surfaces: map[*tview.Box]tuivory.Surface{message.Box: tuivory.Panel},
		Text:     map[*tview.TextView]tuivory.TextRole{message: tuivory.Warning},
	}
	grid := tview.NewTable().SetCell(0, 0, tview.NewTableCell("Header")).SetCell(1, 0, tview.NewTableCell("value"))
	grid.Select(1, 0)
	for _, theme := range []string{"dark", "light", "blackwhite", "dark"} {
		styler, err := tuivory.New(theme, "256")
		if err != nil {
			t.Fatal(err)
		}
		styler.Apply(roles, pages)
		styler.Grid(grid, func(row, col int) tuivory.CellState { return tuivory.CellState{Edited: true} })
		if input.GetText() != "keep 한글" {
			t.Fatal("theme changed input")
		}
		if selected, _ := choice.GetCurrentOption(); selected != 1 {
			t.Fatal("theme changed selection")
		}
		if message.GetBackgroundColor() != styler.Styles.Surface {
			t.Fatal("hidden page was not restyled")
		}
		st := styler.Styles.SyntaxStyle(tuivory.SyntaxKeyword, styler.Styles.EditorStyle())
		fg, bg, _ := st.Decompose()
		if !fg.Valid() || !bg.Valid() {
			t.Fatal("unresolved syntax style")
		}
	}
	document, err := tuivory.ParseTokens([]byte(tuivory.CandidateTokensJSON()))
	if err != nil {
		t.Fatal(err)
	}
	palette, err := document.Palette("light", "16")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := tuivory.Resolve(palette); err != nil {
		t.Fatal(err)
	}
	if _, err := tuivory.New("unknown", "256"); err == nil {
		t.Fatal("accepted invalid theme")
	}
}

func ExampleNew() {
	theme, err := tuivory.New("dark", "256")
	if err != nil {
		panic(err)
	}
	fmt.Println(theme.Styles.Theme(), theme.Styles.Profile())
	// Output: dark 256
}

func TestRootStyleAndTokenAccess(t *testing.T) {
	profile := tuivory.ProfileForColors(16, false)
	styles, err := tuivory.NewStyles("light", profile)
	if err != nil {
		t.Fatal(err)
	}
	color := tuivory.BorderColor("light", profile, styles, true, styles.Field)
	if color == tcell.ColorDefault {
		t.Fatal("unresolved border")
	}
	document, err := tuivory.CandidateTokens()
	if err != nil || document.Format != tuivory.TokenFormat {
		t.Fatal("candidate unavailable", err)
	}
}
