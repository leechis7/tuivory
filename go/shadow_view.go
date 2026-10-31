package tuivory

import (
	"fmt"
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

// ShadowView wraps any host-owned primitive. Its rectangle includes reserved
// shadow space; Child receives only the card. Shadows never receive input.
type ShadowView struct {
	*tview.Box
	Child   tview.Primitive
	palette Palette
	options ShadowOptions
	ASCII   bool
}

func NewShadowView(child tview.Primitive, palette Palette, options ShadowOptions) (*ShadowView, error) {
	if child == nil {
		return nil, fmt.Errorf("shadow: child required")
	}
	v := &ShadowView{Box: tview.NewBox(), Child: child}
	if err := v.SetPalette(palette); err != nil {
		return nil, err
	}
	if err := v.SetShadow(options); err != nil {
		return nil, err
	}
	return v, nil
}
func (v *ShadowView) SetPalette(palette Palette) error {
	p, err := componentPalette(palette, "surface", "hint")
	if err == nil {
		v.palette = p
	}
	return err
}
func (v *ShadowView) SetShadow(options ShadowOptions) error {
	if err := options.Validate(); err != nil {
		return err
	}
	v.options = options
	return nil
}

// Layout exposes geometry without moving focus or changing child data.
func (v *ShadowView) Layout() PopupLayout {
	x, y, w, h := v.GetRect()
	return v.options.Layout(CellRect{X: x, Y: y, Width: w, Height: h})
}
func (v *ShadowView) StyleChildren() []tview.Primitive     { return []tview.Primitive{v.Child} }
func (v *ShadowView) HasFocus() bool                       { return v.Child.HasFocus() }
func (v *ShadowView) Focus(delegate func(tview.Primitive)) { delegate(v.Child) }
func (v *ShadowView) Blur()                                { v.Child.Blur() }
func (v *ShadowView) AtTabBoundary(previous bool) bool     { return tabBoundary(v.Child, previous) }

// InRect deliberately excludes the visual shadow, including for host hit tests.
func (v *ShadowView) InRect(x, y int) bool {
	r := v.Layout().Card
	return r.Width > 0 && r.Height > 0 && x >= r.X && y >= r.Y && x < popupAdd(r.X, r.Width) && y < popupAdd(r.Y, r.Height)
}
func (v *ShadowView) Draw(screen tcell.Screen) {
	l := v.Layout()
	for _, region := range l.ShadowRegions() {
		drawPopupShadow(screen, region, v.palette, v.options.Mode, v.ASCII)
	}
	v.Child.SetRect(l.Card.X, l.Card.Y, l.Card.Width, l.Card.Height)
	if l.Card.Width > 0 && l.Card.Height > 0 {
		v.Child.Draw(WideSafeScreen(screen))
	}
}
func (v *ShadowView) InputHandler() func(*tcell.EventKey, func(tview.Primitive)) {
	return v.WrapInputHandler(func(e *tcell.EventKey, f func(tview.Primitive)) {
		if h := v.Child.InputHandler(); h != nil {
			h(e, f)
		}
	})
}
func (v *ShadowView) PasteHandler() func(string, func(tview.Primitive)) {
	return v.WrapPasteHandler(func(s string, f func(tview.Primitive)) {
		if h := v.Child.PasteHandler(); h != nil {
			h(s, f)
		}
	})
}
func (v *ShadowView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return v.WrapMouseHandler(func(a tview.MouseAction, e *tcell.EventMouse, f func(tview.Primitive)) (bool, tview.Primitive) {
		x, y := e.Position()
		if !v.InRect(x, y) {
			return false, nil
		}
		if h := v.Child.MouseHandler(); h != nil {
			return h(a, e, f)
		}
		return false, nil
	})
}

// Solid uses the existing classic black shadow style. Auto darkens the real
// surface with supported colors, using a stipple when black cannot be darkened.
func shadowBrush(p Palette, mode ShadowMode) (tcell.Style, bool, bool) {
	classic := (Styles{}).PopupShadowStyle().Foreground(p["hint"].FG)
	if mode == ShadowDim {
		return classic, false, true
	}
	if mode == ShadowSolid {
		return classic, false, false
	}
	base := p["surface"].BG
	r, g, b := base.RGB()
	if r < 0 || g < 0 || b < 0 {
		return classic, false, true
	}
	if max(r, g, b) <= 16 {
		return tcell.StyleDefault.Foreground(p["hint"].FG).Background(base), true, false
	}
	rgb, colors256 := false, false
	for _, pair := range p {
		for _, c := range []tcell.Color{pair.FG, pair.BG} {
			if !c.Valid() {
				continue
			}
			if c.IsRGB() {
				rgb = true
			} else if c&^tcell.ColorValid >= 16 {
				colors256 = true
			}
		}
	}
	if rgb {
		return tcell.StyleDefault.Background(tcell.NewRGBColor(r*4/5, g*4/5, b*4/5)), false, false
	}
	if colors256 {
		gray := (r + g + b) * 4 / 15
		index := 232 + max(int32(0), min(int32(23), (gray-8+5)/10))
		return tcell.StyleDefault.Background(tcell.PaletteColor(int(index))), false, false
	}
	return classic, false, false
}
func drawPopupShadow(screen tcell.Screen, r CellRect, p Palette, mode ShadowMode, ascii bool) {
	if r.Width <= 0 || r.Height <= 0 || mode == ShadowOff || mode == "" {
		return
	}
	style, pattern, dim := shadowBrush(p, mode)
	if dim {
		DimRegion(screen, r)
		return
	}
	cols, rows := screen.Size()
	right, bottom := min(cols, popupAdd(r.X, r.Width)), min(rows, popupAdd(r.Y, r.Height))
	left, top := max(0, r.X), max(0, r.Y)
	glyph := ' '
	if pattern {
		glyph = '░'
		if ascii {
			glyph = '.'
		}
	}
	safe := WideSafeScreen(screen)
	for y := top; y < bottom; y++ {
		for x := left; x < right; x++ {
			safe.SetContent(x, y, glyph, nil, style)
		}
	}
}
