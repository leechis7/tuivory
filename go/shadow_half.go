package tuivory

import "github.com/gdamore/tcell/v2"

// halfShadowColor uses the actual backdrop, rather than the popup's surface.
// Dark backdrops retain a little hue; black uses a visible neutral fallback.
func halfShadowColor(p Palette, backdrop tcell.Color) tcell.Color {
	if !backdrop.Valid() {
		backdrop = p["surface"].BG
	}
	r, g, b := backdrop.RGB()
	rgb, indexed := false, false
	for _, pair := range p {
		for _, c := range []tcell.Color{pair.FG, pair.BG} {
			if c.IsRGB() {
				rgb = true
			} else if c.Valid() && c&^tcell.ColorValid >= 16 {
				indexed = true
			}
		}
	}
	if max(r, g, b) <= 16 {
		if rgb {
			return tcell.NewRGBColor(64, 64, 64)
		}
		if indexed {
			return tcell.PaletteColor(238)
		}
		return tcell.PaletteColor(7)
	}
	factor := int32(4)
	if max(r, g, b) <= 96 {
		factor = 2
	}
	if rgb {
		return tcell.NewRGBColor(r*factor/5, g*factor/5, b*factor/5)
	}
	if indexed {
		gray := (r + g + b) * factor / 15
		return tcell.PaletteColor(int(232 + max(int32(0), min(int32(23), (gray-8+5)/10))))
	}
	return tcell.PaletteColor(0)
}

// luminance is a weighted RGB comparison for keeping the corner ink visible.
func shadowBrightness(c tcell.Color) int32 {
	r, g, b := c.RGB()
	return 299*r + 587*g + 114*b
}

func drawHalfShadow(screen tcell.Screen, region CellRect, l PopupLayout, p Palette, options ShadowOptions, ascii bool) {
	cols, rows := screen.Size()
	safe := WideSafeScreen(screen)
	left, right := max(0, region.X), min(cols, popupAdd(region.X, region.Width))
	for y := max(0, region.Y); y < min(rows, popupAdd(region.Y, region.Height)); y++ {
		hasCaps := l.Shadow.Height > l.Card.Height
		cardBottom := popupAdd(l.Card.Y, l.Card.Height)
		if hasCaps && options.HideTopCap && y == l.Shadow.Y && y < cardBottom {
			continue
		}
		bottomCap := hasCaps && y == popupAdd(l.Shadow.Y, l.Shadow.Height)-1
		backgrounds := make([]tcell.Color, max(0, right-left))
		for x := left; x < right; x++ {
			_, _, old, _ := screen.GetContent(x, y)
			if x > 0 {
				_, _, lead, width := screen.GetContent(x-1, y)
				if width > 1 {
					old = lead
				}
			}
			_, bg, _ := old.Decompose()
			if !bg.Valid() {
				bg = p["surface"].BG
			}
			backgrounds[x-left] = bg
		}
		for x := left; x < right; x++ {
			bg := backgrounds[x-left]
			shade := halfShadowColor(p, bg)
			if options.Mode == ShadowSolid {
				shade = tcell.PaletteColor(0)
			} else if !ascii && bottomCap && y > 0 && y-1 > l.Shadow.Y &&
				x >= popupAdd(l.Card.X, l.Card.Width) && shadowBrightness(shade) < shadowBrightness(bg) {
				// A brighter backdrop under the corner must not lighten the tip
				// more than the side shadow it joins.
				_, _, side, _ := screen.GetContent(x, y-1)
				_, above, _ := side.Decompose()
				if above.Valid() && shadowBrightness(above) < shadowBrightness(shade) {
					shade = above
				}
			}
			glyph := ' '
			style := tcell.StyleDefault.Background(shade)
			if ascii {
				glyph, style = '.', tcell.StyleDefault.Foreground(shade).Background(bg)
			} else if l.Shadow.Height > l.Card.Height {
				if y == l.Shadow.Y {
					glyph, style = '▄', tcell.StyleDefault.Foreground(shade).Background(bg)
				} else if y == popupAdd(l.Shadow.Y, l.Shadow.Height)-1 {
					glyph, style = '▀', tcell.StyleDefault.Foreground(shade).Background(bg)
				}
			}
			safe.SetContent(x, y, glyph, nil, style)
		}
	}
}
