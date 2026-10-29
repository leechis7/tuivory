package playground

import (
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
	disabledFG, _, _ := s.DisabledStyle().Decompose()
	return Palette{
		"body": {FG: s.Text, BG: s.Background}, "surface": {FG: s.Text, BG: s.Surface},
		"hint": {FG: s.Muted, BG: s.Surface}, "field": {FG: s.FieldText, BG: s.Field},
		"selection": {FG: s.SelectionFG, BG: s.Selection}, "button": {FG: s.FieldText, BG: s.Button},
		"button.focus": {FG: s.SelectionFG, BG: s.Selection}, "disabled": {FG: disabledFG, BG: s.Surface},
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
	style, err := tuivory.TextOnSurface(Palette{"text": role, "surface": surface}, "text", "surface")
	if err != nil {
		panic(err)
	}
	foreground, background, _ := style.Decompose()
	return Pair{FG: foreground, BG: background, Bold: role.Bold}
}
