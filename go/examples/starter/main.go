// DB-free starter template using the TUIVORY styles extracted from LazyOra.
package main

import (
	"fmt"
	"os"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
)

func main() {
	app := tview.NewApplication()
	themes := []string{"dark", "light", "blackwhite"}
	index := 0
	form := tview.NewForm().AddTextView("TUIVORY", "F2 테마 변경 · Ctrl+Q 종료", 40, 2, true, false).
		AddInputField("이름", "", 24, nil, nil).AddCheckbox("사용", true, nil).
		AddButton("종료", func() { app.Stop() })
	form.SetBorder(true).SetTitle(" Go starter · LazyOra style ")
	apply := func() {
		// Explicit profile keeps this template deterministic; the host can use
		// tuivory.ProfileForColors(screen.Colors(), limited) when it owns a screen.
		s, err := tuivory.New(themes[index], "256")
		if err != nil {
			panic(err)
		}
		s.Form(form)
	}
	apply()
	app.SetInputCapture(func(event *tcell.EventKey) *tcell.EventKey {
		switch event.Key() {
		case tcell.KeyCtrlQ:
			app.Stop()
			return nil
		case tcell.KeyF2:
			index = (index + 1) % len(themes)
			apply()
			return nil
		}
		return event
	})
	if err := app.SetRoot(form, true).Run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
