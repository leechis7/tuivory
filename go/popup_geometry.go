package tuivory

import "fmt"

// ShadowMode selects an optional popup shadow. The zero value is off.
type ShadowMode string

const (
	ShadowOff   ShadowMode = "off"
	ShadowAuto  ShadowMode = "auto"
	ShadowSolid ShadowMode = "solid"
	ShadowDim   ShadowMode = "dim"
)

// ShadowOptions uses terminal cells. Auto/solid/dim with both offsets zero uses
// the default right-two/down-one offset; use Off to remove the shadow entirely.
type ShadowOptions struct {
	Mode    ShadowMode `json:"mode"`
	OffsetX int        `json:"offsetX"`
	OffsetY int        `json:"offsetY"`
}

func (o ShadowOptions) Validate() error {
	if o.OffsetX < 0 || o.OffsetY < 0 {
		return fmt.Errorf("shadow: offsets must be nonnegative")
	}
	switch o.Mode {
	case "", ShadowOff, ShadowAuto, ShadowSolid, ShadowDim:
		return nil
	}
	return fmt.Errorf("shadow: unknown mode %q", o.Mode)
}
func (o ShadowOptions) offsets() (int, int) {
	if o.Mode == "" || o.Mode == ShadowOff {
		return 0, 0
	}
	x, y := max(0, o.OffsetX), max(0, o.OffsetY)
	if x == 0 && y == 0 {
		return 2, 1
	}
	return x, y
}

// PopupLayout describes the full allocation, interactive card, and shifted shadow.
// Card and Shadow fit Bounds. Only a wide glyph crossing an edge may be repaired
// in an adjacent cell, preserving the outside style.
type PopupLayout struct{ Bounds, Card, Shadow CellRect }

// Layout reserves shadow space inside an assigned footprint, retaining at least
// one card cell per nonempty dimension. It performs no drawing or input routing.
func (o ShadowOptions) Layout(bounds CellRect) PopupLayout {
	bounds.Width = max(0, bounds.Width)
	bounds.Height = max(0, bounds.Height)
	l := PopupLayout{Bounds: bounds, Card: bounds}
	if bounds.Width == 0 || bounds.Height == 0 {
		return l
	}
	dx, dy := o.offsets()
	dx = min(dx, bounds.Width-1)
	dy = min(dy, bounds.Height-1)
	l.Card.Width -= dx
	l.Card.Height -= dy
	if dx != 0 || dy != 0 {
		l.Shadow = CellRect{X: popupAdd(bounds.X, dx), Y: popupAdd(bounds.Y, dy), Width: l.Card.Width, Height: l.Card.Height}
	}
	return l
}
func popupAdd(a, b int) int {
	b = max(0, b)
	limit := int(^uint(0) >> 1)
	if a > limit-b {
		return limit
	}
	return a + b
}
func popupSub(a, b int) int {
	b = max(0, b)
	limit := -int(^uint(0)>>1) - 1
	if a < limit+b {
		return limit
	}
	return a - b
}

// PopupPlacement positions the whole card+shadow footprint near a host anchor.
// width/height request the card size; clipping may shrink it on narrow screens.
// Existing MenuPlacement remains the no-shadow card-only helper.
func PopupPlacement(anchor, viewport CellRect, width, height int, shadow ShadowOptions) PopupLayout {
	vw, vh := max(0, viewport.Width), max(0, viewport.Height)
	dx, dy := shadow.offsets()
	w, h := 0, 0
	if width > 0 && height > 0 {
		w = min(vw, popupAdd(width, dx))
		h = min(vh, popupAdd(height, dy))
	}
	maxX, maxY := popupAdd(viewport.X, vw-w), popupAdd(viewport.Y, vh-h)
	x := max(viewport.X, min(maxX, anchor.X))
	y := popupAdd(anchor.Y, max(0, anchor.Height))
	if y > maxY {
		y = popupSub(anchor.Y, h)
	}
	y = max(viewport.Y, min(maxY, y))
	return shadow.Layout(CellRect{X: x, Y: y, Width: w, Height: h})
}

// ShadowRegions returns disjoint right and bottom strips, excluding the card.
// Paint these instead of the full shifted rectangle so layered attributes do
// not leak into the child widget, especially with Dim-mode shadows.
func (l PopupLayout) ShadowRegions() [2]CellRect {
	s, c := l.Shadow, l.Card
	sr, sb := popupAdd(s.X, s.Width), popupAdd(s.Y, s.Height)
	cr, cb := popupAdd(c.X, c.Width), popupAdd(c.Y, c.Height)
	x, y := max(s.X, cr), max(s.Y, cb)
	return [2]CellRect{{X: x, Y: s.Y, Width: max(0, sr-x), Height: max(0, min(sb, cb)-s.Y)}, {X: s.X, Y: y, Width: max(0, s.Width), Height: max(0, sb-y)}}
}
