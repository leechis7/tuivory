package playground

import (
	"fmt"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go/internal/drawing"
	"github.com/rivo/tview"
)

type Options struct {
	Theme, Colors string
	Lang          string
	Mouse         bool
}
type UI struct {
	app                                           *tview.Application
	terminal                                      tcell.Screen
	options                                       Options
	palette                                       Palette
	layers, views                                 *tview.Pages
	root, body, component, upper, lower           *tview.Flex
	header, context, status, footer, guide, small *tview.TextView
	theme, profile, choice                        *choice
	name, password                                *tview.InputField
	disabled                                      *tview.TextView
	check                                         *tview.Checkbox
	nav, list                                     *tview.List
	grid, tokens                                  *tview.Table
	cards                                         []*tview.Flex
	buttons                                       []*tview.Button
	states                                        []*tview.TextView
	page                                          int
	rows                                          []string
	changed                                       map[int]bool
	invalid                                       bool
	popup                                         *popup
	smallMode                                     bool
	reflowQueued                                  bool
	lastWidth, lastHeight                         int
}

func Run(options Options) error {
	var err error
	options, err = normalizeOptions(options)
	if err != nil {
		return err
	}
	terminal, err := tcell.NewScreen()
	if err != nil {
		return err
	}
	// Application.SetScreen initializes its screen. Capture its error without
	// initializing a second time (which starts duplicate terminal input readers).
	checked := &checkedScreen{Screen: terminal}
	app := tview.NewApplication().SetScreen(checked)
	if checked.initError != nil {
		return checked.initError
	}
	defer terminal.Fini()
	ui, err := New(app, terminal, options)
	if err != nil {
		return err
	}
	app.SetRoot(ui.layers, true).EnableMouse(options.Mouse)
	return app.Run()
}
func New(app *tview.Application, terminal tcell.Screen, options Options) (*UI, error) {
	var err error
	options, err = normalizeOptions(options)
	if err != nil {
		return nil, err
	}
	u := &UI{app: app, terminal: terminal, options: options, changed: map[int]bool{}}
	u.rows = []string{u.text("한글 입력 예시", "Sample input"), u.text("선택과 포커스", "Selection and focus"), u.text("Enter로 편집", "Enter to edit")}
	u.layers = tview.NewPages()
	u.views = tview.NewPages()
	u.header = tview.NewTextView().SetText(u.text(" TUIVORY  ·  직접 조작하는 TUI 스타일 실험실", " TUIVORY  ·  Interactive terminal UI style playground"))
	u.context = tview.NewTextView().SetWrap(false)
	u.status = tview.NewTextView().SetText(u.text(" 이름을 입력하거나 Tab으로 이동해 보세요. DB·파일에 저장하지 않습니다.", " Enter a name or press Tab. Nothing is saved to a database or file.")).SetWrap(false)
	u.footer = tview.NewTextView().SetWrap(false)
	u.theme = &choice{DropDown: tview.NewDropDown().SetLabel(u.text(" 테마 ", " Theme ")).SetFieldWidth(12).SetOptions([]string{u.text("다크", "Dark"), u.text("라이트", "Light"), u.text("흑백", "Monochrome")}, nil)}
	u.profile = &choice{DropDown: tview.NewDropDown().SetLabel(u.text(" 색상 ", " Colors ")).SetFieldWidth(14).SetOptions([]string{u.text("자동", "Auto"), u.text("8색", "8 colors"), u.text("16색", "16 colors"), u.text("256색", "256 colors"), "True Color"}, nil)}
	for i, v := range themeNames {
		if v == options.Theme {
			u.theme.SetCurrentOption(i)
		}
	}
	for i, v := range profileNames {
		if v == options.Colors {
			u.profile.SetCurrentOption(i)
		}
	}
	u.theme.SetSelectedFunc(func(_ string, i int) { u.options.Theme = themeNames[i]; u.apply() })
	u.profile.SetSelectedFunc(func(_ string, i int) { u.options.Colors = profileNames[i]; u.apply() })
	u.nav = tview.NewList().ShowSecondaryText(false)
	u.nav.SetBorder(true).SetTitle(u.text(" 둘러보기 ", " Explore "))
	for _, label := range []string{u.text("컴포넌트 견본", "Components"), u.text("색상 토큰", "Color tokens"), u.text("조작 안내", "Controls")} {
		u.nav.AddItem(label, "", 0, nil)
	}
	u.buildComponents()
	u.tokens = tview.NewTable().SetFixed(1, 0).SetSelectable(true, true).SetSeparator('│')
	u.tokens.SetBorder(true).SetTitle(u.text(" 의미별 색상 · 16개 역할 ", " Semantic colors · 16 roles "))
	u.guide = tview.NewTextView().SetText(u.text(guideText, guideTextEN)).SetWrap(true).SetWordWrap(true).SetScrollable(true)
	u.guide.SetBorder(true).SetTitle(u.text(" 조작 안내 ", " Controls ")).SetBorderPadding(1, 1, 2, 2)
	u.views.AddPage("components", u.component, true, true).AddPage("tokens", u.tokens, true, false).AddPage("guide", u.guide, true, false)
	u.nav.SetChangedFunc(func(i int, _ string, _ string, _ rune) { u.showPage(i) })
	u.nav.SetSelectedFunc(func(i int, _ string, _ string, _ rune) { u.showPage(i); u.app.SetFocus(u.pageFocus()) })
	u.body = newFlex()
	controls := newFlex().AddItem(u.theme, 24, 0, false).AddItem(u.profile, 28, 0, false).AddItem(u.context, 0, 1, false)
	u.root = newFlex().SetDirection(tview.FlexRow).AddItem(u.header, 1, 0, false).AddItem(controls, 1, 0, false).AddItem(u.body, 0, 1, true).AddItem(u.status, 1, 0, false).AddItem(u.footer, 1, 0, false)
	u.small = tview.NewTextView().SetText(u.text("TUIVORY\n\n터미널을 80열 × 24행 이상으로 넓혀 주세요.\nCtrl+Q 종료", "TUIVORY\n\nResize the terminal to at least 80 columns × 24 rows.\nCtrl+Q Quit")).SetTextAlign(tview.AlignCenter)
	u.layers.AddPage("main", u.root, true, true).AddPage("small", u.small, true, false)
	u.app.SetRoot(u.layers, true).SetInputCapture(u.key).SetBeforeDrawFunc(func(screen tcell.Screen) bool {
		width, height := screen.Size()
		// Drawing holds Application's lock. Page visibility changes can delegate
		// focus back to SetFocus, so perform reflow in the UI update queue instead.
		if (width != u.lastWidth || height != u.lastHeight) && !u.reflowQueued {
			u.reflowQueued = true
			go u.app.QueueUpdateDraw(func() { u.reflowQueued = false; u.reflow(); u.borders() })
		}
		u.borders()
		return false
	})
	u.app.SetFocus(u.name)
	u.apply()
	u.reflow()
	return u, nil
}
func (u *UI) card(title string) *tview.Flex {
	card := newFlex().SetDirection(tview.FlexRow)
	card.SetBorder(true).SetTitle(title).SetBorderPadding(0, 0, 1, 1)
	u.cards = append(u.cards, card)
	return card
}
func (u *UI) buildComponents() {
	fields := u.card(u.text(" 입력 · 선택 ", " Inputs · Choices "))
	u.name = tview.NewInputField().SetLabel(u.text("이름     ", "Name     ")).SetText(u.text("한글과 English", "Hello, world!")).SetFieldWidth(0)
	u.password = tview.NewInputField().SetLabel(u.text("암호 예시 ", "Password ")).SetText("sample").SetMaskCharacter('*')
	u.choice = &choice{DropDown: tview.NewDropDown().SetLabel(u.text("선택     ", "Choice   ")).SetOptions([]string{u.text("개발 환경", "Development"), u.text("검토 환경", "Review"), u.text("운영 환경", "Production")}, nil).SetCurrentOption(0)}
	u.check = tview.NewCheckbox().SetLabel(u.text("선택 상태를 유지합니다 ", "Keep selection state ")).SetChecked(true)
	u.disabled = tview.NewTextView().SetText(u.text("비활성   입력할 수 없는 예시", "Disabled: read-only example")).SetWrap(false)
	fields.AddItem(u.name, 1, 0, true).AddItem(u.password, 1, 0, false).AddItem(u.choice, 1, 0, false).AddItem(u.check, 1, 0, false).AddItem(u.disabled, 1, 0, false)
	hint := tview.NewTextView().SetText(u.text("Tab 영역 이동 · 선택박스 Enter 펼침", "Tab: move focus · Enter: open choice")).SetWrap(true)
	fields.AddItem(hint, 0, 1, false)
	u.states = append(u.states, hint)
	actions := u.card(u.text(" 버튼 · 상태 ", " Buttons · States "))
	for _, text := range []string{u.text("안내: 색 이외에 문구도 함께 표시합니다.", "Info: states use text as well as color."), u.text("정상: 조작 가능한 견본입니다.", "OK: this is an interactive example."), u.text("주의: 미리보기는 단말 능력을 바꾸지 않습니다.", "Warning: preview leaves terminal unchanged."), u.text("오류: F5로 입력 오류 상태를 켜 보세요.", "Error: press F5 to toggle input errors.")} {
		view := tview.NewTextView().SetText(text).SetWrap(false)
		u.states = append(u.states, view)
		actions.AddItem(view, 1, 0, false)
	}
	row := newFlex()
	labels := []string{u.text("적용", "Apply"), u.text("팝업", "Popup"), u.text("초기화", "Reset"), u.text("비활성", "Disabled")}
	for i, label := range labels {
		index := i
		b := tview.NewButton(label).SetSelectedFunc(func() {
			switch index {
			case 0:
				u.message(u.text("적용 예시: ", "Applied preview: ") + u.name.GetText())
			case 1:
				u.openPreview()
			case 2:
				u.reset()
			}
		})
		b.SetInputCapture(func(event *tcell.EventKey) *tcell.EventKey {
			if event.Key() == tcell.KeyLeft {
				u.app.SetFocus(u.buttons[(index+2)%3])
				return nil
			}
			if event.Key() == tcell.KeyRight {
				u.app.SetFocus(u.buttons[(index+1)%3])
				return nil
			}
			return event
		})
		if i == 3 {
			b.SetDisabled(true)
		}
		u.buttons = append(u.buttons, b)
		row.AddItem(b, 0, 1, false)
	}
	actions.AddItem(tview.NewBox(), 1, 0, false).AddItem(row, 1, 0, false)
	listCard := u.card(u.text(" 목록 · 선택과 포커스 ", " List · Selection and Focus "))
	u.list = tview.NewList().ShowSecondaryText(false)
	for _, label := range []string{u.text("입력창과 선택박스", "Inputs and choices"), u.text("버튼과 비활성 상태", "Buttons and disabled states"), u.text("포커스와 선택은 별개", "Focus differs from selection"), u.text("팝업과 배경 입력 차단", "Popups block background input")} {
		u.list.AddItem(label, "", 0, nil)
	}
	u.list.SetSelectedFunc(func(i int, text, _ string, _ rune) {
		u.message(fmt.Sprintf(u.text("목록 %d 선택: %s", "List item %d selected: %s"), i+1, text))
	})
	listCard.AddItem(u.list, 0, 1, true)
	gridCard := u.card(u.text(" 그리드 · Enter 셀 편집 ", " Grid · Enter to Edit "))
	u.grid = tview.NewTable().SetFixed(1, 0).SetSelectable(true, true).SetSeparator('│')
	for col, text := range []string{"ID", u.text("이름", "Name"), u.text("상태", "State")} {
		u.grid.SetCell(0, col, tview.NewTableCell(text).SetSelectable(false))
	}
	for i, text := range u.rows {
		u.grid.SetCell(i+1, 0, tview.NewTableCell(fmt.Sprint(i+1)))
		u.grid.SetCell(i+1, 1, tview.NewTableCell(text).SetExpansion(1))
		u.grid.SetCell(i+1, 2, tview.NewTableCell(u.text("원본", "Original")))
	}
	u.grid.Select(1, 1).SetSelectedFunc(func(row, col int) {
		if row > 0 && col == 1 {
			u.openEdit(row)
		} else {
			u.message(u.text("이름 열을 선택하고 Enter로 편집하세요.", "Select the Name column and press Enter to edit."))
		}
	})
	gridCard.AddItem(u.grid, 0, 1, true)
	u.upper = newFlex().AddItem(fields, 0, 1, true).AddItem(actions, 0, 1, false)
	u.lower = newFlex().AddItem(listCard, 0, 1, false).AddItem(gridCard, 0, 1, true)
	u.component = newFlex().SetDirection(tview.FlexRow).AddItem(u.upper, 10, 0, true).AddItem(u.lower, 0, 1, false)
}
func (u *UI) showPage(index int) {
	u.page = index
	u.views.SwitchToPage([]string{"components", "tokens", "guide"}[index])
	u.message([]string{u.text("입력·목록·그리드를 직접 조작해 보세요.", "Try the inputs, list, and grid."), u.text("역할별 전경·배경과 실제 색상 견본입니다.", "Foreground, background, and color samples by role."), u.text("방향키와 PgUp/PgDn으로 안내를 읽으세요.", "Use arrow keys and PgUp/PgDn to read the guide.")}[index])
}
func (u *UI) pageFocus() tview.Primitive {
	switch u.page {
	case 1:
		return u.tokens
	case 2:
		return u.guide
	default:
		return u.name
	}
}
func (u *UI) message(text string) {
	if u.status != nil {
		u.status.SetText(" " + text)
	}
}
func (u *UI) reset() {
	u.name.SetText(u.text("한글과 English", "Hello, world!"))
	u.password.SetText("sample")
	u.choice.SetCurrentOption(0)
	u.check.SetChecked(true)
	u.invalid = false
	u.rows = []string{u.text("한글 입력 예시", "Sample input"), u.text("선택과 포커스", "Selection and focus"), u.text("Enter로 편집", "Enter to edit")}
	u.changed = map[int]bool{}
	for i, text := range u.rows {
		u.grid.GetCell(i+1, 1).SetText(text)
		u.grid.GetCell(i+1, 2).SetText(u.text("원본", "Original"))
	}
	u.apply()
	u.message(u.text("견본 값을 초기화했습니다.", "Sample values reset."))
}
func (u *UI) reflow() {
	w, h := u.terminal.Size()
	if w == u.lastWidth && h == u.lastHeight {
		return
	}
	u.lastWidth, u.lastHeight = w, h
	small := w < 80 || h < 24
	if small {
		u.layers.ShowPage("small")
		u.layers.HidePage("modal")
	} else {
		u.layers.HidePage("small")
		if u.popup != nil {
			u.layers.ShowPage("modal")
		}
	}
	u.smallMode = small
	u.body.Clear()
	if w >= 100 {
		u.body.AddItem(u.nav, 21, 0, false)
	} else if u.app.GetFocus() == u.nav {
		u.app.SetFocus(u.pageFocus())
	}
	u.body.AddItem(u.views, 0, 1, true)
	u.component.ResizeItem(u.upper, min(13, max(9, (h-4)/2)), 0)
	if w < 110 {
		u.footer.SetText(u.text(" F1 도움말  F2 테마  F3 색상  F4 팝업  F5 오류  F6 화면  Ctrl+Q 종료", " F1 Help  F2 Theme  F3 Colors  F4 Popup  F5 Error  F6 View  Ctrl+Q Quit"))
	} else {
		u.footer.SetText(u.text(" Tab/Shift+Tab 이동 · F1 도움말 · F2 테마 · F3 색상 · F4 팝업 · F5 입력 오류 · F6 화면 전환 · Enter 셀 편집 · Ctrl+Q 종료", " Tab/Shift+Tab Focus · F1 Help · F2 Theme · F3 Colors · F4 Popup · F5 Error · F6 View · Enter Edit · Ctrl+Q Quit"))
	}
}

