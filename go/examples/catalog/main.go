// Database-free host for shared reusable components.
package main

import (
	"flag"
	"fmt"
	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
	"log"
)

func main() {
	lang := flag.String("lang", "ko", "ko/en")
	theme := flag.String("theme", "dark", "theme")
	colors := flag.String("colors", "256", "color profile")
	ascii := flag.Bool("ascii", false, "ASCII borders")
	mode := flag.String("mode", "forms", "component")
	flag.Parse()
	if *lang != "ko" && *lang != "en" {
		log.Fatal("invalid language")
	}
	text := func(ko, en string) string {
		if *lang == "en" {
			return en
		}
		return ko
	}
	if *mode != "forms" {
		log.Fatal("unknown component")
	}
	options := []ui.FormOption{{ID: "fast", Label: text("빠르게", "Fast")}, {ID: "old", Label: text("사용 불가", "Unavailable"), Disabled: true}, {ID: "safe", Label: text("안전하게", "Safe")}}
	form, err := ui.NewForm([]ui.FormField{{ID: "name", Kind: "text", Label: text("이름", "Name"), Help: text("필수 입력", "Required"), Required: true}, {ID: "notes", Kind: "textarea", Label: text("메모", "Notes"), Value: text("합성 데이터", "Synthetic data")}, {ID: "read", Kind: "text", Label: text("읽기 전용", "Read-only"), Value: "Tuivory", State: ui.ControlState{ReadOnly: true}}, {ID: "agree", Kind: "checkbox", Label: text("동의", "Agree"), Required: true}, {ID: "radio", Kind: "radio", Label: text("방식", "Method"), Options: options, Choice: "fast"}, {ID: "select", Kind: "select", Label: text("선택", "Choice"), Options: options, Choice: "fast"}, {ID: "submit", Kind: "button", Label: text("제출", "Submit"), Action: "submit"}, {ID: "cancel", Kind: "button", Label: text("취소", "Cancel"), Action: "cancel"}})
	if err != nil {
		log.Fatal(err)
	}
	doc, _ := ui.CandidateTokens()
	source, err := doc.Palette(*theme, *colors)
	if err != nil {
		log.Fatal(err)
	}
	palette, _ := ui.Resolve(source)
	app := tview.NewApplication()
	header := tview.NewTextView().SetText("TUIVORY Catalog / " + text("이름 · 공통 컴포넌트", "Name / shared components"))
	footer := tview.NewTextView()
	footer.SetText(text("Tab 이동 / Enter 확정 / Esc 취소 / Ctrl+Q 종료", "Tab move / Enter confirm / Esc cancel / Ctrl+Q quit"))
	view, err := ui.NewFormView(form, palette, func(e ui.FormEvent) {
		footer.SetText(fmt.Sprintf("%s: %s", e.Kind, e.ID))
		if e.Kind == "invalid" {
			for _, id := range e.Missing {
				form.SetFeedback(id, "", text("입력 내용을 확인하세요", "Check this value"))
			}
		}
		if e.Kind == "change" {
			form.SetFeedback(e.ID, "", "")
		}
	})
	if err != nil {
		log.Fatal(err)
	}
	panel, _ := ui.NewPanelView(view, palette)
	panel.ASCII = *ascii
	panel.SetTitle(text("입력·폼", "Inputs and forms"))
	root := tview.NewFlex().SetDirection(tview.FlexRow).AddItem(header, 1, 0, false).AddItem(panel, 0, 1, true).AddItem(footer, 1, 0, false)
	app.SetInputCapture(func(e *tcell.EventKey) *tcell.EventKey {
		if e.Key() == tcell.KeyCtrlQ {
			app.Stop()
			return nil
		}
		return e
	})
	if err := app.SetRoot(root, true).SetFocus(view).EnableMouse(true).Run(); err != nil {
		log.Fatal(err)
	}
}
