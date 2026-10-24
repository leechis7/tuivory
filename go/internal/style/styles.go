package style

import "github.com/gdamore/tcell/v2"

func (s Styles) FieldStyle() tcell.Style {
	return tcell.StyleDefault.Foreground(s.FieldText).Background(s.Field)
}
func (s Styles) SelectionStyle() tcell.Style {
	return tcell.StyleDefault.Foreground(s.SelectionFG).Background(s.Selection)
}
func (s Styles) ButtonStyle() tcell.Style {
	return tcell.StyleDefault.Foreground(s.FieldText).Background(s.Button)
}
func (s Styles) ButtonFocusStyle() tcell.Style { return s.SelectionStyle().Underline(true) }
func (s Styles) DisabledStyle() tcell.Style {
	return tcell.StyleDefault.Foreground(s.Disabled).Background(s.Surface)
}
func (s Styles) EditedStyle() tcell.Style {
	return tcell.StyleDefault.Foreground(s.EditedFG).Background(s.Edited)
}
func (s Styles) EditorStyle() tcell.Style {
	return tcell.StyleDefault.Foreground(s.EditorText).Background(s.Editor)
}

// BorderColor retains the source's contrast choice for the actual widget background.
func BorderColor(theme, profile string, styles Styles, focused bool, background tcell.Color) tcell.Color {
	r, g, b := background.RGB()
	light := r >= 0 && 299*r+587*g+114*b >= 128000
	if theme == "blackwhite" {
		if light {
			return tcell.ColorBlack
		}
		return tcell.ColorSilver
	}
	if focused {
		if light {
			if profile == "8" || profile == "16" {
				return tcell.ColorNavy
			}
			if profile == "256" {
				return indexed(25)
			}
			return tcell.GetColor("#005fcc")
		}
		if profile == "8" || profile == "16" {
			if profile == "8" {
				return indexed(3)
			}
			return tcell.ColorWhite
		}
		return styles.Focus
	}
	if profile == "8" || profile == "16" {
		if light {
			return tcell.ColorBlack
		}
		return tcell.ColorSilver
	}
	if profile == "256" {
		return indexed(244)
	}
	if light {
		return tcell.GetColor("#66758a")
	}
	return tcell.GetColor("#8190a4")
}
