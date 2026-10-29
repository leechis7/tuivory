package playground

import (
	"fmt"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
)

func (u *UI) resolvedProfile() string {
	if u.options.Colors != "auto" {
		return u.options.Colors
	}
	return detectedProfile(u.terminal.Colors())
}
func viewStyle(view *tview.TextView, pair Pair) {
	view.SetBackgroundColor(pair.BG)
	view.SetTextStyle(pair.Style())
}
func (u *UI) apply() {
	p, err := loadPalette(u.options.Theme, u.resolvedProfile())
	if err != nil {
		u.message(err.Error())
		return
	}
	styler, err := tuivory.New(u.options.Theme, u.resolvedProfile())
	if err != nil {
		u.message(err.Error())
		return
	}
	u.palette = p
	u.styleLayout(u.root, p["body"])
	for _, view := range []*tview.TextView{u.header, u.context, u.status, u.footer, u.guide, u.small} {
		viewStyle(view, p["body"])
	}
	viewStyle(u.header, p["header"])
	viewStyle(u.footer, p["surface"])
	u.context.SetText(fmt.Sprintf(u.text(" 미리보기 %s · 단말 %s", " Preview %s · Terminal %s"), u.resolvedProfile(), detectedProfile(u.terminal.Colors())))
	for _, choice := range []*choice{u.theme, u.profile, u.choice} {
		styler.DropDown(choice.DropDown)
		choice.SetDoneFunc(func(key tcell.Key) {
			if key == tcell.KeyTab {
				u.moveFocus(1)
			}
			if key == tcell.KeyBacktab {
				u.moveFocus(-1)
			}
		})
		choice.SetLabelStyle(p["surface"].Style()).SetTextOptions("", "", " ", " ▾", " ▾")
	}
	for _, field := range []*tview.InputField{u.name, u.password} {
		styler.Input(field)
		field.SetLabelStyle(p["surface"].Style())
	}
	if u.invalid {
		u.name.SetLabel(u.text("오류! 이름 ", "Error! Name ")).SetFieldStyle(p["field"].Style().Underline(true))
	} else {
		u.name.SetLabel(u.text("이름     ", "Name     "))
	}
	viewStyle(u.disabled, p["disabled"])
	if disabledStyle, err := tuivory.TextOnSurface(p, "disabled", "surface"); err == nil {
		u.disabled.SetTextStyle(disabledStyle)
	}
	u.check.SetLabelStyle(p["surface"].Style()).SetCheckedStyle(p["field"].Style()).SetUncheckedStyle(p["field"].Style()).SetActivatedStyle(p["selection"].Style())
	u.check.SetCheckedString(tview.Escape("[x]")).SetUncheckedString(tview.Escape("[ ]"))
	for i, view := range u.states {
		role := []string{"hint", "info", "success", "warning", "error"}[i]
		viewStyle(view, textOnSurface(p[role], p["surface"]))
	}
	for _, button := range u.buttons {
		styler.Button(button)
	}
	for _, list := range []*tview.List{u.nav, u.list} {
		list.SetBackgroundColor(p["surface"].BG)
		list.SetMainTextStyle(p["surface"].Style()).SetSecondaryTextStyle(p["hint"].Style()).SetShortcutStyle(p["info"].Style()).SetSelectedStyle(p["selection"].Style()).SetHighlightFullLine(true)
	}
	u.styleGrid()
	row, col := u.tokens.GetSelection()
	for c, label := range []string{u.text("역할", "Role"), u.text("전경", "Foreground"), u.text("배경", "Background"), u.text("색상 견본", "Sample")} {
		u.tokens.SetCell(0, c, tview.NewTableCell(label).SetStyle(p["header"].Style().Underline(true)).SetTransparency(false).SetSelectable(false))
	}
	for i, role := range roleNames {
		pair := p[role]
		values := []string{role, colorLabel(pair.FG), colorLabel(pair.BG), u.text(" Aa 한글 ", " Aa Sample ")}
		for c, value := range values {
			style := p["body"].Style()
			if c == 3 {
				style = pair.Style()
			}
			u.tokens.SetCell(i+1, c, tview.NewTableCell(value).SetStyle(style).SetTransparency(false).SetMaxWidth(24))
		}
	}
	if row < 1 {
		row = 1
	}
	u.tokens.Select(row, col)
	u.tokens.SetBackgroundColor(p["body"].BG)
	u.tokens.SetBordersColor(p["hint"].FG).SetSelectedStyle(p["selection"].Style().Underline(true))
	u.stylePopup()
	u.borders()
}
func colorLabel(c tcell.Color) string {
	if c.IsRGB() {
		return c.String()
	}
	return fmt.Sprintf("%d", int(c&^tcell.ColorValid))
}
func (u *UI) styleLayout(primitive tview.Primitive, pair Pair) {
	if primitive == nil {
		return
	}
	switch w := primitive.(type) {
	case *tview.Flex:
		for _, card := range u.cards {
			if w == card {
				pair = u.palette["surface"]
			}
		}
		w.SetBackgroundColor(pair.BG)
		for i := 0; i < w.GetItemCount(); i++ {
			u.styleLayout(w.GetItem(i), pair)
		}
	case *tview.Pages:
		for _, name := range w.GetPageNames(false) {
			u.styleLayout(w.GetPage(name), pair)
		}
	case *tview.TextView:
		w.SetBackgroundColor(pair.BG)
	case *tview.InputField:
		w.SetBackgroundColor(pair.BG)
	case *choice:
		w.SetBackgroundColor(pair.BG)
	case *tview.DropDown:
		w.SetBackgroundColor(pair.BG)
	case *tview.Checkbox:
		w.SetBackgroundColor(pair.BG)
	case *tview.Box:
		w.SetBackgroundColor(pair.BG)
	}
}
func (u *UI) borders() {
	if u.palette == nil {
		return
	}
	p := u.palette
	styler, err := tuivory.New(u.options.Theme, u.resolvedProfile())
	if err != nil {
		return
	}
	u.styleGrid()
	for _, card := range u.cards {
		card.SetBorderStyle(styler.Styles.BorderStyle(card.HasFocus(), card.GetBackgroundColor())).SetTitleColor(p["surface"].FG)
	}
	for _, box := range []*tview.Box{u.nav.Box, u.tokens.Box, u.guide.Box} {
		box.SetBorderStyle(styler.Styles.BorderStyle(box.HasFocus(), box.GetBackgroundColor())).SetTitleColor(p["body"].FG)
	}
	if u.popup != nil {
		u.popup.card.SetBorderStyle(p["focus.border"].Style()).SetTitleColor(p["surface"].FG)
	}
}

func (u *UI) styleGrid() {
	styler, err := tuivory.New(u.options.Theme, u.resolvedProfile())
	if err != nil {
		return
	}
	styler.Grid(u.grid, func(row, col int) tuivory.CellState {
		return tuivory.CellState{Edited: u.changed[row]}
	})
}
