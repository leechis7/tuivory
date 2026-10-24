// Package style provides TUIVORY style tokens and tcell adapters.
// Theme values and resolution derive from LazyOra; see docs/lazyora-extraction.md.
package style

import (
	"fmt"
	"github.com/gdamore/tcell/v2"
)

type colorProfile uint8

const (
	profileRGB colorProfile = iota
	profileANSI8
	profileANSI16
	profile256
)

// ProfileForColors resolves the host's reported color count. No terminal I/O occurs.
func ProfileForColors(count int, limited bool) string {
	if limited {
		if count > 0 && count <= 8 {
			return "8"
		}
		return "16"
	}
	switch {
	case count > 0 && count <= 8:
		return "8"
	case count > 0 && count <= 16:
		return "16"
	case count > 0 && count <= 256:
		return "256"
	default:
		return "truecolor"
	}
}

// NewStyles resolves LazyOra-derived defaults independently of any screen or app.
func NewStyles(theme, profile string) (Styles, error) {
	if theme != "dark" && theme != "light" && theme != "blackwhite" {
		return Styles{}, fmt.Errorf("unknown theme: %s", theme)
	}
	var p colorProfile
	switch profile {
	case "8":
		p = profileANSI8
	case "16":
		p = profileANSI16
	case "256":
		p = profile256
	case "truecolor":
		p = profileRGB
	default:
		return Styles{}, fmt.Errorf("unknown profile: %s", profile)
	}
	styles := resolve(theme, p)
	styles.theme, styles.profile = theme, profile
	return styles, nil
}

func indexed(i int) tcell.Color { return tcell.PaletteColor(i) }

type Colors struct {
	Background, Surface, Footer, Field, Text, Muted, Accent, Button    tcell.Color
	Editor, EditorText, FieldText, SelectionText, Placeholder, Warning tcell.Color
}

var palette = Colors{
	Editor: tcell.GetColor("#242d3a"), EditorText: tcell.GetColor("#e5edf5"),
	Background: tcell.GetColor("#2e3440"),
	Surface:    tcell.GetColor("#3b4252"),
	Footer:     tcell.GetColor("#434c5e"),
	Field:      tcell.GetColor("#eceff4"),
	Text:       tcell.GetColor("#eceff4"),
	Muted:      tcell.GetColor("#d8dee9"),
	Accent:     tcell.GetColor("#88c0d0"),
	Button:     tcell.GetColor("#81a1c1"),
	FieldText:  tcell.GetColor("#2e3440"), SelectionText: tcell.GetColor("#2e3440"), Placeholder: tcell.GetColor("#485869"), Warning: tcell.ColorYellow,
}

var lightPalette = Colors{
	Editor: tcell.GetColor("#ffffff"), EditorText: tcell.GetColor("#202a36"),
	Background: tcell.GetColor("#f3f5f7"), Surface: tcell.GetColor("#e4eaf0"), Footer: tcell.GetColor("#ccd7e2"),
	Field: tcell.GetColor("#ffffff"), Text: tcell.GetColor("#202a36"), Muted: tcell.GetColor("#485869"),
	Accent: tcell.GetColor("#276a8e"), Button: tcell.GetColor("#bbd4e5"), FieldText: tcell.GetColor("#202a36"),
	SelectionText: tcell.ColorWhite, Placeholder: tcell.GetColor("#485869"), Warning: tcell.GetColor("#8b4f00"),
}

var blackWhitePalette = Colors{
	Editor: tcell.ColorBlack, EditorText: tcell.ColorWhite,
	Background: tcell.ColorBlack, Surface: tcell.ColorBlack, Footer: tcell.ColorBlack,
	Field: tcell.ColorWhite, Text: tcell.ColorWhite, Muted: tcell.ColorSilver,
	Accent: tcell.ColorWhite, Button: tcell.ColorSilver, FieldText: tcell.ColorBlack,
	SelectionText: tcell.ColorBlack, Placeholder: tcell.ColorGray, Warning: tcell.ColorWhite,
}

var darkANSI = Colors{
	Editor: tcell.ColorBlack, EditorText: tcell.ColorSilver,
	Background: tcell.ColorBlack, Surface: tcell.ColorBlack, Footer: tcell.ColorBlack,
	Field: tcell.ColorSilver, Text: tcell.ColorSilver, Muted: tcell.ColorSilver,
	Accent: tcell.ColorYellow, Button: tcell.ColorSilver, FieldText: tcell.ColorBlack,
	SelectionText: tcell.ColorBlack, Placeholder: tcell.ColorNavy, Warning: tcell.ColorYellow,
}

