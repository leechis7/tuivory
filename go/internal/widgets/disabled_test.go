package widgets

import (
	"testing"

	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

func TestDisabledDropDownAfterShowAndReapply(t *testing.T) {
	screen := tcell.NewSimulationScreen("UTF-8")
	if err := screen.Init(); err != nil {
		t.Fatal(err)
	}
	defer screen.Fini()
	screen.SetSize(40, 4)
	for _, kind := range []string{"dropdown", "choice", "form"} {
		t.Run(kind, func(t *testing.T) {
			drop := tview.NewDropDown().SetOptions([]string{"Retained"}, nil).SetCurrentOption(0).SetFieldWidth(16)
			drop.SetDisabled(true)
			choice := NewChoice("", []string{"Retained"}, 0, nil)
			if kind == "choice" {
				drop = choice.DropDown
				drop.SetDisabled(true)
			}
			form := tview.NewForm().AddFormItem(drop)
			for _, theme := range []string{"dark", "light", "blackwhite", "dark"} {
				for _, profile := range []string{"8", "16", "256", "truecolor"} {
					styler, _ := New(theme, profile)
					var view tview.Primitive = drop
					switch kind {
					case "choice":
						styler.Choice(choice)
						view = choice
					case "form":
						styler.Form(form)
						form.SetBorderPadding(0, 0, 0, 0)
						view = form
					default:
						styler.DropDown(drop)
					}
					view.SetRect(0, 0, 40, 4)
					screen.Clear()
					view.Draw(screen)
					screen.Show()
					cells, _, _ := screen.GetContents()
					found := false
					for _, cell := range cells {
						if len(cell.Runes) == 0 || cell.Runes[0] != 'R' {
							continue
						}
						found = true
						fg, bg, attrs := cell.Style.Decompose()
						wantFG, wantBG, wantAttrs := styler.Styles.DisabledStyle().Decompose()
						if fg != wantFG || bg != wantBG || attrs&tcell.AttrDim != wantAttrs&tcell.AttrDim {
							t.Errorf("%s/%s: disabled option %v/%v attrs=%v, want %v/%v attrs=%v", theme, profile, fg, bg, attrs, wantFG, wantBG, wantAttrs)
						}
						break
					}
					if !found {
						t.Fatal("disabled value disappeared")
					}
					focusCalls := 0
					drop.InputHandler()(tcell.NewEventKey(tcell.KeyEnter, 0, 0), func(tview.Primitive) { focusCalls++ })
					drop.MouseHandler()(tview.MouseLeftClick, tcell.NewEventMouse(2, 0, tcell.Button1, 0), func(tview.Primitive) { focusCalls++ })
					if focusCalls != 0 || drop.IsOpen() {
						t.Fatal("disabled dropdown accepted interaction")
					}
				}
			}
		})
	}

}
