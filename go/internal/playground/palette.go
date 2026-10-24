package playground

import (
	"math"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go"
)

type Pair = tuivory.Pair
type Palette = tuivory.Palette

var roleNames = candidateRoles()
var themeNames = []string{"dark", "light", "blackwhite"}
var profileNames = []string{"auto", "8", "16", "256", "truecolor"}

func candidateRoles() []string {
	d, err := tuivory.CandidateTokens()
	if err != nil {
		panic(err)
	} // Bundled data is validated during development.
	return d.Roles
}

func loadPalette(theme, profile string) (Palette, error) {
	s, err := tuivory.NewStyles(theme, profile)
	if err != nil {
		return nil, err
	}
	return Palette{
		"body": {FG: s.Text, BG: s.Background}, "surface": {FG: s.Text, BG: s.Surface},
		"hint": {FG: s.Muted, BG: s.Surface}, "field": {FG: s.FieldText, BG: s.Field},
		"selection": {FG: s.SelectionFG, BG: s.Selection}, "button": {FG: s.FieldText, BG: s.Button},
		"button.focus": {FG: s.SelectionFG, BG: s.Selection}, "disabled": {FG: s.Disabled, BG: s.Surface},
		"edited": {FG: s.EditedFG, BG: s.Edited}, "header": {FG: s.Accent, BG: s.Background},
		"editor": {FG: s.EditorText, BG: s.Editor}, "info": {FG: s.Accent, BG: s.Surface},
		"success": {FG: s.Text, BG: s.Surface}, "warning": {FG: s.Warning, BG: s.Surface},
		"error": {FG: s.Text, BG: s.Surface}, "focus.border": {FG: s.Focus, BG: s.Surface},
	}, nil
}

func detectedProfile(colors int) string {
	return tuivory.ProfileForColors(colors, false)
}

func contains(values []string, value string) bool {
	for _, v := range values {
		if v == value {
			return true
		}
	}
	return false
}

// A semantic foreground must be checked again on its actual component surface.
// Use the surface's validated body text when the colored role cannot contrast.
func textOnSurface(role, surface Pair) Pair {
	lum := func(c tcell.Color) float64 {
		r, g, b := c.RGB()
		linear := func(v int32) float64 {
			f := float64(v) / 255
			if f <= .04045 {
				return f / 12.92
			}
			return math.Pow((f+.055)/1.055, 2.4)
		}
		return .2126*linear(r) + .7152*linear(g) + .0722*linear(b)
	}
	low, high := lum(role.FG), lum(surface.BG)
	if low > high {
		low, high = high, low
	}
	fg := role.FG
	if (high+.05)/(low+.05) < 4.5 {
		fg = surface.FG
	}
	return Pair{FG: fg, BG: surface.BG, Bold: role.Bold}
}
