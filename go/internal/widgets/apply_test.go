package widgets

import (
	"testing"

	"github.com/gdamore/tcell/v2"
	style "github.com/leechis7/tuivory/go/internal/style"
	"github.com/rivo/tview"
)

func TestApplyRecolorsHiddenWidgetsAndKeepsState(t *testing.T) {
	terminal := tcell.NewSimulationScreen("UTF-8")
	if err := terminal.Init(); err != nil {
		t.Fatal(err)
	}
	defer terminal.Fini()
	terminal.SetSize(100, 30)
	app := tview.NewApplication()
	input := tview.NewInputField().SetText("keep 한글")
	text := tview.NewTextView().SetText("one\ntwo\nthree\nfour").ScrollTo(2, 0)
	editor := tview.NewTextArea().SetText("unchanged source", false)
	choice := NewChoice("Choice", []string{"one", "two"}, 1, nil)
	form := tview.NewForm().AddFormItem(input).AddFormItem(choice).AddButton("Save", nil)
	node := tview.NewTreeNode("warning node")
	tree := tview.NewTreeView().SetRoot(node).SetCurrentNode(node)
	list := tview.NewList().AddItem("one", "", 0, nil).AddItem("two", "", 0, nil).SetCurrentItem(1)
	hidden := tview.NewFlex().AddItem(text, 5, 0, false).AddItem(editor, 5, 0, false).AddItem(tree, 5, 0, false).AddItem(list, 5, 0, false)
	pages := tview.NewPages().AddPage("visible", form, true, true).AddPage("hidden", hidden, true, false)
	app.SetFocus(input)
	roles := Roles{Surfaces: map[*tview.Box]style.Surface{text.Box: style.Panel}, Text: map[*tview.TextView]style.TextRole{text: style.Warning}, Tree: map[*tview.TreeNode]style.TextRole{node: style.Warning}}
	for _, theme := range []string{"dark", "light", "blackwhite", "dark"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			s, err := New(theme, profile)
			if err != nil {
				t.Fatal(err)
			}
			s.Apply(roles, pages)
			if input.GetText() != "keep 한글" || editor.GetText() != "unchanged source" || list.GetCurrentItem() != 1 || app.GetFocus() != input {
				t.Fatal("apply changed app state")
			}
			if current, _ := choice.GetCurrentOption(); current != 1 {
				t.Fatal("apply changed choice")
			}
			if row, col := text.GetScrollOffset(); row != 2 || col != 0 {
				t.Fatal("apply changed scroll")
			}
			if text.GetBackgroundColor() != s.Styles.Surface || editor.GetBackgroundColor() != s.Styles.Editor || tree.GetBackgroundColor() != s.Styles.Background {
				t.Fatal("hidden widget not recolored")
			}
			name, _ := pages.GetFrontPage()
			if name != "visible" {
				t.Fatal("apply switched page")
			}
			if len(roles.Surfaces) != 1 {
				t.Fatal("apply mutated host role bindings")
			}
			form.SetRect(0, 0, 90, 20)
			form.Draw(terminal)
			if input.GetText() != "keep 한글" {
				t.Fatal("drawing changed form data")
			}
		}
	}
}

func TestChoiceRetainsOwnStyleAndClearsWideGlyph(t *testing.T) {
	terminal := tcell.NewSimulationScreen("UTF-8")
	if err := terminal.Init(); err != nil {
		t.Fatal(err)
	}
	defer terminal.Fini()
	terminal.SetSize(20, 5)
	base := tcell.StyleDefault.Foreground(tcell.ColorWhite).Background(tcell.ColorBlack)
	terminal.SetContent(0, 0, '한', nil, base)
	overlay := choiceOverlayScreen{Screen: terminal}
	overlay.SetContent(1, 0, 'x', nil, base)
	r, _, _, _ := terminal.GetContent(0, 0)
	if r != ' ' {
		t.Fatal("leading half of wide glyph leaked")
	}
	for _, theme := range []string{"dark", "light", "blackwhite"} {
		for _, profile := range []string{"8", "16", "256", "truecolor"} {
			s, err := New(theme, profile)
			if err != nil {
				t.Fatal(err)
			}
			choice := NewChoice("", []string{"abc", "def"}, 0, nil)
			s.Choice(choice)
			choice.SetFormAttributes(0, tcell.ColorWhite, tcell.ColorBlack, tcell.ColorRed, tcell.ColorRed)
			choice.SetRect(0, 0, 10, 1)
			choice.Draw(terminal)
			_, _, actual, _ := terminal.GetContent(0, 0)
			fg, bg, _ := actual.Decompose()
			wantFG, wantBG, _ := s.Styles.DropDownStyle().Decompose()
			if fg != wantFG || bg != wantBG {
				t.Fatalf("form overwrote choice: %s/%s", theme, profile)
			}
		}
	}
}
