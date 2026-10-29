package tuivory

import (
	"fmt"
	"sort"
	"strings"
)

type Density string

const (
	DensityAuto        Density = "auto"
	DensityCompact     Density = "compact"
	DensityComfortable Density = "comfortable"
)

type SpacingTokens struct{ Gap, Padding, ControlGap, CompactBelow int }

func ResolveSpacing(density Density, columns int) (SpacingTokens, error) {
	if columns < 0 {
		return SpacingTokens{}, fmt.Errorf("negative terminal width")
	}
	if density == DensityAuto {
		if columns < 80 {
			density = DensityCompact
		} else {
			density = DensityComfortable
		}
	}
	switch density {
	case DensityCompact:
		return SpacingTokens{Gap: 0, Padding: 0, ControlGap: 1, CompactBelow: 80}, nil
	case DensityComfortable:
		return SpacingTokens{Gap: 2, Padding: 1, ControlGap: 2, CompactBelow: 80}, nil
	}
	return SpacingTokens{}, fmt.Errorf("invalid density")
}

type CellRect struct{ X, Y, Width, Height int }

func (r CellRect) Inset(padding int) CellRect {
	padding = max(0, padding)
	width, height := max(0, r.Width), max(0, r.Height)
	left, top := min(padding, width), min(padding, height)
	return CellRect{X: r.X + left, Y: r.Y + top, Width: width - left - min(padding, width-left), Height: height - top - min(padding, height-top)}
}

type StackItem struct {
	ID                     string
	Min, Preferred, Weight int
}
type StackSlot struct {
	ID          string
	Start, Size int
}
type StackResult struct {
	Slots  []StackSlot
	Hidden []string
	Gap    int
}

func StackLayout(items []StackItem, total, gap int) (StackResult, error) {
	r := StackResult{}
	if total < 0 || total > 1000000000 || gap < 0 || gap > 1024 {
		return r, fmt.Errorf("invalid stack extent/gap")
	}
	seen := map[string]bool{}
	minimum := 0
	for _, s := range items {
		if s.ID == "" || seen[s.ID] || s.Min < 1 || s.Preferred < 0 || s.Weight < 0 || s.Min > 1000000 || s.Preferred > 1000000 || s.Weight > 1000000 {
			return r, fmt.Errorf("invalid stack item")
		}
		seen[s.ID] = true
		minimum += s.Min
	}
	if len(items) == 0 {
		return r, nil
	}
	available := total - gap*(len(items)-1)
	if available < minimum {
		gap = 0
		available = total
	}
	r.Gap = gap
	sizes := make([]int, len(items))
	active := make([]bool, len(items))
	for i, s := range items {
		if s.Min > available && i > 0 {
			continue
		}
		sizes[i] = min(s.Min, available)
		available -= sizes[i]
		active[i] = true
	}
	for i, s := range items {
		if !active[i] {
			continue
		}
		add := min(max(0, s.Preferred-sizes[i]), available)
		sizes[i] += add
		available -= add
	}
	weights := 0
	for i, s := range items {
		if active[i] {
			weights += s.Weight
		}
	}
	if weights > 0 {
		extra := available
		for i, s := range items {
			if !active[i] {
				continue
			}
			add := extra * s.Weight / weights
			sizes[i] += add
			available -= add
		}
		for i, s := range items {
			if available == 0 {
				break
			}
			if active[i] && s.Weight > 0 {
				sizes[i]++
				available--
			}
		}
	}
	start := 0
	visible := 0
	for i, s := range items {
		if sizes[i] == 0 {
			r.Hidden = append(r.Hidden, s.ID)
			r.Slots = append(r.Slots, StackSlot{ID: s.ID, Start: start})
			continue
		}
		if visible > 0 {
			start += gap
		}
		r.Slots = append(r.Slots, StackSlot{ID: s.ID, Start: start, Size: sizes[i]})
		start += sizes[i]
		visible++
	}
	return r, nil
}

type NamedRect struct {
	ID   string
	Rect CellRect
}

