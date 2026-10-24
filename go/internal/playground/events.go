package playground

import (
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

func (u *UI) focusables() []tview.Primitive {
	if u.popup != nil {
		if u.popup.input != nil {
			return []tview.Primitive{u.popup.input, u.popup.save, u.popup.close}
		}
		return []tview.Primitive{u.popup.text, u.popup.close}
	}
	result := []tview.Primitive{u.theme, u.profile}
	if u.lastWidth >= 100 {
		result = append(result, u.nav)
	}
	switch u.page {
	case 1:
		return append(result, u.tokens)
	case 2:
		return append(result, u.guide)
	default:
		return append(result, u.name, u.password, u.choice, u.check, u.buttons[0], u.buttons[1], u.buttons[2], u.list, u.grid)
	}
}
func (u *UI) moveFocus(delta int) {
	list := u.focusables()
	current := u.app.GetFocus()
	index := -1
	for i, p := range list {
		if current == p {
			index = i
			break
		}
	}
	if index < 0 {
		index = 0
	} else {
		index = (index + delta + len(list)) % len(list)
	}
	u.app.SetFocus(list[index])
	u.borders()
}
func (u *UI) cycleTheme() {
	i, _ := u.theme.GetCurrentOption()
	u.theme.SetCurrentOption((i + 1) % len(themeNames))
}
func (u *UI) cycleProfile() {
	i, _ := u.profile.GetCurrentOption()
	u.profile.SetCurrentOption((i + 1) % len(profileNames))
}
func (u *UI) key(event *tcell.EventKey) *tcell.EventKey {
	if event.Key() == tcell.KeyCtrlQ {
		u.app.Stop()
		return nil
	}
	if u.smallMode {
		return nil
	}
	// Open choice lists own Escape and Tab before the enclosing dialog.
	for _, choice := range []*choice{u.theme, u.profile, u.choice} {
		if choice.IsOpen() && (event.Key() == tcell.KeyEscape || event.Key() == tcell.KeyTab || event.Key() == tcell.KeyBacktab) {
			return event
		}
	}
	switch event.Key() {
	case tcell.KeyTab:
		u.moveFocus(1)
		return nil
	case tcell.KeyBacktab:
		u.moveFocus(-1)
		return nil
	case tcell.KeyEscape:
		if u.popup != nil {
			u.closePopup()
		}
		return nil
	case tcell.KeyF2:
		u.cycleTheme()
		return nil
	case tcell.KeyF3:
		u.cycleProfile()
		return nil
	}
	if u.popup != nil {
		return event
	}
	switch event.Key() {
	case tcell.KeyF1:
		u.openHelp()
		return nil
	case tcell.KeyF4:
		u.openPreview()
		return nil
	case tcell.KeyF5:
		u.invalid = !u.invalid
		u.apply()
		u.message("입력 오류 표시를 전환했습니다. 입력값은 유지됩니다.")
		return nil
	case tcell.KeyF6:
		next := (u.page + 1) % 3
		u.nav.SetCurrentItem(next)
		u.showPage(next)
		u.app.SetFocus(u.pageFocus())
		return nil
	}
	return event
}
