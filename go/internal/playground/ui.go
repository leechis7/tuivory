package playground

import (
	"fmt"

	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

type Options struct {
	Theme, Colors string
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
	lastWidth, lastHeight                         int
}

func Run(options Options) error {
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
	if options.Theme == "" {
		options.Theme = "dark"
	}
	if options.Colors == "" {
		options.Colors = "auto"
	}
	if !contains(themeNames, options.Theme) || !contains(profileNames, options.Colors) {
		return nil, fmt.Errorf("invalid theme or color profile")
	}
	u := &UI{app: app, terminal: terminal, options: options, rows: []string{"한글 입력 예시", "선택과 포커스", "Enter로 편집"}, changed: map[int]bool{}}
	u.layers = tview.NewPages()
	u.views = tview.NewPages()
	u.header = tview.NewTextView().SetText(" TUIVORY  ·  직접 조작하는 TUI 스타일 실험실")
	u.context = tview.NewTextView().SetWrap(false)
	u.status = tview.NewTextView().SetText(" 이름을 입력하거나 Tab으로 이동해 보세요. DB·파일에 저장하지 않습니다.").SetWrap(false)
	u.footer = tview.NewTextView().SetWrap(false)
	u.theme = &choice{DropDown: tview.NewDropDown().SetLabel(" 테마 ").SetFieldWidth(12).SetOptions([]string{"다크", "라이트", "흑백"}, nil)}
	u.profile = &choice{DropDown: tview.NewDropDown().SetLabel(" 색상 ").SetFieldWidth(14).SetOptions([]string{"자동", "8색", "16색", "256색", "True Color"}, nil)}
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
	u.nav.SetBorder(true).SetTitle(" 둘러보기 ")
	for _, label := range []string{"컴포넌트 견본", "색상 토큰", "조작 안내"} {
		u.nav.AddItem(label, "", 0, nil)
	}
	u.buildComponents()
	u.tokens = tview.NewTable().SetFixed(1, 0).SetSelectable(true, true).SetSeparator('│')
	u.tokens.SetBorder(true).SetTitle(" 의미별 색상 · 16개 역할 ")
	u.guide = tview.NewTextView().SetText(guideText).SetWrap(true).SetWordWrap(true).SetScrollable(true)
	u.guide.SetBorder(true).SetTitle(" 조작 안내 ").SetBorderPadding(1, 1, 2, 2)
	u.views.AddPage("components", u.component, true, true).AddPage("tokens", u.tokens, true, false).AddPage("guide", u.guide, true, false)
	u.nav.SetChangedFunc(func(i int, _ string, _ string, _ rune) { u.showPage(i) })
	u.nav.SetSelectedFunc(func(i int, _ string, _ string, _ rune) { u.showPage(i); u.app.SetFocus(u.pageFocus()) })
	u.body = newFlex()
	controls := newFlex().AddItem(u.theme, 24, 0, false).AddItem(u.profile, 28, 0, false).AddItem(u.context, 0, 1, false)
	u.root = newFlex().SetDirection(tview.FlexRow).AddItem(u.header, 1, 0, false).AddItem(controls, 1, 0, false).AddItem(u.body, 0, 1, true).AddItem(u.status, 1, 0, false).AddItem(u.footer, 1, 0, false)
	u.small = tview.NewTextView().SetText("TUIVORY\n\n터미널을 80열 × 24행 이상으로 넓혀 주세요.\nCtrl+Q 종료").SetTextAlign(tview.AlignCenter)
	u.layers.AddPage("main", u.root, true, true).AddPage("small", u.small, true, false)
	u.app.SetRoot(u.layers, true).SetInputCapture(u.key).SetBeforeDrawFunc(func(_ tcell.Screen) bool { u.reflow(); u.borders(); return false })
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
	fields := u.card(" 입력 · 선택 ")
	u.name = tview.NewInputField().SetLabel("이름     ").SetText("한글과 English").SetFieldWidth(0)
	u.password = tview.NewInputField().SetLabel("암호 예시 ").SetText("sample").SetMaskCharacter('*')
	u.choice = &choice{DropDown: tview.NewDropDown().SetLabel("선택     ").SetOptions([]string{"개발 환경", "검토 환경", "운영 환경"}, nil).SetCurrentOption(0)}
	u.check = tview.NewCheckbox().SetLabel("선택 상태를 유지합니다 ").SetChecked(true)
	u.disabled = tview.NewTextView().SetText("비활성   입력할 수 없는 예시").SetWrap(false)
	fields.AddItem(u.name, 1, 0, true).AddItem(u.password, 1, 0, false).AddItem(u.choice, 1, 0, false).AddItem(u.check, 1, 0, false).AddItem(u.disabled, 1, 0, false)
	hint := tview.NewTextView().SetText("Tab 영역 이동 · 선택박스 Enter 펼침").SetWrap(true)
	fields.AddItem(hint, 0, 1, false)
	u.states = append(u.states, hint)
	actions := u.card(" 버튼 · 상태 ")
	for _, text := range []string{"안내: 색 이외에 문구도 함께 표시합니다.", "정상: 조작 가능한 견본입니다.", "주의: 미리보기는 단말 능력을 바꾸지 않습니다.", "오류: F5로 입력 오류 상태를 켜 보세요."} {
		view := tview.NewTextView().SetText(text).SetWrap(false)
		u.states = append(u.states, view)
		actions.AddItem(view, 1, 0, false)
	}
	row := newFlex()
	labels := []string{"적용", "팝업", "초기화", "비활성"}
	for i, label := range labels {
		index := i
		b := tview.NewButton(label).SetSelectedFunc(func() {
			switch index {
			case 0:
				u.message("적용 예시: " + u.name.GetText())
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
	listCard := u.card(" 목록 · 선택과 포커스 ")
	u.list = tview.NewList().ShowSecondaryText(false)
	for _, label := range []string{"입력창과 선택박스", "버튼과 비활성 상태", "포커스와 선택은 별개", "팝업과 배경 입력 차단"} {
		u.list.AddItem(label, "", 0, nil)
	}
	u.list.SetSelectedFunc(func(i int, text, _ string, _ rune) { u.message(fmt.Sprintf("목록 %d 선택: %s", i+1, text)) })
	listCard.AddItem(u.list, 0, 1, true)
	gridCard := u.card(" 그리드 · Enter 셀 편집 ")
	u.grid = tview.NewTable().SetFixed(1, 0).SetSelectable(true, true).SetSeparator('│')
	for col, text := range []string{"ID", "이름", "상태"} {
		u.grid.SetCell(0, col, tview.NewTableCell(text).SetSelectable(false))
	}
	for i, text := range u.rows {
		u.grid.SetCell(i+1, 0, tview.NewTableCell(fmt.Sprint(i+1)))
		u.grid.SetCell(i+1, 1, tview.NewTableCell(text).SetExpansion(1))
		u.grid.SetCell(i+1, 2, tview.NewTableCell("원본"))
	}
	u.grid.Select(1, 1).SetSelectedFunc(func(row, col int) {
		if row > 0 && col == 1 {
			u.openEdit(row)
		} else {
			u.message("이름 열을 선택하고 Enter로 편집하세요.")
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
	u.message([]string{"입력·목록·그리드를 직접 조작해 보세요.", "역할별 전경·배경과 실제 색상 견본입니다.", "방향키와 PgUp/PgDn으로 안내를 읽으세요."}[index])
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
	u.name.SetText("한글과 English")
	u.password.SetText("sample")
	u.choice.SetCurrentOption(0)
	u.check.SetChecked(true)
	u.invalid = false
	u.rows = []string{"한글 입력 예시", "선택과 포커스", "Enter로 편집"}
	u.changed = map[int]bool{}
	for i, text := range u.rows {
		u.grid.GetCell(i+1, 1).SetText(text)
		u.grid.GetCell(i+1, 2).SetText("원본")
	}
	u.apply()
	u.message("견본 값을 초기화했습니다.")
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
		u.footer.SetText(" F1 도움말  F2 테마  F3 색상  F4 팝업  F5 오류  F6 화면  Ctrl+Q 종료")
	} else {
		u.footer.SetText(" Tab/Shift+Tab 이동 · F1 도움말 · F2 테마 · F3 색상 · F4 팝업 · F5 입력 오류 · F6 화면 전환 · Enter 셀 편집 · Ctrl+Q 종료")
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
현재는 문서의 후보 팔레트를 사용하는 견본입니다.

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

// Protect a leading half of an existing two-cell glyph when a choice list opens.
type wideSafeScreen struct{ tcell.Screen }

func (s wideSafeScreen) SetContent(x, y int, r rune, c []rune, style tcell.Style) {
	if x > 0 {
		_, _, old, w := s.Screen.GetContent(x-1, y)
		if w > 1 {
			s.Screen.SetContent(x-1, y, ' ', nil, old)
		}
	}
	s.Screen.SetContent(x, y, r, c, style)
}

// Choice keeps a wide glyph behind an opened list from hiding its first cell.
type choice struct{ *tview.DropDown }

func (c *choice) Draw(screen tcell.Screen) {
	if c.IsOpen() {
		c.DropDown.Draw(wideSafeScreen{screen})
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
