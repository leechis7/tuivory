package tuivory

import (
	"fmt"
	"math"

	"github.com/gdamore/tcell/v2"
)

// TextOnSurface binds a text role to the actual surface without changing tokens.
// Use a better surface foreground below the role target (disabled 2:1, others 4.5:1).
// Use raw palette styles for explicit field, selection, edit or custom backgrounds.
func TextOnSurface(palette Palette, role, surface string) (tcell.Style, error) {
	text, ok := palette[role]
	if !ok {
		return tcell.StyleDefault, fmt.Errorf("missing text role %q", role)
	}
	base, ok := palette[surface]
	if !ok {
		return tcell.StyleDefault, fmt.Errorf("missing surface role %q", surface)
	}
	text.BG = base.BG
	current := surfaceContrast(text.FG, base.BG)
	target := 4.5
	if role == "disabled" {
		target = 2.0
	}
	if current < target && surfaceContrast(base.FG, base.BG) > current {
		text.FG = base.FG
	}
	style := disabledCue(palette, role, text.Style())
	if role == "disabled" && text.FG == base.FG {
		style = style.Bold(false).Dim(true)
	}
	return style, nil
}

func surfaceContrast(foreground, background tcell.Color) float64 {
	luminance := func(color tcell.Color) float64 {
		r, g, b := color.RGB()
		// Terminal-inherited colors have no reference RGB to compare.
		if r < 0 || g < 0 || b < 0 {
			return math.NaN()
		}
		channel := func(c int32) float64 {
			v := float64(c) / 255
			if v <= 0.04045 {
				return v / 12.92
			}
			return math.Pow((v+0.055)/1.055, 2.4)
		}
		return 0.2126*channel(r) + 0.7152*channel(g) + 0.0722*channel(b)
	}
	a, b := luminance(foreground), luminance(background)
	if a > b {
		a, b = b, a
	}
	return (b + 0.05) / (a + 0.05)
}

func plainTextRole(role string) bool {
	switch role {
	case "body", "hint", "disabled", "info", "success", "warning", "error":
		return true
	}
	return false
}

func componentStyle(palette Palette, role string) tcell.Style {
	if plainTextRole(role) {
		style, err := TextOnSurface(palette, role, "surface")
		if err != nil {
			panic(err)
		}
		return style
	}
	pair, ok := palette[role]
	if !ok {
		panic("component: missing role " + role)
	}
	return pair.Style()
}

// ControlStyleOnSurface binds ordinary control text to a host-selected surface.
// Selection and edited backgrounds remain explicit; ControlStyle stays raw.
func ControlStyleOnSurface(palette Palette, state ControlState, focused bool, surface string) (tcell.Style, error) {
	v := state.Visual()
	if !plainTextRole(v.Role) {
		return ControlStyle(palette, state, focused)
	}
	style, err := TextOnSurface(palette, v.Role, surface)
	return style.Underline(focused && v.Focusable), err
}

// Keep a brightness cue when the palette has no distinct disabled foreground.
func disabledCue(palette Palette, role string, style tcell.Style) tcell.Style {
	if role == "disabled" {
		fg, _, _ := style.Decompose()
		if body, ok := palette["body"]; ok && fg == body.FG {
			return style.Bold(false).Dim(true)
		}
	}
	return style
}
