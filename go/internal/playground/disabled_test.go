package playground

import (
	"testing"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go"
)

// Inspect the physical buffer, rather than just palette definitions. In an
// 8-color palette the disabled cue lives in attributes, not the RGB pair.
func TestDisabledTokenSampleAfterShowAndPaletteRoundTrip(t *testing.T) {
	u, screen := testUI(t)
	for _, ti := range []int{0, 1, 2, 0} {
		for pi, profile := range profileNames[1:] {
			u.theme.SetCurrentOption(ti)
			u.profile.SetCurrentOption(pi + 1)
			u.showPage(1)
			drawUI(u, screen)
			styles, _ := tuivory.NewStyles(themeNames[ti], profile)
			wantFG, wantBG, wantAttrs := styles.DisabledStyle().Decompose()
			for i, role := range roleNames {
				if role != "disabled" {
					continue
				}
				x, y, width := u.tokens.GetCell(i+1, 3).GetLastPosition()
				if width < 3 {
					t.Fatal("disabled sample is not visible")
				}
				cells, columns, _ := screen.GetContents()
				cell := cells[y*columns+x+1]
				fg, bg, attrs := cell.Style.Decompose()
				if fg != wantFG || bg != wantBG || attrs&tcell.AttrDim != wantAttrs&tcell.AttrDim {
					t.Errorf("%s/%s: sample %v/%v attrs=%v, disabled style %v/%v attrs=%v", themeNames[ti], profile, fg, bg, attrs, wantFG, wantBG, wantAttrs)
				}
			}
		}
	}
}
