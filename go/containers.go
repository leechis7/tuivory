package tuivory

import "fmt"

// Track constraints are terminal cells; Max=0 means unbounded. Fixed>0
// overrides weight. On tiny screens minimums shrink in declaration order.
type Track struct{ Min, Max, Fixed, Weight int }
type LayoutItem struct {
	ID                      string
	Track                   Track
	Row, Column             int
	RowSpan                 int `json:"row_span"`
	ColumnSpan              int `json:"column_span"`
	Hidden, Modal, Centered bool
	Disabled                bool
	Drawer                  string // "left" or "right" for an edge-attached layer.
	// Layer size: zero expands to available space. Nonzero X/Y are inset offsets.
	Area CellRect
}
type ContainerOptions struct {
	Kind          string // row, column, grid, layers
	Gap, Padding  int
	Rows, Columns []Track
	VirtualWidth  int `json:"virtual_width"`
	VirtualHeight int `json:"virtual_height"`
}

func trackValid(t Track) bool {
	return t.Min >= 0 && t.Max >= 0 && t.Fixed >= 0 && t.Weight >= 0 && max(t.Min, t.Max, t.Fixed, t.Weight) <= 1000000 && (t.Max == 0 || t.Max >= t.Min) && (t.Max == 0 || t.Fixed <= t.Max)
}
func allocateTracks(tracks []Track, total, gap int) ([]int, int, error) {
	if len(tracks) > 1024 {
		return nil, 0, fmt.Errorf("too many tracks")
	}
	tracks = append([]Track(nil), tracks...)
	for i, t := range tracks {
		if t == (Track{}) {
			tracks[i].Weight = 1
		}
	}
	sizes := make([]int, len(tracks))
	for _, t := range tracks {
		if !trackValid(t) {
			return nil, 0, fmt.Errorf("invalid track constraints")
		}
	}
	if len(tracks) == 0 {
		return sizes, 0, nil
	}
	gap = min(gap, max(0, total/(len(tracks)-1+1)))
	available := max(0, total-gap*(len(tracks)-1))
	minimum := 0
	for _, t := range tracks {
		minimum += max(t.Min, t.Fixed)
	}
	if minimum > available {
		gap = 0
		available = max(0, total)
	}
	for i, t := range tracks {
		sizes[i] = min(available, max(t.Min, t.Fixed))
		available -= sizes[i]
	}
	for available > 0 {
		weight := 0
		for i, t := range tracks {
			if t.Fixed == 0 && t.Weight > 0 && (t.Max == 0 || sizes[i] < t.Max) {
				weight += t.Weight
			}
		}
		if weight == 0 {
			break
		}
		budget := available
		changed := false
		for i, t := range tracks {
			if t.Fixed > 0 || t.Weight == 0 || t.Max > 0 && sizes[i] >= t.Max {
				continue
			}
			add := min(available, max(1, int(int64(budget)*int64(t.Weight)/int64(weight))))
			if t.Max > 0 {
				add = min(add, t.Max-sizes[i])
			}
			sizes[i] += add
			available -= add
			changed = changed || add > 0
		}
		if !changed {
			break
		}
	}
	return sizes, gap, nil
}
func ComputeContainer(bounds CellRect, items []LayoutItem, options ContainerOptions) ([]NamedRect, error) {
	if len(items) > 1024 || bounds.X < -1000000 || bounds.Y < -1000000 || bounds.X > 1000000 || bounds.Y > 1000000 {
		return nil, fmt.Errorf("invalid container bounds/item count")
	}
	if options.Gap < 0 || options.Padding < 0 || options.Gap > 1024 || options.Padding > 1024 || bounds.Width < 0 || bounds.Height < 0 || max(bounds.Width, bounds.Height, options.VirtualWidth, options.VirtualHeight) > 1000000 || options.VirtualWidth < 0 || options.VirtualHeight < 0 {
		return nil, fmt.Errorf("invalid container extent")
	}
	if options.Kind != "row" && options.Kind != "column" && options.Kind != "grid" && options.Kind != "layers" {
		return nil, fmt.Errorf("unknown container kind")
	}
	seen := map[string]bool{}
	visible := []LayoutItem{}
	for _, item := range items {
		if item.Drawer != "" && (options.Kind != "layers" || item.Centered || (item.Drawer != "left" && item.Drawer != "right")) {
			return nil, fmt.Errorf("invalid drawer layer")
		}
		if item.ID == "" || seen[item.ID] || !trackValid(item.Track) || min(item.Row, item.Column, item.RowSpan, item.ColumnSpan, item.Area.X, item.Area.Y, item.Area.Width, item.Area.Height) < 0 || max(item.Area.X, item.Area.Y, item.Area.Width, item.Area.Height) > 1000000 {
			return nil, fmt.Errorf("invalid container item")
		}
		seen[item.ID] = true
		if !item.Hidden {
			visible = append(visible, item)
		}
	}
	inner := bounds.Inset(options.Padding)
	out := []NamedRect{}
	switch options.Kind {
	case "row", "column":
		tracks := make([]Track, len(visible))
		for i, item := range visible {
			tracks[i] = item.Track
		}
		total := inner.Width
		if options.Kind == "column" {
			total = inner.Height
		}
		sizes, gap, e := allocateTracks(tracks, total, options.Gap)
		if e != nil {
			return nil, e
		}
		at := 0
		for i, item := range visible {
			r := inner
			if options.Kind == "row" {
				r.X += at
				r.Width = sizes[i]
			} else {
				r.Y += at
				r.Height = sizes[i]
			}
			out = append(out, NamedRect{ID: item.ID, Rect: r})
			at += sizes[i] + gap
		}
	case "grid":
		widths, gx, e := allocateTracks(options.Columns, inner.Width, options.Gap)
		if e != nil {
			return nil, e
		}
		heights, gy, e := allocateTracks(options.Rows, inner.Height, options.Gap)
		if e != nil {
			return nil, e
		}
		for _, item := range visible {
			rs, cs := max(1, item.RowSpan), max(1, item.ColumnSpan)
			if item.Row >= len(heights) || item.Column >= len(widths) || rs > len(heights)-item.Row || cs > len(widths)-item.Column {
				return nil, fmt.Errorf("grid span outside tracks")
			}
			r := CellRect{X: inner.X, Y: inner.Y}
			for _, w := range widths[:item.Column] {
				r.X += w + gx
			}
			for _, h := range heights[:item.Row] {
				r.Y += h + gy
			}
			for _, w := range widths[item.Column : item.Column+cs] {
				r.Width += w
			}
			for _, h := range heights[item.Row : item.Row+rs] {
				r.Height += h
			}
			r.Width += gx * (cs - 1)
			r.Height += gy * (rs - 1)
			out = append(out, NamedRect{ID: item.ID, Rect: r})
		}
	case "layers":
		for _, item := range visible {
			r := inner
			r.X += max(0, item.Area.X)
			r.Y += max(0, item.Area.Y)
			r.Width = max(0, r.Width-max(0, item.Area.X))
			r.Height = max(0, r.Height-max(0, item.Area.Y))
			if item.Area.Width > 0 {
				r.Width = min(r.Width, item.Area.Width)
			}
			if item.Area.Height > 0 {
				r.Height = min(r.Height, item.Area.Height)
			}
			if item.Centered {
				r.X = inner.X + (inner.Width-r.Width)/2
				r.Y = inner.Y + (inner.Height-r.Height)/2
			}
			if item.Drawer != "" {
				preferred := item.Area.Width
				if preferred == 0 {
					preferred = inner.Width
				}
				placement := DrawerLayout(inner, preferred, 0)
				r.Width = placement.Rect.Width
				r.X = inner.X
				if item.Drawer == "right" {
					r.X = inner.X + inner.Width - r.Width
				}
			}
			out = append(out, NamedRect{ID: item.ID, Rect: r})
		}
	}
	return out, nil
}