const guideText = `TUIVORY · 무엇을 볼 수 있나요?

1. 컴포넌트 견본
이름을 입력하고 암호 마스킹, 선택박스, 체크박스를 조작하세요.
적용/팝업/초기화 버튼을 눌러 상태와 모달을 확인합니다.
그리드 이름 열에서 Enter로 편집하고 저장하면 * 변경 표시가 남습니다.
이 예시는 DB나 파일에 저장하지 않습니다.

2. 테마와 색상
F2로 다크/라이트/흑백, F3로 자동/8/16/256/True Color를 전환합니다.
입력값·체크·선택·편집한 셀은 그대로 유지됩니다.
색상 선택은 토큰 미리보기이며 터미널 자체의 지원 능력을 바꾸지 않습니다.
실제 단말은 더 적은 색으로 근사할 수 있습니다.

3. 색상 토큰
F6 또는 왼쪽 메뉴로 이동합니다. 16개 의미별 역할의 전경/배경을 비교하세요.
Go 스타일 팔레트로 표시하며 공통 토큰은 역할 표시 순서에 사용합니다.

4. 조작
Tab/Shift+Tab: 조작 대상 이동
방향키: 목록·그리드 이동 / 버튼 좌우 이동
Enter: 버튼 실행·선택박스 펼침·이름 셀 편집
F1: 도움말 / F4: 팝업 / F5: 입력 오류 표시 / F6: 화면
Esc: 열린 선택박스나 팝업 닫기
Ctrl+Q: 종료

마우스로도 선택·버튼·팝업을 조작할 수 있습니다.
80×24 미만이면 터미널을 넓히라는 안내를 보여줍니다.
실제 ANSI 팔레트, 글꼴, 마우스 지원은 단말마다 다릅니다.`

// Choice uses shared wide-glyph overlap protection for its open list.
type choice struct{ *tview.DropDown }

func (c *choice) Draw(screen tcell.Screen) {
	if c.IsOpen() {
		c.DropDown.Draw(drawing.SafeScreen(screen))
		return
	}
	c.DropDown.Draw(screen)
}

// Flex is transparent by default; opaque boxes also paint padding and gaps.
func newFlex() *tview.Flex { f := tview.NewFlex(); f.Box = tview.NewBox(); return f }

// SetScreen ignores Init's return value; retain it while preserving normal
// initialization on future suspend/resume operations.
type checkedScreen struct {
	tcell.Screen
	initError error
}

func (s *checkedScreen) Init() error { s.initError = s.Screen.Init(); return s.initError }
