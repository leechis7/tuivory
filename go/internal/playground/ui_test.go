package playground

import (
	"fmt"
	"math"
	"testing"
	"unicode"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go"
	"github.com/rivo/tview"
)

func testUI(t *testing.T) (*UI, tcell.SimulationScreen) {
	t.Helper()
	return testUIOptions(t, Options{Theme: "dark", Colors: "truecolor", Mouse: true})
}
func testUIOptions(t *testing.T, options Options) (*UI, tcell.SimulationScreen) {
	t.Helper()
	terminal := tcell.NewSimulationScreen("UTF-8")
	if err := terminal.Init(); err != nil {
		t.Fatal(err)
	}
	app := tview.NewApplication().SetScreen(terminal)
	terminal.SetSize(120, 36)
	t.Cleanup(terminal.Fini)
	ui, err := New(app, terminal, options)
	if err != nil {
		t.Fatal(err)
	}
	drawUI(ui, terminal)
	return ui, terminal
}
func drawUI(ui *UI, terminal tcell.Screen) {
	w, h := terminal.Size()
	ui.reflow()
	ui.borders()
	ui.layers.SetRect(0, 0, w, h)
	ui.layers.Draw(terminal)
	terminal.Show()
}
func deliver(ui *UI, key tcell.Key, r rune) {
	event := ui.key(tcell.NewEventKey(key, r, 0))
	if event != nil {
		ui.app.GetFocus().InputHandler()(event, func(p tview.Primitive) { ui.app.SetFocus(p) })
	}
}
func TestThemeProfileRoundTripRetainsWorkAndFocus(t *testing.T) {
	ui, terminal := testUI(t)
	ui.name.SetText("유지할 한글 입력")
	ui.check.SetChecked(false)
	ui.choice.SetCurrentOption(2)
	ui.list.SetCurrentItem(2)
	ui.grid.Select(2, 1)
	ui.app.SetFocus(ui.grid)
	deliver(ui, tcell.KeyEnter, 0)
	if ui.popup == nil || ui.popup.input == nil {
		t.Fatal("grid did not open editor")
	}
	ui.popup.input.SetText("바꾼 값")
	deliver(ui, tcell.KeyTab, 0)
	deliver(ui, tcell.KeyEnter, 0)
	if ui.popup != nil || ui.grid.GetCell(2, 1).Text != "바꾼 값" || ui.grid.GetCell(2, 2).Text != "* 변경됨" {
		t.Fatal("cell change not applied")
	}
	for themeIndex, theme := range themeNames {
		for profileIndex, profile := range profileNames[1:] {
			ui.theme.SetCurrentOption(themeIndex)
			ui.profile.SetCurrentOption(profileIndex + 1)
			drawUI(ui, terminal)
			if ui.name.GetText() != "유지할 한글 입력" || ui.check.IsChecked() || ui.list.GetCurrentItem() != 2 || ui.app.GetFocus() != ui.grid || ui.grid.GetCell(2, 1).Text != "바꾼 값" {
				t.Fatalf("theme/profile changed user state: %s/%s", theme, profile)
			}
			selected, _ := ui.choice.GetCurrentOption()
			if selected != 2 {
				t.Fatal("choice changed")
			}
			row, col := ui.grid.GetSelection()
			if row != 2 || col != 1 {
				t.Fatal("grid selection changed")
			}
		}
	}
}
func TestPopupTrapsTabBlocksMouseAndRestoresFocus(t *testing.T) {
	ui, terminal := testUI(t)
	ui.app.SetFocus(ui.name)
	ui.name.SetText("keep")
	deliver(ui, tcell.KeyF4, 0)
	drawUI(ui, terminal)
	if ui.popup == nil {
		t.Fatal("popup missing")
	}
	close := ui.popup.close
	deliver(ui, tcell.KeyTab, 0)
	if ui.app.GetFocus() != close {
		t.Fatal("Tab did not reach close")
	}
	deliver(ui, tcell.KeyTab, 0)
	if ui.app.GetFocus() != ui.popup.text {
		t.Fatal("Tab escaped popup")
	}
	before := ui.app.GetFocus()
	event := tcell.NewEventMouse(0, 0, tcell.Button1, 0)
	consumed, _ := ui.layers.MouseHandler()(tview.MouseLeftClick, event, func(p tview.Primitive) { ui.app.SetFocus(p) })
	if !consumed || ui.app.GetFocus() != before || ui.popup == nil || ui.name.GetText() != "keep" {
		t.Fatal("outside click leaked to background")
	}
	deliver(ui, tcell.KeyF2, 0)
	deliver(ui, tcell.KeyF3, 0)
	drawUI(ui, terminal)
	if ui.popup == nil || ui.app.GetFocus() != before {
		t.Fatal("theme change replaced popup or focus")
	}
	deliver(ui, tcell.KeyEscape, 0)
	if ui.popup != nil || ui.app.GetFocus() != ui.name {
		t.Fatal("Escape failed to restore focus")
	}
}
func TestChoiceEscapeAndSmallWindowRecovery(t *testing.T) {
	ui, terminal := testUI(t)
	ui.app.SetFocus(ui.choice)
	deliver(ui, tcell.KeyEnter, 0)
	if !ui.choice.IsOpen() {
		t.Fatal("choice did not open")
	}
	deliver(ui, tcell.KeyEscape, 0)
	if ui.choice.IsOpen() {
		t.Fatal("choice did not close")
	}
	ui.openPreview()
	popup := ui.popup
	terminal.SetSize(60, 18)
	drawUI(ui, terminal)
	if !ui.smallMode {
		t.Fatal("small window not detected")
	}
	terminal.SetSize(80, 24)
	drawUI(ui, terminal)
	if ui.smallMode || ui.popup != popup {
		t.Fatal("resize lost popup")
	}
	deliver(ui, tcell.KeyEscape, 0)
	drawUI(ui, terminal)
	for _, p := range ui.focusables() {
		if p == ui.nav {
			t.Fatal("hidden navigation remains in Tab cycle")
		}
	}
}
func TestPaletteGridAndFocusedBorderAcrossProfiles(t *testing.T) {
	ui, terminal := testUI(t)
	for _, theme := range themeNames {
		for _, profile := range profileNames[1:] {
			t.Run(theme+"/"+profile, func(t *testing.T) {
				ui.options.Theme, ui.options.Colors = theme, profile
				ui.apply()
				ui.app.SetFocus(ui.name)
				drawUI(ui, terminal)
				x, y, _, _ := ui.cards[0].GetRect()
				r, _, _, _ := terminal.GetContent(x, y)
				if r != tview.Borders.TopLeftFocus {
					t.Fatalf("focused field card corner %q", r)
				}
				if ui.tokens.GetRowCount() != 17 {
					t.Fatal("token roles missing")
				}
				p, err := loadPalette(theme, profile)
				if err != nil {
					t.Fatal(err)
				}
				for name, pair := range p {
					if pair.FG == pair.BG {
						t.Fatal("invisible role", name)
					}
				}
				deliver(ui, tcell.KeyF6, 0)
				drawUI(ui, terminal)
				if ui.page != 1 || ui.app.GetFocus() != ui.tokens {
					t.Fatal("token page not reachable")
				}
				ui.nav.SetCurrentItem(0)
				ui.showPage(0)
			})
		}
	}
}
func TestOptionsRejectUnsupportedValues(t *testing.T) {
	app := tview.NewApplication()
	screen := tcell.NewSimulationScreen("")
	_, err := New(app, screen, Options{Theme: "unknown"})
	if err == nil {
		t.Fatal("invalid theme accepted")
	}
}
func Example_detectedProfile() {
	fmt.Println(detectedProfile(8), detectedProfile(16), detectedProfile(256), detectedProfile(1<<24)) // Output: 8 16 256 truecolor
}

