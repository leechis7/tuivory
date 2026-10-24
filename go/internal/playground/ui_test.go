package playground

import (
	"fmt"
	"math"
	"testing"
	"unicode"

	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

func testUI(t *testing.T) (*UI, tcell.SimulationScreen) {
	t.Helper()
	terminal := tcell.NewSimulationScreen("UTF-8")
	if err := terminal.Init(); err != nil {
		t.Fatal(err)
	}
	app := tview.NewApplication().SetScreen(terminal)
	terminal.SetSize(120, 36)
	t.Cleanup(terminal.Fini)
	ui, err := New(app, terminal, Options{Theme: "dark", Colors: "truecolor", Mouse: true})
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
						if ratio := (high + .05) / (low + .05); ratio < 4.5 {
							t.Fatalf("text contrast %.2f at %s/%s page%d %d,%d %q", ratio, theme, profile, page, x, y, r)
						}
					}
				}
			}
		}
	}
}
