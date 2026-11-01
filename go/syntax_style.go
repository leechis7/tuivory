package tuivory

import "strings"

var darkEightSyntaxHook = func() func(string, Style) Style {
	styles, _ := NewStyles("dark", "8")
	return SyntaxStyleFunc(styles)
}()

// Recognize the complete default dark ANSI-8 palette rather than guessing from
// one foreground: monochrome, richer and custom palettes retain their styling.
func lowColorSyntaxStyle(p Palette, role string, base Style) Style {
	if p["surface"].BG != ColorBlack || p["warning"].FG != ColorOlive || p["body"].FG != ColorSilver {
		return base
	}
	for _, pair := range p {
		if pair.FG.IsRGB() || pair.BG.IsRGB() || pair.FG&^ColorValid > 7 || pair.BG&^ColorValid > 7 {
			return base
		}
	}
	return darkEightSyntaxHook(role, base)
}

// SyntaxPaletteRole maps semantic syntax styles to existing shared role colors.
// Rendering binds these foregrounds to the actual surface, never a token box.
func SyntaxPaletteRole(role string) string {
	switch strings.TrimPrefix(role, "syntax.") {
	case "keyword":
		return "info"
	case "function":
		return "success"
	case "type":
		return "header"
	case "string":
		return "warning"
	case "number":
		return "edited"
	case "comment":
		return "hint"
	case "parameter":
		return "error"
	default:
		return "body"
	}
}

// SyntaxStyleFunc adapts the existing seven-role Go syntax colors, including
// monochrome and limited-color attributes, to a shared editor's optional hook.
func SyntaxStyleFunc(styles Styles) func(string, Style) Style {
	kinds := map[string]SyntaxKind{"keyword": SyntaxKeyword, "function": SyntaxFunction, "type": SyntaxType, "string": SyntaxString, "number": SyntaxNumber, "comment": SyntaxComment, "parameter": SyntaxParameter}
	return func(role string, base Style) Style {
		return styles.SyntaxStyle(kinds[strings.TrimPrefix(role, "syntax.")], base)
	}
}