// Detect real widget defaults leaking black text/background into light themes.
func TestRenderedTextContrastAcrossProfiles(t *testing.T) {
	ui, terminal := testUI(t)
	luminance := func(c tcell.Color) float64 {
		r, g, b := c.RGB()
		linear := func(v int32) float64 {
			f := float64(v) / 255
			if f <= 0.04045 {
				return f / 12.92
			}
			return math.Pow((f+0.055)/1.055, 2.4)
		}
		return .2126*linear(r) + .7152*linear(g) + .0722*linear(b)
	}
	for themeIndex, theme := range themeNames {
		for profileIndex, profile := range profileNames[1:] {
			ui.theme.SetCurrentOption(themeIndex)
			ui.profile.SetCurrentOption(profileIndex + 1)
			for page := 0; page < 3; page++ {
				ui.nav.SetCurrentItem(page)
				ui.showPage(page)
				ui.app.SetFocus(ui.pageFocus())
				drawUI(ui, terminal)
				for y := 0; y < 36; y++ {
					for x := 0; x < 120; x++ {
						r, _, style, _ := terminal.GetContent(x, y)
						if !unicode.IsLetter(r) && !unicode.IsDigit(r) {
							continue
						}
						fg, bg, attrs := style.Decompose()
						if attrs&tcell.AttrDim != 0 {
							continue
						}
						if !fg.Valid() || !bg.Valid() {
							t.Fatalf("unresolved text style at %s/%s page%d %d,%d", theme, profile, page, x, y)
						}
						low, high := luminance(fg), luminance(bg)
						if low > high {
							low, high = high, low
						}
						target := 4.5
						if fg == ui.palette["disabled"].FG && bg == ui.palette["surface"].BG {
							target = 2.0
						}
						if ratio := (high + .05) / (low + .05); ratio < target {
							t.Fatalf("text contrast %.2f at %s/%s page%d %d,%d %q", ratio, theme, profile, page, x, y, r)
						}
					}
				}
			}
		}
	}
}

