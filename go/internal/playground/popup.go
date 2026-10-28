package playground

import (
	"fmt"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go/internal/drawing"
	"github.com/rivo/tview"
)

type popup struct {
	card        *tview.Flex
	text        *tview.TextView
	input       *tview.InputField
	save, close *tview.Button
	buttons     *tview.Flex
	previous    tview.Primitive
}
type popupLayer struct {
	*tview.Flex
	owner *UI
}

func (p *popupLayer) Draw(screen tcell.Screen) {
	x, y, w, h := p.owner.layers.GetRect()
	drawing.Dim(screen, x, y, w, h)
	width, height := min(76, max(1, w-6)), min(20, max(1, h-4))
	if p.owner.popup.input != nil {
		height = min(height, 10)
	}
	p.Flex.SetRect(x+(w-width)/2, y+(h-height)/2, width, height)
	p.Flex.Draw(drawing.SafeScreen(screen))
}
func (p *popupLayer) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return func(action tview.MouseAction, event *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		x, y := event.Position()
		if !p.InRect(x, y) {
			return true, nil
		}
		return p.Flex.MouseHandler()(action, event, focus)
	}
}
func (u *UI) openPopup(title, text string, editRow int) {
	if u.popup != nil {
		return
	}
	p := &popup{previous: u.app.GetFocus()}
	u.popup = p
	p.text = tview.NewTextView().SetText(text).SetWrap(true).SetWordWrap(true).SetScrollable(true)
	p.close = tview.NewButton(u.text("닫기 / Esc", "Close / Esc")).SetSelectedFunc(u.closePopup)
	p.card = newFlex().SetDirection(tview.FlexRow)
	p.card.SetBorder(true).SetTitle(title).SetBorderPadding(1, 1, 2, 2)
	p.card.AddItem(p.text, 0, 1, false)
	p.buttons = newFlex()
	if editRow > 0 {
		p.input = tview.NewInputField().SetLabel(u.text("새 값 ", "New value ")).SetText(u.rows[editRow-1])
		p.save = tview.NewButton(u.text("저장", "Save")).SetSelectedFunc(func() {
			u.rows[editRow-1] = p.input.GetText()
			u.changed[editRow] = true
			u.grid.GetCell(editRow, 1).SetText(u.rows[editRow-1])
			u.grid.GetCell(editRow, 2).SetText(u.text("* 변경됨", "* Edited"))
			u.closePopup()
			u.apply()
			u.message(u.text("* 변경된 견본 셀입니다. DB나 파일에 저장하지 않습니다.", "* Edited sample cell. Nothing is saved to a database or file."))
		})
		p.input.SetDoneFunc(func(key tcell.Key) {
			if key == tcell.KeyEnter {
				u.app.SetFocus(p.save)
			}
		})
		p.card.AddItem(p.input, 1, 0, true).AddItem(tview.NewBox(), 1, 0, false)
		p.save.SetInputCapture(func(event *tcell.EventKey) *tcell.EventKey {
			if event.Key() == tcell.KeyLeft || event.Key() == tcell.KeyRight {
				u.app.SetFocus(p.close)
				return nil
			}
			return event
		})
		p.close.SetInputCapture(func(event *tcell.EventKey) *tcell.EventKey {
			if event.Key() == tcell.KeyLeft || event.Key() == tcell.KeyRight {
				u.app.SetFocus(p.save)
				return nil
			}
			return event
		})
		p.buttons.AddItem(p.save, 0, 1, false)
	}
	p.buttons.AddItem(p.close, 0, 1, false)
	p.card.AddItem(p.buttons, 1, 0, false)
	layer := &popupLayer{p.card, u}
	u.layers.AddPage("modal", layer, true, true)
	if p.input != nil {
		u.app.SetFocus(p.input)
	} else {
		u.app.SetFocus(p.text)
	}
	u.stylePopup()
	u.borders()
}
func (u *UI) stylePopup() {
	p := u.popup
	if p == nil {
		return
	}
	palette := u.palette
	u.styleLayout(p.card, palette["surface"])
	p.card.SetBackgroundColor(palette["surface"].BG)
	p.buttons.SetBackgroundColor(palette["surface"].BG)
	viewStyle(p.text, palette["surface"])
	p.close.SetStyle(palette["button"].Style()).SetActivatedStyle(palette["button.focus"].Style().Underline(true))
	if p.input != nil {
		p.input.SetBackgroundColor(palette["surface"].BG)
		p.input.SetFieldStyle(palette["field"].Style()).SetLabelStyle(palette["surface"].Style())
		p.save.SetStyle(palette["button"].Style()).SetActivatedStyle(palette["button.focus"].Style().Underline(true))
	}
}
func (u *UI) closePopup() {
	if u.popup == nil {
		return
	}
	previous := u.popup.previous
	u.layers.RemovePage("modal")
	u.popup = nil
	u.app.SetFocus(previous)
	u.borders()
}
func (u *UI) openHelp() {
	u.openPopup(u.text(" TUIVORY 조작 안내 ", " TUIVORY Controls "), u.text(guideText, guideTextEN), 0)
}
func (u *UI) openPreview() {
	_, choice := u.choice.GetCurrentOption()
	u.openPopup(u.text(" 팝업 · 현재 입력 미리보기 ", " Popup · Current Input Preview "), fmt.Sprintf(u.text("이름: %s\n선택: %s\n체크: %t\n\n암호 예시는 표시하지 않습니다.\n\nTab/Shift+Tab은 팝업 안에서만 이동합니다.\n바깥 클릭은 뒤 화면을 조작하지 않습니다.\nF2/F3으로 팝업을 연 상태에서도 테마를 바꿀 수 있습니다.\nEsc로 닫으면 이전 포커스로 돌아갑니다.", "Name: %s\nChoice: %s\nChecked: %t\n\nThe password example is hidden.\n\nTab/Shift+Tab cycles within this popup.\nOutside clicks do not reach the background.\nF2/F3 changes styles while the popup is open.\nEsc closes it and restores the previous focus."), u.name.GetText(), choice, u.check.IsChecked()), 0)
}
func (u *UI) openEdit(row int) {
	u.openPopup(u.text(" 셀 편집 · 합성 데이터 ", " Edit Cell · Synthetic Data "), u.text("이름 값을 바꾸고 저장하세요. 변경됨 표시는 색상과 *를 함께 사용합니다.", "Change the name and save. Edited cells use both color and an * marker."), row)
}
