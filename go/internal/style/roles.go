package style

import "github.com/gdamore/tcell/v2"

type Surface uint8

const (
	Canvas Surface = iota
	Panel
	Field
	Footer
	Editor
)

type TextRole uint8

const (
	Body TextRole = iota
	Hint
	Accent
	Warning
)

func (s Styles) Theme() string    { return s.theme }
func (s Styles) Profile() string  { return s.profile }
func (s Styles) ansiColors() bool { return s.profile == "8" || s.profile == "16" }

func (s Styles) SurfaceColor(surface Surface) tcell.Color {
	switch surface {
	case Panel:
		return s.Surface
	case Field:
		return s.Field
	case Footer:
		return s.Footer
	case Editor:
		return s.Editor
	default:
		return s.Background
	}
}

func (s Styles) SurfaceText(surface Surface) tcell.Color {
	switch surface {
	case Field:
		return s.FieldText
	case Editor:
		return s.EditorText
	default:
		return s.Text
	}
}

func (s Styles) TextColor(role TextRole) tcell.Color {
	switch role {
	case Hint:
		return s.Muted
	case Accent:
		return s.Accent
	case Warning:
		return s.Warning
	default:
		return s.Text
	}
}

func (s Styles) TextStyle(surface Surface, role TextRole) tcell.Style {
	fg := s.TextColor(role)
	if surface == Field {
		fg = s.FieldText
	}
	return tcell.StyleDefault.Foreground(fg).Background(s.SurfaceColor(surface))
}

func (s Styles) BorderStyle(focused bool, background tcell.Color) tcell.Style {
	return tcell.StyleDefault.Foreground(BorderColor(s.theme, s.profile, s, focused, background)).Background(background)
}

func (s Styles) DropDownStyle() tcell.Style {
	if s.ansiColors() && s.theme != "blackwhite" {
		return s.SelectionStyle()
	}
	return tcell.StyleDefault.Foreground(s.Text).Background(s.Footer)
}

func (s Styles) TabStyle(active bool) tcell.Style {
	if active {
		return s.ButtonFocusStyle()
	}
	return s.ButtonStyle()
}

// FooterButtonStyle returns the footer text style.
//
// Deprecated: Use TextStyle(Footer, Body), which has the same colors and attributes.
func (s Styles) FooterButtonStyle() tcell.Style {
	return tcell.StyleDefault.Foreground(s.Text).Background(s.Footer)
}

// ComparisonHeaderStyle is the generic selected-column header used in LazyOra's
// keymap comparison. The host supplies which column is current.
func (s Styles) ComparisonHeaderStyle(current bool) tcell.Style {
	if current {
		return s.TextStyle(Field, Body).Underline(true)
	}
	if s.theme == "blackwhite" {
		return tcell.StyleDefault.Foreground(tcell.ColorBlack).Background(tcell.ColorSilver)
	}
	return s.SelectionStyle().Underline(true)
}

func (s Styles) SplitterStyle() tcell.Style {
	return tcell.StyleDefault.Foreground(s.Button).Background(s.Background)
}

// PopupBackdrop preserves the original attributes and the original limited-mode
// override; limited is an explicit host preference, separate from color count.
func (s Styles) PopupBackdrop(base tcell.Style, limited bool) tcell.Style {
	result := base.Foreground(s.Muted).Background(s.Background).Dim(true)
	if limited {
		result = result.Foreground(tcell.ColorSilver).Background(tcell.ColorBlack)
	}
	return result
}

// PopupCardStyle returns panel body text style.
//
// Deprecated: Use TextStyle(Panel, Body), which returns the same style.
func (s Styles) PopupCardStyle() tcell.Style { return s.TextStyle(Panel, Body) }
func (s Styles) PopupShadowStyle() tcell.Style {
	return tcell.StyleDefault.Background(tcell.ColorBlack)
}
