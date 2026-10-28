// Database-free host for shared reusable components.
package main

import (
	"flag"
	"fmt"
	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
	"log"
	"strconv"
	"strings"
)

type demoRows struct {
	count int
	en    bool
}

func (s demoRows) Len() int { return s.count }
func (s demoRows) IndexOf(id string) int {
	n, e := strconv.Atoi(strings.TrimPrefix(id, "row-"))
	if e != nil || n < 0 || n >= s.count || id != fmt.Sprintf("row-%d", n) {
		return -1
	}
	return n
}
func (s demoRows) Row(n int) ui.GridRecord {
	if n < 0 || n >= s.count {
		return ui.GridRecord{}
	}
	name := fmt.Sprintf("Synthetic %d", n)
	if !s.en {
		name = fmt.Sprintf("합성 항목 %d", n)
	}
	return ui.GridRecord{ID: fmt.Sprintf("row-%d", n), Cells: map[string]string{"name": name, "value": fmt.Sprint(n * 10), "state": "ready"}, State: ui.ControlState{Disabled: n == 1, Edited: n == 3}}
}
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
	if *mode != "forms" && *mode != "collections" && *mode != "grid" {
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
	if *mode == "collections" {
		picker, _ := ui.NewSearchPicker([]ui.ListItem{{ID: "group", Label: text("언어", "Languages"), Separator: true}, {ID: "go", Label: "Go", Secondary: text("공통 공개 모듈", "Shared public module"), Icon: "◆", ASCIIIcon: "*", Shortcut: "G"}, {ID: "old", Label: text("비활성 항목", "Disabled item"), Disabled: true}, {ID: "rust", Label: "Rust", Secondary: text("공통 공개 crate", "Shared public crate"), Icon: "◆", ASCIIIcon: "*", Shortcut: "R"}})
		picker.List.Empty = text("결과 없음", "No results")
		picker.Handle("open", "", 1)
		view, err = ui.NewSearchPickerView(picker, palette, *ascii, func(e ui.ListEvent) { footer.SetText(e.Kind + ": " + e.ID + " " + e.Query) })
		if err != nil {
			log.Fatal(err)
		}
	}
	if *mode == "grid" {
		grid, _ := ui.NewGrid([]ui.GridColumn{{ID: "name", Label: text("이름", "Name"), Width: 28, Editable: true}, {ID: "value", Label: text("값", "Value"), Width: 16, Editable: true}, {ID: "state", Label: text("상태", "State"), Width: 16}}, demoRows{count: 100000, en: *lang == "en"})
		grid.Empty = text("결과 없음", "No results")
		view, err = ui.NewGridView(grid, palette, func(e ui.GridEvent) { footer.SetText(e.Kind + ": " + e.RowID + " / " + e.ColumnID) })
		if err != nil {
			log.Fatal(err)
		}
	}
	panel, _ := ui.NewPanelView(view, palette)
	panel.ASCII = *ascii
	panel.SetTitle(*mode)
	root := tview.NewFlex().SetDirection(tview.FlexRow).AddItem(header, 1, 0, false).AddItem(panel, 0, 1, true).AddItem(footer, 1, 0, false)
	app.SetInputCapture(func(e *tcell.EventKey) *tcell.EventKey {
		if *mode == "grid" && e.Key() == tcell.KeyCtrlC {
			if view.Key != nil {
				view.Key(e)
			}
			return nil
		}
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
