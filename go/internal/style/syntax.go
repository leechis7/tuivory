package style

import "github.com/gdamore/tcell/v2"

// SyntaxKind is supplied by the host lexer; TUIVORY does not parse source code.
type SyntaxKind uint8

const (
	SyntaxKeyword SyntaxKind = iota + 1
	SyntaxFunction
	SyntaxType
	SyntaxString
	SyntaxNumber
	SyntaxComment
	SyntaxParameter
)

var syntaxRichColors = [...]tcell.Color{0, tcell.GetColor("#204a87"), tcell.GetColor("#006b73"), tcell.GetColor("#5951a0"), tcell.GetColor("#a3273a"), tcell.GetColor("#6945a3"), tcell.GetColor("#526a43"), tcell.GetColor("#8b4f00")}
var syntaxANSIColors = [...]tcell.Color{0, tcell.ColorNavy, tcell.ColorTeal, tcell.ColorPurple, tcell.ColorMaroon, tcell.ColorPurple, tcell.ColorGreen, tcell.ColorMaroon}

var syntaxDarkColors = [...]tcell.Color{0, tcell.GetColor("#8db8ff"), tcell.GetColor("#73d7ce"), tcell.GetColor("#c7adff"), tcell.GetColor("#efa3aa"), tcell.GetColor("#ebcd79"), tcell.GetColor("#a2bb98"), tcell.GetColor("#f2bc84")}
var syntaxDarkANSIColors = [...]tcell.Color{0, tcell.ColorAqua, tcell.ColorWhite, tcell.ColorFuchsia, tcell.ColorYellow, tcell.ColorYellow, tcell.ColorLime, tcell.ColorWhite}

func syntaxTokenStyle(kind SyntaxKind, limited bool, base tcell.Style) tcell.Style {
	colors := syntaxRichColors
	if limited {
		colors = syntaxANSIColors
	}
	_, bg, _ := base.Decompose()
	r, g, b := bg.RGB()
	if r >= 0 && 299*r+587*g+114*b < 128000 {
		colors = syntaxDarkColors
		if limited {
			colors = syntaxDarkANSIColors
		}
	}
	style := base.Foreground(colors[kind])
	if !limited && (kind == SyntaxKeyword || kind == SyntaxParameter) {
		style = style.Bold(true)
	}
	return style
}

func (s Styles) SyntaxStyle(kind SyntaxKind, base tcell.Style) tcell.Style {
	if kind < SyntaxKeyword || kind > SyntaxParameter {
		return base
	}
	if s.theme == "blackwhite" {
		return base.Bold(false).Underline(kind == SyntaxKeyword || kind == SyntaxParameter).Italic(kind == SyntaxComment)
	}
	p := s.profile
	_, bg, _ := base.Decompose()
	r, g, b := bg.RGB()
	dark := r >= 0 && 299*r+587*g+114*b < 128000
	if p == "8" {
		fg := indexed(7)
		if !dark {
			fg = indexed(0)
		}
		if kind == SyntaxKeyword && !dark {
			fg = indexed(4)
		}
		if kind == SyntaxParameter {
			fg = indexed(3)
			if !dark {
				fg = indexed(1)
			}
		}
		return base.Foreground(fg).Bold(false).Underline(kind == SyntaxKeyword)
	}
	if p == "256" {
		values := [...]int{0, 25, 23, 54, 124, 54, 22, 94}
		if dark {
			values = [...]int{0, 117, 117, 183, 217, 222, 114, 222}
		}
		return base.Foreground(indexed(values[kind])).Bold(false)
	}
	return syntaxTokenStyle(kind, p == "16", base)
}
