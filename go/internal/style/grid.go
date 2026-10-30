package style

import "github.com/gdamore/tcell/v2"

// CellState describes display state without any database value or app object.
type CellState struct {
	Row                               int
	CurrentRow, Null, Edited, InRange bool
}

func (s Styles) GridHeaderStyle(active bool) tcell.Style {
	if active {
		return s.SelectionStyle().Underline(true)
	}
	return tcell.StyleDefault.Foreground(s.Text).Background(s.GridColors().Header).Underline(true)
}

func (s Styles) GridActiveStyle(focused, edited bool) tcell.Style {
	if edited {
		return s.EditedStyle().Underline(focused)
	}
	return s.GridHeaderStyle(focused)
}

// GridCellStyle retains LazyOra's composition: stripe, current row, null,
// edited, then range selection. State markers remain the host's responsibility.
func (s Styles) GridCellStyle(state CellState) tcell.Style {
	p := s.GridColors()
	fg, bg := s.Text, p.Background
	if state.Row%2 == 0 {
		bg = p.Stripe
	}
	if state.Row > 0 && state.CurrentRow {
		bg = p.Current
	}
	result := tcell.StyleDefault
	if state.Row > 0 && state.Null {
		fg = p.Muted
		result = result.Italic(true)
	}
	result = result.Foreground(fg).Background(bg)
	if state.Edited {
		result = s.EditedStyle()
	}
	if state.InRange {
		result = s.TextStyle(Field, Body).Underline(true)
	}
	return result
}

func (s Styles) GridDividerColor() tcell.Color {
	if s.ansiColors() && s.theme != "blackwhite" {
		return tcell.ColorTeal
	}
	return s.GridColors().Divider
}

func (s Styles) GridGutterStyle() tcell.Style {
	p := s.GridColors()
	if s.ansiColors() && s.theme != "blackwhite" {
		if s.theme == "light" {
			return tcell.StyleDefault.Foreground(s.Muted).Background(s.Background)
		}
		return tcell.StyleDefault.Foreground(tcell.ColorSilver).Background(tcell.ColorBlack)
	}
	return tcell.StyleDefault.Foreground(p.Muted).Background(p.Background)
}

func (s Styles) GridStatusStyle() tcell.Style {
	if s.ansiColors() && s.theme != "blackwhite" {
		if s.theme == "light" {
			return tcell.StyleDefault.Foreground(tcell.ColorBlack).Background(tcell.ColorSilver)
		}
		return s.SelectionStyle()
	}
	return tcell.StyleDefault.Foreground(s.Muted).Background(s.Surface)
}

type GridColors struct{ Background, Stripe, Header, Current, RangeBG, Divider, Muted tcell.Color }

var gridPalette = GridColors{
	tcell.GetColor("#232b38"), tcell.GetColor("#293342"), tcell.GetColor("#3b4e67"),
	tcell.GetColor("#35485f"), tcell.GetColor("#496b82"), tcell.GetColor("#52647a"), tcell.GetColor("#95a5b9"),
}

var lightGridPalette = GridColors{
	tcell.GetColor("#ffffff"), tcell.GetColor("#f0f4f8"), tcell.GetColor("#d4e0eb"),
	tcell.GetColor("#dce9f4"), tcell.GetColor("#bdd9ea"), tcell.GetColor("#91a6b8"), tcell.GetColor("#526579"),
}

func (s Styles) GridColors() GridColors {
	p := s
	if s.theme == "blackwhite" || s.ansiColors() {
		return GridColors{p.Background, p.Background, p.Surface, p.Background, s.Selection, p.Muted, p.Text}
	}
	if s.profile == "256" {
		stripe := indexed(237)
		if s.theme == "light" {
			stripe = indexed(254)
		}
		return GridColors{p.Background, stripe, p.Surface, p.Surface, s.Selection, p.Muted, p.Muted}
	}
	if s.theme == "light" {
		c := lightGridPalette
		c.Muted = p.Muted
		return c
	}
	c := gridPalette
	c.Muted = p.Muted
	return c
}
