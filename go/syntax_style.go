package tuivory

import "strings"

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
