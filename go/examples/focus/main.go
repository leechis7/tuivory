// Database-free host for the public control-state and modal focus APIs.
package main

import (
	"flag"
	"fmt"
	"github.com/gdamore/tcell/v2"
	ui "github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
	"github.com/rivo/uniseg"
	"log"
)

func targets(level int) []ui.FocusTarget {
	switch level {
	case 0:
		return []ui.FocusTarget{{ID: "open"}, {ID: "read", State: ui.ControlState{ReadOnly: true}}, {ID: "busy", State: ui.ControlState{Busy: true}}, {ID: "disabled", State: ui.ControlState{Disabled: true}}, {ID: "tail"}}
	case 1:
		return []ui.FocusTarget{{ID: "child"}, {ID: "invalid", State: ui.ControlState{Invalid: true, Selected: true, Edited: true}}, {ID: "disabled", State: ui.ControlState{Disabled: true}}, {ID: "close"}}
	default:
		return []ui.FocusTarget{{ID: "close"}, {ID: "read", State: ui.ControlState{ReadOnly: true}}}
	}
}
func text(en bool, ko, english string) string {
	if en {
		return english
	}
	return ko
}
func label(id string, en bool) string {
	labels := map[string][2]string{"open": {"팝업 열기", "Open popup"}, "read": {"읽기 전용 내용", "Read-only content"}, "busy": {"처리 중인 항목", "Busy control"}, "disabled": {"사용 불가", "Disabled"}, "tail": {"마지막 항목", "Last control"}, "child": {"중첩 팝업 열기", "Open nested popup"}, "invalid": {"오류 · 선택 · 변경됨", "Invalid · Selected · Edited"}, "close": {"닫기", "Close"}}
	pair := labels[id]
	return text(en, pair[0], pair[1])
}

type rect struct{ x, y, w, h int }

func area(level, w, h int) rect {
	if level == 0 {
		return rect{min(2, max(0, w-1)), 3, max(0, w-4), min(10, max(0, h-6))}
	}
	width, height := min(64, max(0, w-4)), min(10, max(0, h-4))
	if level == 2 {
		width, height = min(48, max(0, w-2)), min(8, max(0, h-4))
	}
	return rect{(w - width) / 2, max(2, (h-height)/2), width, height}
}
func write(screen tcell.Screen, x, y, w int, s string, style tcell.Style) {
	glyphs := uniseg.NewGraphemes(ui.CellText(s, w))
	column := 0
	for glyphs.Next() {
		r := []rune(glyphs.Str())
		screen.SetContent(x+column, y, r[0], r[1:], style)
		column += glyphs.Width()
	}
}

type lines struct {
	*tview.Box
	items      []ui.FocusTarget
	palette    ui.Palette
	focused    string
	en, active bool
}

func (l *lines) Draw(screen tcell.Screen) {
	x, y, w, h := l.GetRect()
	for index, item := range l.items {
		if index >= h {
			break
		}
		v := item.State.Visual()
		style, _ := ui.ControlStyle(l.palette, item.State, l.active && l.focused == item.ID)
		cursor := "  "
		if l.active && l.focused == item.ID {
			cursor = "> "
		}
		write(screen, x, y+index, w, cursor+fmt.Sprintf("%-6s", v.Markers)+label(item.ID, l.en), style)
	}
}
func (l *lines) HasFocus() bool { return l.active }

type view struct {
	*tview.Box
	stack          *ui.FocusStack
	en, ascii      bool
	theme, profile string
	palette        ui.Palette
}