var lightANSI = Colors{
	Editor: tcell.ColorWhite, EditorText: tcell.ColorBlack,
	Background: tcell.ColorSilver, Surface: tcell.ColorSilver, Footer: tcell.ColorWhite, Field: tcell.ColorWhite,
	Text: tcell.ColorBlack, Muted: tcell.ColorNavy, Accent: tcell.ColorNavy, Button: tcell.ColorSilver,
	FieldText: tcell.ColorBlack, SelectionText: tcell.ColorWhite, Placeholder: tcell.ColorGray, Warning: tcell.ColorMaroon,
}

type Styles struct {
	Colors
	Selection, SelectionFG, Edited, EditedFG, Disabled, Focus tcell.Color
	theme, profile                                            string
}

func resolve(theme string, profile colorProfile) Styles {
	p := profile
	if theme == "blackwhite" {
		c := blackWhitePalette
		c.Text, c.EditorText, c.Muted, c.Accent, c.Warning = tcell.ColorSilver, tcell.ColorSilver, tcell.ColorSilver, tcell.ColorSilver, tcell.ColorSilver
		c.Field, c.Button, c.Placeholder = tcell.ColorSilver, tcell.ColorSilver, tcell.ColorBlack
		return Styles{Colors: c, Selection: tcell.ColorSilver, SelectionFG: tcell.ColorBlack, Edited: tcell.ColorSilver, EditedFG: tcell.ColorBlack, Disabled: tcell.ColorSilver, Focus: tcell.ColorSilver}
	}
	light := theme == "light"
	c := palette
	if light {
		c = lightPalette
	}
	t := Styles{Colors: c, Selection: tcell.GetColor("#005f87"), SelectionFG: tcell.ColorWhite,
		Edited: tcell.GetColor("#d7af87"), EditedFG: tcell.GetColor("#202a36"), Disabled: c.Muted, Focus: c.Accent}
	if light {
		t.Focus = tcell.GetColor("#005fcc")
		t.Accent = t.Focus
		t.Warning = tcell.GetColor("#7a4300")
	}
	t.SelectionText = t.SelectionFG
	if p == profileANSI8 || p == profileANSI16 {
		c = darkANSI
		c.Text, c.EditorText, c.Muted, c.Placeholder = indexed(7), indexed(7), indexed(7), indexed(0)
		if p == profileANSI8 {
			c.Accent, c.Warning = indexed(3), indexed(3)
		} else {
			c.Accent = indexed(14)
		}
		if light {
			c = lightANSI
			c.Background, c.Surface, c.Editor, c.Field, c.Footer = indexed(7), indexed(7), indexed(7), indexed(7), indexed(7)
			c.Text, c.Muted, c.EditorText, c.Placeholder = indexed(0), indexed(0), indexed(0), indexed(0)
			if p == profileANSI16 {
				c.Background, c.Editor, c.Field, c.Footer = indexed(15), indexed(15), indexed(15), indexed(15)
			}
		}
		t = Styles{Colors: c, Selection: indexed(4), SelectionFG: indexed(7), Edited: indexed(3), EditedFG: indexed(0), Disabled: c.Muted, Focus: indexed(7)}
		if light {
			t.Focus = indexed(4)
		}
		if p == profileANSI16 {
			t.SelectionFG = indexed(15)
		}
		t.SelectionText = t.SelectionFG
		return t
	}
	if p == profile256 {
		c.Background, c.Surface, c.Footer, c.Editor, c.Text, c.EditorText, c.Muted = indexed(236), indexed(237), indexed(237), indexed(236), indexed(252), indexed(252), indexed(250)
		c.Field, c.FieldText, c.Button, c.Placeholder, c.Accent, c.Warning = indexed(254), indexed(235), indexed(153), indexed(239), indexed(117), indexed(222)
		if light {
			c.Background, c.Surface, c.Footer, c.Editor = indexed(255), indexed(254), indexed(254), indexed(231)
			c.Text, c.EditorText, c.Muted, c.Field, c.Accent, c.Warning = indexed(235), indexed(235), indexed(239), indexed(231), indexed(25), indexed(94)
		}
		t = Styles{Colors: c, Selection: indexed(24), SelectionFG: indexed(255), Edited: indexed(180), EditedFG: indexed(0), Disabled: c.Muted, Focus: c.Accent}
		if light {
			t.SelectionFG = indexed(231)
		}
		t.SelectionText = t.SelectionFG
	}
	return t
}
