package playground

import (
	"strings"
	"testing"
	"unicode"

	"github.com/gdamore/tcell/v2"
)

func TestLanguageDefaultsAndValidation(t *testing.T) {
	u, _ := testUI(t)
	if u.options.Lang != "ko" || u.name.GetLabel() != "이름     " {
		t.Fatal("Korean must remain the default")
	}
	// Invalid language must fail before attempting terminal initialization.
	if err := Run(Options{Lang: "fr"}); err == nil || !strings.Contains(err.Error(), "ko or en") {
		t.Fatalf("unexpected language validation: %v", err)
	}
}

func TestEnglishUIStatesAndRendering(t *testing.T) {
	u, terminal := testUIOptions(t, Options{Lang: "en", Colors: "truecolor"})
	assertEnglish := func() {
		t.Helper()
		terminal.Clear()
		drawUI(u, terminal)
		w, h := terminal.Size()
		for y := 0; y < h; y++ {
			for x := 0; x < w; x++ {
				r, _, _, _ := terminal.GetContent(x, y)
				if unicode.Is(unicode.Hangul, r) {
					t.Fatalf("untranslated text at %d,%d: %c", x, y, r)
				}
			}
		}
	}
	if u.name.GetLabel() != "Name     " || u.name.GetText() != "Hello, world!" {
		t.Fatal("English inputs not initialized")
	}
	for _, size := range [][2]int{{120, 36}, {80, 24}, {60, 20}, {120, 36}} {
		terminal.SetSize(size[0], size[1])
		assertEnglish()
	}
	for page := 0; page < 3; page++ {
		u.showPage(page)
		assertEnglish()
	}
	u.showPage(0)
	u.openHelp()
	assertEnglish()
	u.closePopup()
	u.openPreview()
	assertEnglish()
	u.closePopup()
	deliver(u, tcell.KeyF5, 0)
	if u.name.GetLabel() != "Error! Name " {
		t.Fatal("English error indicator missing")
	}
	assertEnglish()
	u.name.SetText("Keep this input")
	u.openEdit(1)
	u.popup.input.SetText("Edited sample")
	u.popup.save.InputHandler()(tcell.NewEventKey(tcell.KeyEnter, 0, 0), nil)
	if u.grid.GetCell(1, 2).Text != "* Edited" {
		t.Fatal("English edited marker missing")
	}
	for theme := range themeNames {
		for profile := range profileNames {
			u.theme.SetCurrentOption(theme)
			u.profile.SetCurrentOption(profile)
			assertEnglish()
			if u.name.GetText() != "Keep this input" || u.grid.GetCell(1, 1).Text != "Edited sample" {
				t.Fatal("theme or profile change lost application state")
			}
		}
	}
	u.reset()
	assertEnglish()
	if u.name.GetText() != "Hello, world!" || u.grid.GetCell(1, 2).Text != "Original" {
		t.Fatal("reset did not restore English samples")
	}
}
