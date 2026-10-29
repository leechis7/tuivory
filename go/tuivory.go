// Package tuivory provides reusable TUI components and styles through one import.
// Component models and renderers manage internal interaction and presentation.
// Hosts compose screens and supply scope order, global keys, data and actions.
// New creates a Styler for existing widgets; shared components also accept the
// candidate palette. Hosts retain terminal lifecycle and business I/O.
package tuivory

import (
	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go/internal/style"
	"github.com/leechis7/tuivory/go/internal/tokens"
	widgets "github.com/leechis7/tuivory/go/internal/widgets"
)

// Aliases keep state and method signatures usable without subpackage imports.
type (
	Styler        = widgets.Styler
	Styles        = style.Styles
	Colors        = style.Colors
	Pair          = style.Pair
	Palette       = style.Palette
	Surface       = style.Surface
	TextRole      = style.TextRole
	CellState     = style.CellState
	GridColors    = style.GridColors
	SyntaxKind    = style.SyntaxKind
	Roles         = widgets.Roles
	StyleChildren = widgets.StyleChildren
	Choice        = widgets.Choice
	TokenPair     = tokens.Pair
	TokenPalette  = tokens.Palette
	TokenDocument = tokens.Document
)

const (
	Canvas          = style.Canvas
	Panel           = style.Panel
	Field           = style.Field
	Footer          = style.Footer
	Editor          = style.Editor
	Body            = style.Body
	Hint            = style.Hint
	Accent          = style.Accent
	Warning         = style.Warning
	SyntaxKeyword   = style.SyntaxKeyword
	SyntaxFunction  = style.SyntaxFunction
	SyntaxType      = style.SyntaxType
	SyntaxString    = style.SyntaxString
	SyntaxNumber    = style.SyntaxNumber
	SyntaxComment   = style.SyntaxComment
	SyntaxParameter = style.SyntaxParameter
	TokenFormat     = tokens.Format
)

// New creates a widget styler for an explicit theme and color profile.
func New(theme, profile string) (Styler, error) { return widgets.New(theme, profile) }

// NewStyles resolves colors and state styles without creating widgets.
func NewStyles(theme, profile string) (Styles, error) { return style.NewStyles(theme, profile) }

// ProfileForColors translates host-reported color capability without terminal I/O.
func ProfileForColors(count int, limited bool) string { return style.ProfileForColors(count, limited) }

// NewChoice creates a drop-down preserving its style inside a Form.
// Apply Styler.Choice or Styler.Form before drawing it.
func NewChoice(label string, options []string, selected int, changed func(string, int)) *Choice {
	return widgets.NewChoice(label, options, selected, changed)
}

// CandidateTokens loads the shared draft JSON candidate, which is distinct from
// the actual LazyOra-derived styles returned by New and NewStyles.
func CandidateTokens() (*TokenDocument, error) { return tokens.Candidate() }

// ParseTokens validates a complete language-neutral token document.
func ParseTokens(data []byte) (*TokenDocument, error) { return tokens.Parse(data) }

// CandidateTokensJSON returns the shared draft candidate data.
func CandidateTokensJSON() string { return tokens.CandidateJSON() }

// Resolve converts language-neutral palette values to terminal styles.
func Resolve(source TokenPalette) (Palette, error) { return style.Resolve(source) }

// BorderColor selects a border color for the actual background and focus state.
func BorderColor(theme, profile string, styles Styles, focused bool, background tcell.Color) tcell.Color {
	return style.BorderColor(theme, profile, styles, focused, background)
}