func (v *view) refresh() {
	doc, _ := ui.CandidateTokens()
	p, e := doc.Palette(v.theme, v.profile)
	if e != nil {
		log.Fatal(e)
	}
	v.palette, e = ui.Resolve(p)
	if e != nil {
		log.Fatal(e)
	}
}
func (v *view) Draw(screen tcell.Screen) {
	x, y, w, h := v.GetRect()
	surface := v.palette["surface"].Style()
	for row := 0; row < h; row++ {
		for col := 0; col < w; col++ {
			screen.SetContent(x+col, y+row, ' ', nil, surface)
		}
	}
	write(screen, x, y, w, "TUIVORY Focus · "+text(v.en, "한글 상태·팝업 견본 / 이름", "Control and popup example / Name"), v.palette["body"].Style())
	write(screen, x, y+1, w, fmt.Sprintf("Scope=%s Focus=%s Depth=%d", v.stack.ScopeID(), v.stack.Focused(), v.stack.Depth()), v.palette["info"].Style())
	for level := 0; level <= v.stack.Depth(); level++ {
		r := area(level, w, h)
		if r.w < 3 || r.h < 3 {
			continue
		}
		content := &lines{Box: tview.NewBox(), items: targets(level), palette: v.palette, focused: v.stack.Focused(), en: v.en, active: level == v.stack.Depth()}
		panel, _ := ui.NewPanelView(content, v.palette)
		panel.ASCII = v.ascii
		panel.SetRect(x+r.x, y+r.y, r.w, r.h)
		titles := [][2]string{{"기본 컨트롤", "Root controls"}, {"바깥 팝업", "Outer popup"}, {"안쪽 팝업", "Inner popup"}}
		panel.SetTitle(text(v.en, titles[level][0], titles[level][1]))
		panel.Draw(screen)
	}
	if h > 0 {
		write(screen, x, y+h-1, w, text(v.en, "Tab/Shift+Tab 이동 · Enter 열기/닫기 · Esc 복귀 · F2 테마 · F3 색상 · F4 ASCII · Ctrl+Q 종료", "Tab/Shift+Tab move · Enter open/close · Esc return · F2 theme · F3 colors · F4 ASCII · Ctrl+Q quit"), v.palette["hint"].Style())
	}
}
func (v *view) activate() {
	allowed := false
	for _, target := range v.stack.Targets() {
		if target.ID == v.stack.Focused() {
			allowed = target.State.Visual().Activatable
		}
	}
	if !allowed {
		return
	}
	switch v.stack.Focused() {
	case "open":
		_ = v.stack.Open("outer", targets(1), "child", true)
	case "child":
		_ = v.stack.Open("inner", targets(2), "close", true)
	case "close":
		_ = v.stack.Close(v.stack.ScopeID())
	}
}
func (v *view) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return func(action tview.MouseAction, event *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		if action != tview.MouseLeftClick {
			return false, nil
		}
		x, y := event.Position()
		ox, oy, w, h := v.GetRect()
		x -= ox
		y -= oy
		for level := v.stack.Depth(); level >= 0; level-- {
			r := area(level, w, h)
			if x < r.x || x >= r.x+r.w || y < r.y || y >= r.y+r.h {
				continue
			}
			scope := []string{"root", "outer", "inner"}[level]
			if v.stack.Route(scope).Blocked {
				return true, v
			}
			row := y - r.y - 2
			items := targets(level)
			if row >= 0 && row < len(items) && x >= r.x+2 && x < r.x+r.w-2 {
				v.stack.Focus(items[row].ID)
			}
			return true, v
		}
		return true, v
	}
}
func main() {
	lang := flag.String("lang", "ko", "ko or en")
	theme := flag.String("theme", "dark", "dark/light/blackwhite")
	profile := flag.String("colors", "256", "8/16/256/truecolor")
	ascii := flag.Bool("ascii", false, "ASCII borders")
	flag.Parse()
	if *lang != "ko" && *lang != "en" {
		log.Fatal("--lang must be ko or en")
	}
	stack, e := ui.NewFocusStack("root", targets(0))
	if e != nil {
		log.Fatal(e)
	}
	v := &view{Box: tview.NewBox(), stack: stack, en: *lang == "en", theme: *theme, profile: *profile, ascii: *ascii}
	v.refresh()
	app := tview.NewApplication()
	cycle := func(value *string, values []string) {
		for i, s := range values {
			if *value == s {
				*value = values[(i+1)%len(values)]
				return
			}
		}
	}
	app.SetInputCapture(func(event *tcell.EventKey) *tcell.EventKey {
		switch event.Key() {
		case tcell.KeyCtrlQ:
			app.Stop()
		case tcell.KeyTab, tcell.KeyBacktab:
			stack.Move(event.Key() == tcell.KeyBacktab)
		case tcell.KeyEnter:
			v.activate()
		case tcell.KeyEscape:
			if request := stack.RequestClose(); request != nil {
				_ = stack.Close(request.ID)
			}
		case tcell.KeyF2:
			cycle(&v.theme, []string{"dark", "light", "blackwhite"})
			v.refresh()
		case tcell.KeyF3:
			cycle(&v.profile, []string{"8", "16", "256", "truecolor"})
			v.refresh()
		case tcell.KeyF4:
			v.ascii = !v.ascii
		}
		return nil
	})
	if e := app.SetRoot(v, true).SetFocus(v).EnableMouse(true).Run(); e != nil {
		log.Fatal(e)
	}
}
