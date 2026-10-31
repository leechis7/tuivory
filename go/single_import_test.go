package tuivory_test

import (
	"testing"

	ui "github.com/leechis7/tuivory/go"
)

func TestSingleImportApplication(t *testing.T) {
	oldBorders, oldTheme := ui.GetBorders(), ui.GetWidgetStyles()
	defer ui.SetBorders(oldBorders)
	defer ui.SetWidgetStyles(oldTheme)
	borders := oldBorders
	borders.TopLeft = '+'
	borders.TopLeftFocus = '+'
	ui.SetBorders(borders)
	theme := oldTheme
	theme.PrimitiveBackgroundColor = ui.ColorNavy
	ui.SetWidgetStyles(theme)

	screen := ui.NewSimulationScreen("UTF-8")
	if err := screen.Init(); err != nil {
		t.Fatal(err)
	}
	defer screen.Fini()
	screen.SetSize(40, 12)
	form := ui.NewWidgetForm().AddInputField("Name", "한글", 10, nil, nil)
	form.SetBorder(true)
	text := ui.NewWidgetTextView().SetText("한글 é 😀")
	tree := ui.NewWidgetTreeView().SetRoot(ui.NewWidgetTreeNode("Root"))
	layout := ui.NewFlex().AddItem(form, 20, 0, true).AddItem(text, 0, 1, false)
	pages := ui.NewPages().AddPage("main", layout, true, true).AddPage("tree", tree, true, false)
	app := ui.NewApplication().SetScreen(screen).SetRoot(pages, true)
	var captured ui.InputEvent
	app.SetInputCapture(func(key *ui.EventKey) *ui.EventKey { captured = ui.InputFromKey(key); return key })
	app.GetInputCapture()(ui.NewEventKey(ui.KeyRune, 'c', ui.ModCtrl))
	if action, _ := captured.EditingAction(); action != "copy" {
		t.Fatal(captured)
	}
	app.SetMouseCapture(func(event *ui.EventMouse, action ui.MouseAction) (*ui.EventMouse, ui.MouseAction) {
		return event, action
	})
	mouse := ui.NewEventMouse(3, 2, ui.Button1, ui.ModShift)
	event, action := app.GetMouseCapture()(mouse, ui.MouseLeftDown)
	if got := ui.InputFromMouse(action, event); got.X != 3 || got.Y != 2 {
		t.Fatal(got)
	}

	form.SetRect(0, 0, 20, 8)
	form.Draw(screen)
	screen.Show()
	cells, _, _ := screen.GetContents()
	if len(cells[0].Runes) == 0 || cells[0].Runes[0] != '+' {
		t.Fatal("root configuration did not reach drawing")
	}
	app.SetFocus(text)
	if app.GetFocus() != text {
		t.Fatal("focus identity")
	}
	if ui.GetWidgetStyles().PrimitiveBackgroundColor != ui.ColorNavy {
		t.Fatal("global theme setter")
	}
	// Semantic constructors keep their original signatures alongside raw widgets.
	model, err := ui.NewForm([]ui.FormField{{ID: "name", Kind: "text", Value: "원문"}})
	if err != nil || model == nil {
		t.Fatal(err)
	}
	button, err := ui.NewButton("save", "Save")
	if err != nil || button == nil {
		t.Fatal(err)
	}
	if ui.NewWidgetButton("Save") == nil || ui.NewWidgetGrid() == nil || ui.NewWidgetList() == nil {
		t.Fatal("compatibility constructors")
	}
}

func TestSingleImportGlobalMapReplacement(t *testing.T) {
	old := ui.SemigraphicJoints
	defer ui.SetSemigraphicJoints(old)
	replacement := map[string]rune{"test": '+'}
	ui.SetSemigraphicJoints(replacement)
	replacement["test"] = '*'
	if ui.SemigraphicJoints["test"] != '*' {
		t.Fatal("root map lost the active shared entries")
	}
}
