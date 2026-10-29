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
	gridPreset := flag.String("grid-preset", "simple", "simple/data")
	gridSample := flag.Bool("grid-sample", false, "five-row grid comparison")
	mode := flag.String("mode", "forms", "component")
	densityFlag := flag.String("density", "auto", "auto/compact/comfortable")
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
	if *mode != "forms" && *mode != "collections" && *mode != "grid" && *mode != "feedback" && *mode != "layout" {
		log.Fatal("unknown component")
	}
	options := []ui.FormOption{{ID: "fast", Label: text("빠르게", "Fast")}, {ID: "old", Label: text("사용 불가", "Unavailable"), Disabled: true}, {ID: "safe", Label: text("안전하게", "Safe")}}
	form, err := ui.NewForm([]ui.FormField{{ID: "name", Kind: "text", Label: text("이름", "Name"), Help: text("필수 입력", "Required"), Required: true}, {ID: "notes", Kind: "textarea", Label: text("메모", "Notes"), Value: text("합성 데이터", "Synthetic data")}, {ID: "read", Kind: "text", Label: text("읽기 전용", "Read-only"), Value: "Tuivory", State: ui.ControlState{ReadOnly: true}}, {ID: "locked", Kind: "text", Label: text("비활성 입력", "Disabled input"), Value: "Tuivory", State: ui.ControlState{Disabled: true}}, {ID: "save", Kind: "button", Label: text("저장 불가", "Save unavailable"), State: ui.ControlState{Disabled: true}}, {ID: "agree", Kind: "checkbox", Label: text("동의", "Agree"), Required: true}, {ID: "radio", Kind: "radio", Label: text("방식", "Method"), Options: options, Choice: "fast"}, {ID: "select", Kind: "select", Label: text("선택", "Choice"), Options: options, Choice: "fast"}, {ID: "submit", Kind: "button", Label: text("제출", "Submit"), Action: "submit"}, {ID: "cancel", Kind: "button", Label: text("취소", "Cancel"), Action: "cancel"}})
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
		if *gridSample {
			grid = sampleGrid(text)
		}
		gridOptions, e := ui.GridPreset(*gridPreset)
		if e != nil {
			log.Fatal(e)
		}
		gridOptions.ASCII = *ascii
		if *densityFlag != "auto" {
			gridOptions, e = gridOptions.WithDensity(*densityFlag)
			if e != nil {
				log.Fatal(e)
			}
		}
		if e = grid.SetOptions(gridOptions); e != nil {
			log.Fatal(e)
		}
		configureGrid(grid, text)
		grid.Empty = text("결과 없음", "No results")
		view, err = ui.NewGridView(grid, palette, func(e ui.GridEvent) { footer.SetText(e.Kind + ": " + e.RowID + " / " + e.ColumnID) })
		if err != nil {
			log.Fatal(err)
		}
	}
	if *mode == "feedback" {
		queue, _ := ui.NewNoticeQueue(8)
		_ = queue.Push(ui.Notice{ID: "saved", Text: text("임시 알림", "Transient notice"), Severity: "success", ExpiresAt: 5})
		_ = queue.Push(ui.Notice{ID: "error", Text: text("연결 실패", "Connection failed"), Detail: text("재시도가 필요합니다", "Retry is available"), Severity: "error", ExpiresAt: 1, Actions: []ui.NoticeAction{{ID: "retry", Label: text("재시도", "Retry")}}})
		progress := &ui.Progress{ID: "load", Label: text("합성 작업", "Synthetic operation"), Status: "loading", Current: 50, Total: 100, Cancellable: true, CancelLabel: text("c 취소 요청", "c request cancellation")}
		now := uint64(0)
		height := 1
		view, err = ui.NewRowsView(func(w, h int) []ui.ComponentLine {
			height = h
			return feedbackRows(queue, progress, w, h, now, *lang == "en")
		}, palette)
		if err != nil {
			log.Fatal(err)
		}
		emit := func(e ui.NoticeEvent) {
			if e.Kind == "" {
				return
			}
			footer.SetText(e.Kind + ": " + e.ID + " / " + e.Action)
			if e.Kind == "dismiss" {
				queue.Dismiss(e.ID)
			}
			if e.Kind == "cancel" {
				progress.Status = "cancelled"
				progress.Message = text("앱이 취소를 처리했습니다", "The host handled cancellation")
			}
		}
		view.Key = func(key *tcell.EventKey) {
			if key.Key() == tcell.KeyRune && key.Rune() == 'c' {
				emit(progress.RequestCancel())
				return
			}
			if key.Key() == tcell.KeyRune && key.Rune() == 't' {
				now = 100
				queue.Expire(now)
				emit(ui.NoticeEvent{Kind: "expired"})
				return
			}
			action := ui.NavigationKey(key)
			if key.Key() == tcell.KeyDelete {
				action = "dismiss"
			}
			emit(queue.Handle(action, now, max(1, height-4)))
		}
		view.Click = func(line ui.ComponentLine) {
			for _, n := range queue.Visible(now) {
				if n.ID == line.ID {
					queue.Focused = n.ID
				}
			}
		}
	}
	if *mode == "layout" {
		density := ui.Density(*densityFlag)
		if _, e := ui.ResolveSpacing(density, 120); e != nil {
			log.Fatal(e)
		}
		removed, helpOpen := false, false
		view, err = ui.NewRowsView(func(w, h int) []ui.ComponentLine {
			return layoutDemoRows(w, h, density, removed, helpOpen, *lang == "en")
		}, palette)
		if err != nil {
			log.Fatal(err)
		}
		view.Key = func(key *tcell.EventKey) {
			if key.Key() == tcell.KeyF1 {
				helpOpen = !helpOpen
				return
			}
			if helpOpen {
				if key.Key() == tcell.KeyEscape {
					helpOpen = false
				}
				return
			}
			if key.Key() == tcell.KeyRune && key.Rune() == 'x' {
				event := (ui.Chip{ID: "filter", Removable: true}).RequestRemove()
				if event.Kind != "" {
					removed = true
					footer.SetText(event.Kind + ": " + event.ID)
				}
			}
			if key.Key() == tcell.KeyRune && key.Rune() == 'd' {
				if density == ui.DensityCompact {
					density = ui.DensityComfortable
				} else {
					density = ui.DensityCompact
				}
				footer.SetText("density: " + string(density))
			}
		}
	}
	panel, _ := ui.NewPanelView(view, palette)
	panel.ASCII = *ascii
	panel.SetTitle(*mode)
	root := tview.NewFlex().SetDirection(tview.FlexRow).AddItem(header, 1, 0, false).AddItem(panel, 0, 1, true).AddItem(footer, 1, 0, false)
	app.SetInputCapture(func(e *tcell.EventKey) *tcell.EventKey {
		if e.Key() == tcell.KeyF2 || e.Key() == tcell.KeyF3 {
			if e.Key() == tcell.KeyF2 {
				values := []string{"dark", "light", "blackwhite"}
				for i, v := range values {
					if *theme == v {
						*theme = values[(i+1)%len(values)]
						break
					}
				}
			} else {
				values := []string{"8", "16", "256", "truecolor"}
				for i, v := range values {
					if *colors == v {
						*colors = values[(i+1)%len(values)]
						break
					}
				}
			}
			source, e := doc.Palette(*theme, *colors)
			if e != nil {
				log.Fatal(e)
			}
			palette, _ = ui.Resolve(source)
			if e = view.SetPalette(palette); e != nil {
				log.Fatal(e)
			}
			_ = panel.SetPalette(palette)
			header.SetTextColor(palette["body"].FG).SetBackgroundColor(palette["surface"].BG)
			footer.SetTextColor(palette["hint"].FG).SetBackgroundColor(palette["surface"].BG)
			return nil
		}

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

func feedbackRows(queue *ui.NoticeQueue, progress *ui.Progress, w, h int, now uint64, en bool) []ui.ComponentLine {
	if h <= 0 {
		return nil
	}
	rows := queue.Layout(w, max(1, h-4), now)
	if len(rows) == 0 {
		message := "알림 없음"
		if en {
			message = "No pending notices"
		}
		rows = ui.DataState{Kind: "empty", Text: message}.Layout(w)
	}
	rows = append(rows, ui.ComponentLine{Role: "hint"})
	return append(rows, progress.Layout(w, now)...)
}

func layoutHelp(en bool) *ui.Help {
	tr := func(ko, english string) string {
		if en {
			return english
		}
		return ko
	}
	help, _ := ui.NewHelp([]ui.Shortcut{{Key: "Ctrl+Q", Text: tr("종료", "Quit"), Priority: 100}, {Key: "F1/Esc", Text: tr("도움말 열기/복귀", "Open help / return"), Priority: 90}, {Key: "x", Text: tr("필터 제거 요청", "Request filter removal"), Priority: 80}, {Key: "d", Text: tr("밀도 전환", "Change density"), Priority: 70}})
	return help
}
func layoutDemoRows(w, h int, density ui.Density, removed, helpOpen, en bool) []ui.ComponentLine {
	if helpOpen {
		return layoutHelp(en).Layout(w, h)
	}
	if w <= 0 || h <= 0 {
		return nil
	}
	tokens, _ := ui.ResolveSpacing(density, w)
	rects, hidden, _ := ui.StackRects(ui.CellRect{Width: w, Height: max(0, h-2)}, []ui.StackItem{{ID: "main", Min: 12, Preferred: 40, Weight: 1}, {ID: "aside", Min: 10, Preferred: 24}}, tokens, false)
	rows := make([]ui.ComponentLine, h)
	for i := range rows {
		rows[i].Role = "surface"
	}
	add := func(y, x, width int, text, role string) {
		if y < 0 || y >= h || width <= 0 {
			return
		}
		rows[y].Spans = append(rows[y].Spans, ui.ComponentSpan{Start: x, Width: width, Text: text, Role: role})
	}
	tr := func(ko, english string) string {
		if en {
			return english
		}
		return ko
	}
	count := uint64(145)
	for _, slot := range rects {
		r := slot.Rect
		if r.Width == 0 || r.Height == 0 {
			continue
		}
		add(r.Y, r.X, r.Width, "[ "+slot.ID+" ]", "header")
		if slot.ID == "main" {
			badge := ui.Badge{ID: "count", Label: tr("작업", "Tasks"), Count: &count}
			line := badge.Line(r.Width)
			if r.Height > 1 {
				add(r.Y+1, r.X, r.Width, line.Text, line.Role)
			}
			if !removed && r.Height > 2 {
				chip := ui.Chip{ID: "filter", Label: tr("검토 필터", "Review filter"), Removable: true, State: ui.ControlState{Selected: true}}
				line = chip.Line(r.Width)
				add(r.Y+2, r.X, r.Width, line.Text, line.Role)
				rows[r.Y+2].ID = "filter"
			}
		} else {
			for i, line := range layoutHelp(en).Layout(r.Width, max(0, r.Height-1)) {
				add(r.Y+1+i, r.X, r.Width, line.Text, line.Role)
			}
		}
	}
	placement := ui.DrawerLayout(ui.CellRect{Width: w, Height: h}, 24, 40)
	rows[h-1] = ui.ComponentLine{Text: ui.CellText(fmt.Sprintf("density=%s gap=%d padding=%d hidden=%d overlay=%t", density, tokens.Gap, tokens.Padding, len(hidden), placement.Overlay), w), Role: "hint"}
	return rows
}