// ContainerState is a backend-neutral focus/hit/drag router. Modal layers block
// lower layers even when the pointer is outside the card. IDs survive reflow.
type ContainerState struct {
	Focused, Captured string
	modal             string
	restore           map[string]string
}

func (s *ContainerState) Eligible(items []LayoutItem) []string {
	start := 0
	for i, item := range items {
		if !item.Hidden && item.Modal {
			start = i
		}
	}
	out := []string{}
	for _, item := range items[start:] {
		if !item.Hidden {
			if !item.Disabled {
				out = append(out, item.ID)
			}
		}
	}
	return out
}
func (s *ContainerState) Reconcile(items []LayoutItem) {
	ids := s.Eligible(items)
	modal := ""
	for _, item := range items {
		if item.Modal && !item.Hidden {
			modal = item.ID
		}
	}
	if modal != s.modal {
		if s.restore == nil {
			s.restore = map[string]string{}
		}
		oldVisible := false
		for _, item := range items {
			oldVisible = oldVisible || item.ID == s.modal && !item.Hidden && item.Modal
		}
		if s.modal != "" && !oldVisible {
			previous := s.restore[s.modal]
			delete(s.restore, s.modal)
			for steps := 0; steps <= len(items); steps++ {
				found := false
				for _, id := range ids {
					if id == previous {
						s.Focused = id
						found = true
					}
				}
				if found {
					break
				}
				next, ok := s.restore[previous]
				if !ok {
					break
				}
				delete(s.restore, previous)
				previous = next
			}
		}
		if _, exists := s.restore[modal]; modal != "" && !exists {
			s.restore[modal] = s.Focused
		}
		s.modal = modal
	}
	found, captured := false, false
	for _, id := range ids {
		found = found || id == s.Focused
		captured = captured || id == s.Captured
	}
	if !found {
		s.Focused = ""
		if len(ids) > 0 {
			s.Focused = ids[0]
		}
	}
	if !captured {
		s.Captured = ""
	}
}
func (s *ContainerState) Move(items []LayoutItem, previous bool) string {
	s.Reconcile(items)
	ids := s.Eligible(items)
	for i, id := range ids {
		if id == s.Focused {
			delta := 1
			if previous {
				delta = len(ids) - 1
			}
			s.Focused = ids[(i+delta)%len(ids)]
			break
		}
	}
	return s.Focused
}
func (s *ContainerState) Hit(items []LayoutItem, rects []NamedRect, x, y int) string {
	ids := s.Eligible(items)
	for i := len(rects) - 1; i >= 0; i-- {
		r := rects[i]
		eligible := false
		for _, id := range ids {
			eligible = eligible || id == r.ID
		}
		if eligible && x >= r.Rect.X && y >= r.Rect.Y && x < r.Rect.X+r.Rect.Width && y < r.Rect.Y+r.Rect.Height {
			return r.ID
		}
	}
	return ""
}
