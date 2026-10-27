// Database-free application importing Tuivory's public tree API.
package main

import (
	"flag"
	"fmt"
	"log"

	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
)

func main() {
	lang := flag.String("lang", "ko", "ko or en")
	theme := flag.String("theme", "dark", "dark, light, blackwhite")
	colors := flag.String("colors", "256", "8, 16, 256, truecolor")
	ascii := flag.Bool("ascii", false, "ASCII arrows and icons")
	flag.Parse()
	if *lang != "ko" && *lang != "en" {
		log.Fatal("--lang requires ko or en")
	}
	text := func(ko, en string) string {
		if *lang == "en" {
			return en
		}
		return ko
	}
	count := uint64(3)
	tree, err := ui.NewTree([]ui.TreeNode{
		{ID: "workspace", Name: text("작업 공간", "Workspace"), Icon: "◇", ASCIIIcon: "R", Secondary: text("DB 없는 견본", "Database-free sample")},
		{ID: "examples", Parent: "workspace", Name: text("예제", "Examples"), Icon: "□", ASCIIIcon: "D", Count: &count},
		{ID: "go", Parent: "examples", Name: "Go", Secondary: text("공개 패키지", "Public package"), Icon: "·", ASCIIIcon: "F"},
		{ID: "rust", Parent: "examples", Name: "Rust", Secondary: text("공개 crate", "Public crate"), Icon: "·", ASCIIIcon: "F"},
		{ID: "long", Parent: "examples", Name: text("매우 긴 한글 이름과 English 표시 셀 스크롤 예시", "A very long name demonstrating terminal cell scrolling"), Icon: "·", ASCIIIcon: "F"},
		{ID: "lazy", Parent: "workspace", Name: text("아직 불러오지 않은 항목", "Unloaded items"), Branch: true, Secondary: text("펼침 이벤트만 반환", "Returns an expansion event")},
		{ID: "notes", Name: text("참고", "Notes"), Secondary: "[red] literal text", Icon: "□", ASCIIIcon: "F"},
	})
	if err != nil {
		log.Fatal(err)
	}
	state := &ui.TreeState{Expanded: map[string]bool{"workspace": true, "examples": true}}
	doc, _ := ui.CandidateTokens()
	paletteFor := func() ui.Palette {
		raw, e := doc.Palette(*theme, *colors)
		if e != nil {
			log.Fatal(e)
		}
		p, e := ui.Resolve(raw)
		if e != nil {
			log.Fatal(e)
		}
		return p
	}
	view, err := ui.NewTreeView(tree, state, paletteFor())
	if err != nil {
		log.Fatal(err)
	}
	view.ASCII = *ascii
	view.SetTitle(text(" 트리 ", " Tree "))
	header := tview.NewTextView().SetDynamicColors(false)
	footer := tview.NewTextView().SetDynamicColors(false)
	button := tview.NewButton(text("포커스 비교: Enter", "Focus comparison: Enter"))
	app := tview.NewApplication()
	status := text("이름 · 보조 설명 · 개수", "Name · Secondary · Count")
	refresh := func() {
		p := paletteFor()
		if err := view.SetPalette(p); err != nil {
			log.Fatal(err)
		}
		header.SetText(fmt.Sprintf("TUIVORY Tree · %s / %s\n%s", *theme, *colors, status)).SetTextColor(p["body"].FG).SetBackgroundColor(p["surface"].BG)
		footer.SetText(text("방향키 탐색 · Space 펼침 · Enter 실행 · Alt+←/→ 가로 이동\nTab 포커스 · F2 테마 · F3 색상 · F4 ASCII · Ctrl+Q 종료", "Arrows navigate · Space expand · Enter activate · Alt+Left/Right pan\nTab focus · F2 theme · F3 colors · F4 ASCII · Ctrl+Q quit")).SetTextColor(p["hint"].FG).SetBackgroundColor(p["surface"].BG)
		button.SetStyle(p["body"].Style()).SetActivatedStyle(p["selection"].Style())
	}
	view.OnEvent = func(event ui.TreeEvent) { status = fmt.Sprintf("%s: %s", event.Kind, event.ID); refresh() }
	button.SetSelectedFunc(func() {
		status = text("선택은 유지되고 입력 포커스만 이동합니다.", "Selection persists independently of input focus.")
		refresh()
	})
	root := tview.NewFlex().SetDirection(tview.FlexRow).AddItem(header, 2, 0, false).AddItem(view, 0, 1, true).AddItem(button, 1, 0, false).AddItem(footer, 2, 0, false)
	themes := []string{"dark", "light", "blackwhite"}
	profiles := []string{"8", "16", "256", "truecolor"}
	cycle := func(value *string, options []string) {
		for i, item := range options {
			if *value == item {
				*value = options[(i+1)%len(options)]
				return
			}
		}
	}
	app.SetInputCapture(func(e *tcell.EventKey) *tcell.EventKey {
		switch e.Key() {
		case tcell.KeyCtrlQ:
			app.Stop()
			return nil
		case tcell.KeyTab, tcell.KeyBacktab:
			if view.HasFocus() {
				app.SetFocus(button)
			} else {
				app.SetFocus(view)
			}
			return nil
		case tcell.KeyF2:
			cycle(theme, themes)
			refresh()
			return nil
		case tcell.KeyF3:
			cycle(colors, profiles)
			refresh()
			return nil
		case tcell.KeyF4:
			view.ASCII = !view.ASCII
			return nil
		}
		return e
	})
	refresh()
	if err := app.SetRoot(root, true).SetFocus(view).EnableMouse(true).Run(); err != nil {
		log.Fatal(err)
	}
}
