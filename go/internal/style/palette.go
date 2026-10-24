// Package style adapts TUIVORY tokens to tcell styles; it owns no screen or app state.
package style

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go/internal/tokens"
)

type Pair struct {
	FG, BG tcell.Color
	Bold   bool
}

func (p Pair) Style() tcell.Style {
	return tcell.StyleDefault.Foreground(p.FG).Background(p.BG).Bold(p.Bold)
}

type Palette map[string]Pair

func color(value string) (tcell.Color, error) {
	if strings.HasPrefix(value, "#") && len(value) == 7 {
		n, err := strconv.ParseUint(value[1:], 16, 24)
		if err == nil {
			return tcell.NewHexColor(int32(n)), nil
		}
	}
	n, err := strconv.Atoi(value)
	if err != nil || n < 0 || n > 255 {
		return 0, fmt.Errorf("invalid color: %q", value)
	}
	return tcell.PaletteColor(n), nil
}

// Resolve preserves ANSI indices instead of substituting reference RGB values.
func Resolve(source tokens.Palette) (Palette, error) {
	palette := Palette{}
	for role, pair := range source {
		fg, err := color(pair.Foreground)
		if err != nil {
			return nil, err
		}
		bg, err := color(pair.Background)
		if err != nil {
			return nil, err
		}
		if pair.FontWeight != "none" && pair.FontWeight != "bold" {
			return nil, fmt.Errorf("invalid font weight: %q", pair.FontWeight)
		}
		palette[role] = Pair{FG: fg, BG: bg, Bold: pair.FontWeight == "bold"}
	}
	return palette, nil
}