// Inspect physical output after Show, including every corner and both edge directions.
func TestAllPlaygroundAreasUseFocusBorders(t *testing.T) {
	for _, theme := range themeNames {
		for _, profile := range profileNames[1:] {
			t.Run(theme+"/"+profile, func(t *testing.T) {
				ui, screen := testUIOptions(t, Options{Theme: theme, Colors: profile, Mouse: true})
				styler, _ := tuivory.New(theme, profile)
				check := func(frame tview.Primitive, focused bool) {
					t.Helper()
					x, y, w, h := frame.GetRect()
					cells, cols, _ := screen.GetContents()
					corners := []rune{'┌', '┐', '└', '┘', '─', '│'}
					if focused {
						corners = []rune{'╔', '╗', '╚', '╝', '═', '║'}
					}
					points := [][3]int{{x, y, 0}, {x + w - 1, y, 1}, {x, y + h - 1, 2}, {x + w - 1, y + h - 1, 3}, {x + 1, y + h - 1, 4}, {x, y + 1, 5}}
					for _, at := range points {
						c := cells[at[1]*cols+at[0]]
						want := string(corners[at[2]])
						if string(c.Runes) != want || string(c.Bytes) != want {
							t.Fatalf("focused=%t point=%v got=%q/%q want=%q", focused, at, c.Runes, c.Bytes, want)
						}
					}
				}
				scenes := []struct {
					page          int
					target, frame tview.Primitive
				}{
					{0, ui.name, ui.cards[0]}, {0, ui.buttons[0], ui.cards[1]}, {0, ui.list, ui.cards[2]}, {0, ui.grid, ui.cards[3]},
					{0, ui.nav, ui.nav}, {1, ui.tokens, ui.tokens}, {2, ui.guide, ui.guide},
				}
				for _, scene := range scenes {
					ui.nav.SetCurrentItem(scene.page)
					ui.showPage(scene.page)
					ui.app.SetFocus(scene.target)
					drawUI(ui, screen)
					check(scene.frame, true)
					if box, ok := scene.frame.(interface{ GetBackgroundColor() tcell.Color }); ok {
						x, y, _, _ := scene.frame.GetRect()
						_, _, got, _ := screen.GetContent(x, y)
						fg, _, _ := got.Decompose()
						want, _, _ := styler.Styles.BorderStyle(true, box.GetBackgroundColor()).Decompose()
						if fg != want {
							t.Fatal("focused border color differs", scene.page)
						}
					}
					if scene.target == ui.nav {
						ui.app.SetFocus(ui.name)
					} else {
						ui.app.SetFocus(ui.nav)
					}
					drawUI(ui, screen)
					check(scene.frame, false)
				}
				ui.nav.SetCurrentItem(0)
				ui.showPage(0)
				ui.app.SetFocus(ui.name)
				for _, open := range []func(){ui.openHelp, ui.openPreview, func() { ui.openEdit(1) }} {
					previous := ui.app.GetFocus()
					open()
					drawUI(ui, screen)
					check(ui.popup.card, true)
					ui.closePopup()
					drawUI(ui, screen)
					if ui.app.GetFocus() != previous {
						t.Fatal("popup lost original focus")
					}
					check(ui.cards[0], true)
				}
			})
		}
	}
}
