// Database-free composition through public controls and layout containers.
package main

import (
	"flag"
	ui "github.com/leechis7/tuivory/go"

	"log"
)

func main() {
	lang := flag.String("lang", "ko", "ko/en")
	theme := flag.String("theme", "dark", "theme")
	profile := flag.String("colors", "256", "profile")
	ascii := flag.Bool("ascii", false, "ASCII ornaments")
	opened := flag.Bool("open", false, "open modal")
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
	palette := func() ui.Palette {
		doc, e := ui.CandidateTokens()
		if e != nil {
			log.Fatal(e)
		}
		raw, e := doc.Palette(*theme, *profile)
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
	status := tr("명령은 요청만 전달합니다.", "Actions emit requests only.")
	form, e := ui.NewForm([]ui.FormField{{ID: "name", Kind: "text", Label: tr("이름", "Name"), Value: tr("예제 사용자", "Example user")}, {ID: "password", Kind: "password", Label: tr("암호", "Password"), Value: "example-secret"}, {ID: "check", Kind: "checkbox", Label: tr("선택 상태 보존", "Preserve selection"), Checked: true}, {ID: "save", Kind: "button", Label: tr("저장 요청", "Request save")}})
	if e != nil {
		log.Fatal(e)
	}
	fv, _ := ui.NewFormView(form, p, func(e ui.FormEvent) { status = e.Kind + ":" + e.ID })
	editor := ui.NewEditor("fn example() {\n    print(\"Unicode 界 😀 é\");\n}\n")
	editor.Buffer.Select(0, 0)
	if err := editor.SetByteSyntax([]ui.ByteSyntaxSpan{{Start: 0, End: 2, Role: "info"}}); err != nil {
		log.Fatal(err)
	}
	ev, _ := ui.NewEditorView(editor, p, func(e ui.TextEvent) { status = e.Kind })
	viewer := ui.NewTextView(tr("[리터럴] 도움말과 긴 원문\n세로·가로 스크롤 / Shift+방향키 선택\n원문 복사는 앱에 요청합니다.", "[literal] Help and original text\nScroll vertically/horizontally; Shift+arrows select\nCopying requests a host action."))
	vv, _ := ui.NewEditorView(viewer, p, func(e ui.TextEvent) { status = e.Kind })
	left, _ := ui.NewPanelView(fv, p)
	left.SetTitle(tr("독립 컨트롤·폼", "Controls and form"))
	right, _ := ui.NewPanelView(ev, p)
	right.SetTitle(tr("편집기", "Editor"))
	bottom, _ := ui.NewPanelView(vv, p)
	bottom.SetTitle(tr("읽기 전용 텍스트", "Read-only text"))
	grid, _ := ui.NewLayoutGrid([]ui.Track{{Weight: 2}, {Weight: 1}}, []ui.Track{{Weight: 1}, {Weight: 2}}, []ui.ContainerChild{{Item: ui.LayoutItem{ID: "form", RowSpan: 2}, Child: left}, {Item: ui.LayoutItem{ID: "editor", Column: 1}, Child: right}, {Item: ui.LayoutItem{ID: "viewer", Row: 1, Column: 1}, Child: bottom}}, p)
	grid.Options.Gap = 1
	header, _ := ui.NewRowsView(func(w, h int) []ui.ComponentLine {
		return []ui.ComponentLine{{Text: tr("TUIVORY 공통 컨트롤·배치", "TUIVORY Controls and layout"), Role: "header"}}
	}, p)
	footer, _ := ui.NewRowsView(func(w, h int) []ui.ComponentLine {
		return []ui.ComponentLine{{Text: status, Role: "hint"}, {Text: tr("Tab 이동 · F2 테마 · F3 색상 · F4 팝업 · Ctrl+Q 종료", "Tab focus / F2 theme / F3 colors / F4 popup / Ctrl+Q quit"), Role: "hint"}}
	}, p)
	body, _ := ui.NewColumn([]ui.ContainerChild{{Item: ui.LayoutItem{ID: "header", Disabled: true, Track: ui.Track{Fixed: 1}}, Child: header}, {Item: ui.LayoutItem{ID: "content", Track: ui.Track{Weight: 1}}, Child: grid}, {Item: ui.LayoutItem{ID: "footer", Disabled: true, Track: ui.Track{Fixed: 2}}, Child: footer}}, p)
	body.CycleFocus = false
	popupForm, _ := ui.NewForm([]ui.FormField{{ID: "secret", Kind: "password", Label: tr("암호 마스킹", "Secret masking"), Value: "never-render-this"}, {ID: "ok", Kind: "button", Label: tr("확인 요청", "Confirm request")}})
	pv, _ := ui.NewFormView(popupForm, p, func(e ui.FormEvent) { status = e.Kind + ":" + e.ID })
	surface, _ := ui.NewSurfaceView(pv, p)
	surface.SetBorderPadding(1, 1, 2, 2)
	shadow, _ := ui.NewShadowView(surface, p, ui.ShadowOptions{Mode: ui.ShadowAuto})
	root, _ := ui.NewLayerStack(nil, p)
	update := func() {
		_ = root.SetChildren([]ui.ContainerChild{{Item: ui.LayoutItem{ID: "main"}, Child: body}, {Item: ui.LayoutItem{ID: "popup", Modal: true, Hidden: !*opened, Centered: true, Area: ui.CellRect{Width: 48, Height: 10}}, Child: shadow}})
	}
	update()
	panels := []*ui.PanelView{left, right, bottom, surface}
	refresh := func() {
		p = palette()
		for _, panel := range panels {
			_ = panel.SetPalette(p)
			panel.ASCII = *ascii
		}
		for _, rows := range []*ui.RowsView{fv, ev, vv, pv, header, footer} {
			_ = rows.SetPalette(p)
		}
		for _, c := range []*ui.ContainerView{grid, body, root} {
			_ = c.SetPalette(p)
		}
		_ = shadow.SetPalette(p)
		shadow.ASCII = *ascii
	}
	refresh()
	app.SetInputCapture(func(e *ui.EventKey) *ui.EventKey {
		switch e.Key() {
		case ui.KeyCtrlC:
			// The host reserves Ctrl+Q for exit and lets the control receive copy.
			return ui.NewEventKey(e.Key(), e.Rune(), e.Modifiers())
		case ui.KeyCtrlQ:
			app.Stop()
			return nil
		case ui.KeyF2:
			if *theme == "dark" {
				*theme = "light"
			} else if *theme == "light" {
				*theme = "blackwhite"
			} else {
				*theme = "dark"
			}
			refresh()
			return nil
		case ui.KeyF3:
			values := []string{"8", "16", "256", "truecolor"}
			for i, v := range values {
				if v == *profile {
					*profile = values[(i+1)%len(values)]
					break
				}
			}
			refresh()
			return nil
		case ui.KeyF4:
			*opened = !*opened
			update()
			return nil
		case ui.KeyEscape:
			if *opened {
				*opened = false
				update()
				return nil
			}
		}
		return e
	})
	if e := app.SetRoot(root, true).EnableMouse(true).EnablePaste(true).SetFocus(root).Run(); e != nil {
		log.Fatal(e)
	}
}
