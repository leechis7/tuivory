// A host composes menu controls and chooses global keys, eligibility and actions.
package main

import (
	"flag"
	"fmt"
	ui "github.com/leechis7/tuivory/go"

	"log"
)

type scene struct {
	*ui.Box
	background  ui.Primitive
	popup       *ui.ShadowView
	bar         *ui.RowsView
	menu        *ui.Menu
	drawPopup   func(ui.Screen)
	event       func(ui.MenuEvent)
	beforeMouse func()
	paste       func(string)
}

func (s *scene) HasFocus() bool { return s.background.HasFocus() || s.popup.HasFocus() }
func (s *scene) InputHandler() func(*ui.EventKey, func(ui.Primitive)) {
	return s.WrapInputHandler(func(e *ui.EventKey, focus func(ui.Primitive)) {
		if !s.menu.Opened() {
			if h := s.background.InputHandler(); h != nil {
				h(e, focus)
			}
		}
	})
}
func (s *scene) PasteHandler() func(string, func(ui.Primitive)) {
	return s.WrapPasteHandler(func(text string, focus func(ui.Primitive)) {
		if !s.menu.Opened() {
			if s.paste != nil {
				s.paste(text)
				return
			}
			if h := s.background.PasteHandler(); h != nil {
				h(text, focus)
			}
		}
	})
}
func (s *scene) Draw(screen ui.Screen) {
	x, y, w, h := s.GetRect()
	s.background.SetRect(x, y, w, h)
	s.background.Draw(screen)
	if s.menu.Opened() {
		s.drawPopup(screen)
	}
}
func (s *scene) MouseHandler() func(ui.MouseAction, *ui.EventMouse, func(ui.Primitive)) (bool, ui.Primitive) {
	return s.WrapMouseHandler(func(a ui.MouseAction, e *ui.EventMouse, focus func(ui.Primitive)) (bool, ui.Primitive) {
		x, y := e.Position()
		if s.menu.Opened() {
			if s.bar.InRect(x, y) {
				return s.bar.MouseHandler()(a, e, focus)
			}
			if s.popup.InRect(x, y) {
				return s.popup.MouseHandler()(a, e, focus)
			}
			if a == ui.MouseLeftClick || a == ui.MouseLeftDoubleClick {
				s.event(s.menu.Close())
			}
			return true, nil
		}
		if s.beforeMouse != nil {
			s.beforeMouse()
		}
		return s.background.MouseHandler()(a, e, focus)
	})
}
func main() {
	lang := flag.String("lang", "ko", "ko/en")
	theme := flag.String("theme", "dark", "theme")
	colors := flag.String("colors", "256", "color profile")
	ascii := flag.Bool("ascii", false, "ASCII menu glyphs")
	shadowFlag := flag.String("shadow", "off", "off/auto/solid/dim")
	flag.Parse()
	if *lang != "ko" && *lang != "en" {
		log.Fatal("invalid language")
	}
	tr := func(ko, en string) string {
		if *lang == "en" {
			return en
		}
		return ko
	}
	items := []ui.MenuItem{
		{ID: "file", Label: tr("파일", "File"), Mnemonic: "f"}, {ID: "new", Parent: "file", Label: tr("새 문서", "New document"), Mnemonic: "n", Shortcut: "Ctrl+N", Icon: "◇", ASCIIIcon: "*"}, {ID: "save", Parent: "file", Label: tr("저장 요청", "Save request"), Mnemonic: "s", Shortcut: "Ctrl+S", Disabled: true}, {ID: "sep", Parent: "file", Separator: true}, {ID: "recent", Parent: "file", Label: tr("최근 예제", "Recent examples"), Mnemonic: "r"}, {ID: "alpha", Parent: "recent", Label: tr("한글 예제와 긴 이름", "A long example name"), Secondary: "[red] literal", Mnemonic: "a"}, {ID: "more", Parent: "recent", Label: tr("다른 예제", "More examples"), Mnemonic: "m"}, {ID: "beta", Parent: "more", Label: "Unicode 界 😀 é", Mnemonic: "b"},
		{ID: "edit", Label: tr("편집", "Edit"), Mnemonic: "e"}, {ID: "clipboard", Parent: "edit", Label: tr("클립보드 요청", "Clipboard requests"), Mnemonic: "c"}, {ID: "copy", Parent: "clipboard", Label: tr("복사 요청", "Copy request"), Mnemonic: "c", Shortcut: "Ctrl+C"}, {ID: "paste", Parent: "clipboard", Label: tr("붙여넣기 요청", "Paste request"), Mnemonic: "p", Shortcut: "Ctrl+V"},
		{ID: "view", Label: tr("보기", "View"), Mnemonic: "v"}, {ID: "detail", Parent: "view", Label: tr("상세 요청", "Detail request"), Mnemonic: "d"},
	}
	menu, err := ui.NewMenu(items)
	if err != nil {
		log.Fatal(err)
	}
	menu.BackLabel = tr("뒤로", "Back")
	menu.EmptyLabel = tr("항목 없음", "No items")
	form, _ := ui.NewForm([]ui.FormField{{ID: "value", Kind: "text", Label: tr("값", "Value"), Value: tr("합성 문서", "Synthetic draft")}})
	doc, _ := ui.CandidateTokens()
	palette := func() ui.Palette {
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
	p := palette()
	app := ui.NewApplication()
	origin := "editor"
	var emit func(ui.MenuEvent)
	var refresh func()
	status := ui.NewWidgetTextView()
	header := ui.NewWidgetTextView()
	hints := ui.NewWidgetTextView()
	editor, _ := ui.NewFormView(form, p, func(e ui.FormEvent) { status.SetText(e.Kind + ": " + e.ID) })
	preview := ui.NewWidgetTextView().SetText(tr("앱이 선택한 내용·명령·화면 배치\n메뉴 항목은 실제 파일·DB·클립보드를 변경하지 않습니다.", "Host-owned content, commands and screen layout\nMenu items do not change files, databases or clipboard."))
	left, _ := ui.NewPanelView(editor, p)
	left.SetTitle(tr("편집 영역", "Editor"))
	right, _ := ui.NewPanelView(preview, p)
	right.SetTitle(tr("미리보기", "Preview"))
	menuView, _ := ui.NewMenuView(menu, p, *ascii, func(e ui.MenuEvent) { emit(e) })
	popup, _ := ui.NewPanelView(menuView, p)
	shadowOptions := ui.ShadowOptions{Mode: ui.ShadowMode(*shadowFlag)}
	shadow, err := ui.NewShadowView(popup, p, shadowOptions)
	if err != nil {
		log.Fatal(err)
	}
	bar, _ := ui.NewMenuBarView(menu, p, func(e ui.MenuEvent) {
		if e.Kind == "focus" && menu.Opened() {
			e = menu.Open(e.ID, menu.ReturnID())
		}
		emit(e)
	})
	activeOrigin := func() string {
		if preview.HasFocus() {
			return "preview"
		}
		if editor.HasFocus() {
			return "editor"
		}
		return origin
	}
	restore := func(id string) {
		origin = id
		if id == "preview" {
			app.SetFocus(preview)
		} else {
			app.SetFocus(editor)
		}
	}
	emit = func(e ui.MenuEvent) {
		if e.Kind == "" {
			return
		}
		if e.Kind == "open_request" {
			caller := activeOrigin()
			if menu.Opened() {
				caller = menu.ReturnID()
			}
			e = menu.Open(e.ID, caller)
		}
		if menu.Opened() {
			app.SetFocus(menuView)
		} else if e.ReturnID != "" {
			restore(e.ReturnID)
		}
		status.SetText(fmt.Sprintf("%s: %s / origin=%s", e.Kind, e.ID, e.ReturnID))
		refresh()
	}
	refresh = func() {
		p = palette()
		for _, e := range []error{editor.SetPalette(p), menuView.SetPalette(p), bar.SetPalette(p), popup.SetPalette(p), shadow.SetPalette(p), left.SetPalette(p), right.SetPalette(p)} {
			if e != nil {
				log.Fatal(e)
			}
		}
		menuView.ASCII = *ascii
		popup.ASCII = *ascii
		shadow.ASCII = *ascii
		left.ASCII = *ascii
		right.ASCII = *ascii
		title := menu.Title()
		if title == "" {
			title = tr("문맥 메뉴", "Context menu")
		}
		popup.SetTitle(title)
		for _, v := range []*ui.WidgetTextView{header, status, hints, preview} {
			v.SetTextColor(p["body"].FG).SetBackgroundColor(p["surface"].BG)
		}
		header.SetText("TUIVORY Menu / " + tr("컴포넌트와 앱의 명령 연결", "Components and host actions"))
		shadowHint := ""
		if *shadowFlag != "off" {
			shadowHint = tr("F6 그림자: ", "F6 shadow: ") + *shadowFlag + " · "
		}
		hints.SetText(shadowHint + tr("F10 메뉴 · Shift+F10 문맥 · Alt+F/E/V · F2 테마 F3 색상 F4 ASCII F5 사용 가능 상태 · Tab 영역 · Ctrl+Q 종료", "F10 menu / Shift+F10 context / Alt+F/E/V / F2 theme F3 colors F4 ASCII F5 eligibility / Tab panel / Ctrl+Q quit"))
	}
	body := ui.NewFlex().SetDirection(ui.FlexRow).AddItem(header, 1, 0, false).AddItem(bar, 1, 0, false).AddItem(left, 0, 1, true).AddItem(right, 0, 1, false).AddItem(status, 1, 0, false).AddItem(hints, 1, 0, false)
	root := &scene{Box: ui.NewBox(), background: body, popup: shadow, bar: bar, menu: menu, event: func(e ui.MenuEvent) { emit(e) }, beforeMouse: func() { origin = activeOrigin() }, paste: func(text string) {
		if activeOrigin() == "editor" {
			form.Handle("insert", text)
		}
	}}
	root.drawPopup = func(screen ui.Screen) {
		x, y, w, h := root.GetRect()
		anchor := ui.CellRect{X: x + 4, Y: y + 3, Width: 1, Height: 1}
		if path := menu.Path(); len(path) > 0 {
			for _, c := range menu.BarLayout(w).Cells {
				if c.ID == path[0] {
					anchor = ui.CellRect{X: x + c.Start, Y: y + 1, Width: c.Width, Height: 1}
				}
			}
		}
		mw, mh := menu.ContentSize()
		plan := ui.PopupPlacement(anchor, ui.CellRect{X: x, Y: y, Width: w, Height: h}, min(52, max(24, mw+4)), mh+4, shadowOptions)
		r := plan.Bounds
		shadow.SetRect(r.X, r.Y, r.Width, r.Height)
		shadow.Draw(screen)
	}
	cycle := func(s *string, values []string) {
		for n, v := range values {
			if v == *s {
				*s = values[(n+1)%len(values)]
				return
			}
		}
	}
	app.SetInputCapture(func(e *ui.EventKey) *ui.EventKey {
		switch e.Key() {
		case ui.KeyCtrlQ:
			app.Stop()
			return nil
		case ui.KeyF2:
			cycle(theme, []string{"dark", "light", "blackwhite"})
			refresh()
			return nil
		case ui.KeyF3:
			cycle(colors, []string{"8", "16", "256", "truecolor"})
			refresh()
			return nil
		case ui.KeyF4:
			*ascii = !*ascii
			refresh()
			return nil
		case ui.KeyF6:
			cycle(shadowFlag, []string{"off", "auto", "solid", "dim"})
			shadowOptions.Mode = ui.ShadowMode(*shadowFlag)
			if err := shadow.SetShadow(shadowOptions); err != nil {
				log.Fatal(err)
			}
			refresh()
			return nil
		case ui.KeyF5:
			items[2].Disabled = !items[2].Disabled
			ev, err := menu.SetItems(items)
			if err != nil {
				log.Fatal(err)
			}
			emit(ev)
			return nil
		case ui.KeyF10:
			if menu.Opened() {
				if e.Modifiers()&ui.ModShift != 0 {
					emit(menu.Open("", menu.ReturnID()))
				} else {
					emit(menu.Close())
				}
			} else {
				id := menu.BarFocusedID()
				if e.Modifiers()&ui.ModShift != 0 {
					id = ""
				}
				origin = activeOrigin()
				emit(menu.Open(id, origin))
			}
			return nil
		}
		if e.Key() == ui.KeyRune && e.Modifiers()&ui.ModAlt != 0 {
			emit(menu.HandleBar("mnemonic", string(e.Rune())))
			return nil
		}
		if menu.Opened() {
			a, v := ui.MenuKey(e)
			_, _, _, h := menuView.GetInnerRect()
			emit(menu.Handle(a, v, h))
			return nil
		}
		if e.Key() == ui.KeyTab {
			origin = activeOrigin()
			if origin == "editor" {
				restore("preview")
			} else {
				restore("editor")
			}
			return nil
		}
		return e
	})
	status.SetText(tr("명령 요청만 반환하며 실제 동작은 앱이 결정합니다.", "Menus emit requests; the host decides actual actions."))
	refresh()
	if err := app.SetRoot(root, true).SetFocus(editor).EnableMouse(true).EnablePaste(true).Run(); err != nil {
		log.Fatal(err)
	}
}