func StackRects(parent CellRect, items []StackItem, tokens SpacingTokens, vertical bool) ([]NamedRect, []string, error) {
	if parent.Width < 0 || parent.Height < 0 || tokens.Padding < 0 || tokens.Padding > 1024 {
		return nil, nil, fmt.Errorf("invalid stack rectangle")
	}
	inner := parent.Inset(tokens.Padding)
	total := inner.Width
	if vertical {
		total = inner.Height
	}
	layout, e := StackLayout(items, total, tokens.Gap)
	if e != nil {
		return nil, nil, e
	}
	out := []NamedRect{}
	for _, s := range layout.Slots {
		r := inner
		if vertical {
			r.Y += s.Start
			r.Height = s.Size
		} else {
			r.X += s.Start
			r.Width = s.Size
		}
		out = append(out, NamedRect{ID: s.ID, Rect: r})
	}
	hidden := []string{}
	for _, r := range out {
		if r.Rect.Width == 0 || r.Rect.Height == 0 {
			hidden = append(hidden, r.ID)
		}
	}
	return out, hidden, nil
}

type DrawerPlacement struct {
	Rect    CellRect
	Overlay bool
}

func DrawerLayout(parent CellRect, preferred, minContent int) DrawerPlacement {
	preferred = max(0, preferred)
	minContent = max(0, minContent)
	r := parent
	r.Width = min(max(0, parent.Width), preferred)
	return DrawerPlacement{Rect: r, Overlay: preferred > max(0, parent.Width) || minContent > max(0, parent.Width)-preferred}
}

type ComponentEvent struct{ Kind, ID string }
type Badge struct {
	ID, Label string
	Count     *uint64
	Limit     uint64
	State     ControlState
}

func (b Badge) Line(width int) ComponentLine {
	label := b.Label
	if b.Count != nil {
		limit := b.Limit
		if limit == 0 {
			limit = 99
		}
		count := fmt.Sprint(*b.Count)
		if *b.Count > limit {
			count = fmt.Sprintf("%d+", limit)
		}
		label += " [" + count + "]"
	}
	v := b.State.Visual()
	return ComponentLine{ID: b.ID, Text: CellText(strings.TrimPrefix(v.Markers, "-")+label, width), Role: v.Role}
}

type Chip struct {
	ID, Label string
	State     ControlState
	Removable bool
}

func (c Chip) Line(width int) ComponentLine {
	v := c.State.Visual()
	prefix := strings.TrimPrefix(v.Markers, "-") + "["
	suffix := "]"
	if c.Removable {
		suffix += " x"
	}
	value := prefix + CellText(c.Label, max(0, width-len(prefix)-len(suffix))) + suffix
	return ComponentLine{ID: c.ID, Text: CellText(value, width), Role: v.Role, Value: "remove"}
}
func (c Chip) RequestRemove() ComponentEvent {
	if c.ID != "" && c.Removable && c.State.Visual().Editable {
		return ComponentEvent{Kind: "remove", ID: c.ID}
	}
	return ComponentEvent{}
}

type Shortcut struct {
	Key, Text string
	Priority  int
	Disabled  bool
}
type Help struct{ items []Shortcut }

func NewHelp(items []Shortcut) (*Help, error) {
	seen := map[string]bool{}
	for _, i := range items {
		key := strings.ToLower(strings.TrimSpace(i.Key))
		if key == "" || seen[key] {
			return nil, fmt.Errorf("empty or duplicate shortcut")
		}
		seen[key] = true
	}
	copy := append([]Shortcut(nil), items...)
	sort.SliceStable(copy, func(i, j int) bool { return copy[i].Priority > copy[j].Priority })
	return &Help{items: copy}, nil
}
func (h *Help) Layout(width, height int) []ComponentLine {
	limit := max(0, height)
	if len(h.items) > limit && height > 1 {
		limit--
	}
	out := []ComponentLine{}
	for _, s := range h.items[:min(limit, len(h.items))] {
		role := "body"
		if s.Disabled {
			role = "disabled"
		}
		out = append(out, ComponentLine{Text: CellText("["+s.Key+"] "+s.Text, width), Role: role})
	}
	if len(h.items) > limit && height > len(out) {
		out = append(out, ComponentLine{Text: CellText(fmt.Sprintf("+%d", len(h.items)-limit), width), Role: "hint"})
	}
	return out
}
