package playground

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"testing"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go"
)

// The Rust host ships a snapshot of this example's Go palette, separate from
// the public candidate palette. Compare it here so later Go fixes cannot drift.
func TestRustPlaygroundPaletteMatchesGo(t *testing.T) {
	if _, err := os.Stat("../../../rust/examples/playground"); os.IsNotExist(err) {
		t.Skip("cross-language checkout check; Rust examples are not in this Go module")
	}
	rgb := func(c tcell.Color) string { r, g, b := c.RGB(); return fmt.Sprintf("#%02x%02x%02x", r, g, b) }
	palettes := map[string]any{}
	extra := []string{"sample.dropdown", "sample.grid.body", "sample.grid.stripe", "sample.grid.current", "sample.grid.header", "sample.grid.divider", "sample.border", "sample.border.focus"}
	for _, theme := range themeNames {
		for _, profile := range profileNames[1:] {
			palette, err := loadPalette(theme, profile)
			if err != nil {
				t.Fatal(err)
			}
			pairs := map[string]any{}
			styles, err := tuivory.NewStyles(theme, profile)
			if err != nil {
				t.Fatal(err)
			}
			additional := []tcell.Style{styles.DropDownStyle(), styles.GridCellStyle(tuivory.CellState{Row: 1}), styles.GridCellStyle(tuivory.CellState{Row: 2}), styles.GridCellStyle(tuivory.CellState{Row: 1, CurrentRow: true}), styles.GridHeaderStyle(false), tcell.StyleDefault.Foreground(styles.GridDividerColor()).Background(styles.GridColors().Background), styles.BorderStyle(false, styles.Surface), styles.BorderStyle(true, styles.Surface)}
			for i, role := range extra {
				fg, bg, _ := additional[i].Decompose()
				palette[role] = Pair{FG: fg, BG: bg}
			}
			for role, pair := range palette {
				pairs[role] = map[string]string{"foreground": colorLabel(pair.FG), "background": colorLabel(pair.BG), "referenceForeground": rgb(pair.FG), "referenceBackground": rgb(pair.BG), "fontWeight": "none"}
			}
			palettes[theme+"-"+profile] = pairs
		}
	}
	data, err := json.MarshalIndent(map[string]any{"format": "tuivory.tokens.draft", "roles": append(append([]string{}, roleNames...), extra...), "palettes": palettes}, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	data = append(data, '\n')
	path := "../../../rust/examples/playground/go-palette.json"
	if os.Getenv("TUIVORY_UPDATE_GO_PLAYGROUND_PALETTE") == "1" {
		if err := os.WriteFile(path, data, 0644); err != nil {
			t.Fatal(err)
		}
	}
	actual, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if string(actual) != string(data) {
		t.Fatal("Rust playground palette differs from Go; regenerate with TUIVORY_UPDATE_GO_PLAYGROUND_PALETTE=1")
	}
	source, err := os.ReadFile("../../../rust/examples/playground/app.rs")
	if err != nil {
		t.Fatal(err)
	}
	for _, guide := range []string{guideText, guideTextEN} {
		if !strings.Contains(string(source), guide) {
			t.Fatal("Rust and Go playground guides differ")
		}
	}
}

func TestFirstPaintCardBackgroundMatchesThemeRoundTrip(t *testing.T) {
	for _, theme := range themeNames {
		for _, profile := range profileNames[1:] {
			t.Run(theme+"-"+profile, func(t *testing.T) {
				u, screen := testUIOptions(t, Options{Theme: theme, Colors: profile})
				drawUI(u, screen)
				styles, _ := tuivory.NewStyles(theme, profile)
				for pass := 0; pass < 2; pass++ {
					cells, columns, _ := screen.GetContents()
					for _, point := range [][2]int{{23, 10}, {80, 10}} {
						_, bg, _ := cells[point[1]*columns+point[0]].Style.Decompose()
						if bg != styles.Surface {
							t.Errorf("pass %d at %v: background %v, want %v", pass, point, bg, styles.Surface)
						}
					}
					for i := 0; i < len(themeNames); i++ {
						u.cycleTheme()
					}
					drawUI(u, screen)
				}
			})
		}
	}
}
