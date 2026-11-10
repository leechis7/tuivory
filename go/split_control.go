package tuivory

import "math"

// SplitSide identifies the panel affected by a collapse action.
type SplitSide uint8

const (
	SplitNeither SplitSide = iota
	SplitFirst
	SplitSecond
)

// SplitControl adds optional collapse and pointer capture to a SplitSpec.
// Keep a separate control and SplitState for each independently sized axis.
type SplitControl struct {
	collapsed      SplitSide
	ratio          float64
	pressed, moved bool
	start, total   int
}

func (c *SplitControl) Collapsed() SplitSide { return c.collapsed }
func (c *SplitControl) Captured() bool       { return c.pressed }
func (c *SplitControl) Dragging() bool       { return c.pressed && c.moved }
func (c *SplitControl) CancelPointer()       { c.pressed, c.moved = false, false }

// VisibleFocus returns the visible panel to which the host should route focus.
func (c *SplitControl) VisibleFocus(activeSecond bool) bool {
	switch c.collapsed {
	case SplitFirst:
		return true
	case SplitSecond:
		return false
	default:
		return activeSecond
	}
}

func (c *SplitControl) Layout(spec SplitSpec, state *SplitState, total int) SplitLayout {
	if c.collapsed != SplitNeither && total > 0 {
		if c.collapsed == SplitFirst {
			return SplitLayout{Divider: 1, Second: total - 1}
		}
		return SplitLayout{First: total - 1, Divider: 1}
	}
	layout := spec.Layout(state, total)
	if c.ratio > 0 && !layout.Compact {
		copy := SplitState{Preferred: max(1, int(math.Floor(c.ratio*float64(total-1)+0.5)))}
		return spec.Layout(&copy, total)
	}
	return layout
}

// Toggle is the same action for a keyboard binding, menu or divider click.
func (c *SplitControl) Toggle(spec SplitSpec, state *SplitState, total int, side SplitSide) bool {
	c.CancelPointer()
	if c.collapsed != SplitNeither {
		c.collapsed = SplitNeither
		return true
	}
	if side != SplitFirst && side != SplitSecond {
		return false
	}
	layout := c.Layout(spec, state, total)
	if c.ratio == 0 && !layout.Compact {
		c.ratio = float64(layout.First) / float64(total-1)
	}
	c.collapsed = side
	return true
}

func (c *SplitControl) Resize(spec SplitSpec, state *SplitState, total, position int) bool {
	old := c.Layout(spec, state, total)
	if c.collapsed != SplitNeither || old.Compact {
		return false
	}
	spec.Resize(state, total, position)
	c.ratio = 0
	return state.Preferred != old.First
}

// Pointer handles down, move, up or cancel on the split axis. inside means the
// pointer is inside the split rectangle, including its perpendicular axis.
func (c *SplitControl) Pointer(spec SplitSpec, state *SplitState, total, position int, inside bool, action string, side SplitSide) bool {
	if action == "cancel" {
		had := c.Captured()
		c.CancelPointer()
		return had
	}
	if action == "down" {
		c.CancelPointer()
		l := c.Layout(spec, state, total)
		if !inside || l.Divider != 1 || position != l.First {
			return false
		}
		c.pressed, c.start, c.total = true, position, total
		return true
	}
	if !c.pressed || (action != "move" && action != "up") {
		return false
	}
	if total != c.total {
		c.CancelPointer()
		return true
	}
	c.moved = c.moved || action == "move" || position != c.start || !inside
	if c.moved {
		c.Resize(spec, state, total, position)
	}
	if action == "up" {
		click := !c.moved
		c.CancelPointer()
		if click {
			c.Toggle(spec, state, total, side)
		}
	}
	return true
}

// SplitGlyph returns the divider or the action arrow at its grip.
func SplitGlyph(rows, ascii, grip bool, side, collapsed SplitSide) rune {
	if collapsed != SplitNeither {
		side = collapsed
	}
	if grip && (side == SplitFirst || side == SplitSecond) {
		towardFirst := (side == SplitFirst) != (collapsed != SplitNeither)
		if rows {
			if ascii {
				if towardFirst {
					return '^'
				}
				return 'v'
			}
			if towardFirst {
				return '↑'
			}
			return '↓'
		}
		if ascii {
			if towardFirst {
				return '<'
			}
			return '>'
		}
		if towardFirst {
			return '‹'
		}
		return '›'
	}
	if rows {
		if ascii {
			return '-'
		}
		return '─'
	}
	if ascii {
		return '|'
	}
	return '│'
}
