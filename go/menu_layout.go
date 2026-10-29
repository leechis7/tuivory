package tuivory

import "strings"

func menuLabel(i MenuItem) string {
	label := i.Label
	if i.Mnemonic != "" {
		label += " (" + strings.ToUpper(i.Mnemonic) + ")"
	}
	return label
}
func (m *Menu) rows() []MenuItem {
	rows := []MenuItem{}
	if m.backAllowed() {
		rows = append(rows, MenuItem{ID: "@back", Label: m.BackLabel}, MenuItem{Separator: true})
	}
	for _, id := range m.children[m.parent()] {
		rows = append(rows, m.items[m.index[id]])
	}
	return rows
}

// ContentSize excludes the host panel's border/padding.
func (m *Menu) ContentSize() (int, int) {
	w := 12
	rows := m.rows()
	for _, i := range rows {
		w = max(w, gridTextWidth(menuLabel(i))+gridTextWidth(i.Secondary)+gridTextWidth(i.Shortcut)+gridTextWidth(i.Icon)+8)
	}
	return min(4096, w), max(1, len(rows))
}
func (m *Menu) Layout(width, height int, ascii bool) []ComponentLine {
	if !m.opened || width <= 0 || height <= 0 {
		return nil
	}
	width = min(width, 65535)
	height = min(height, 4096)
	m.reconcile()
	rows := m.rows()
	if len(rows) == 0 {
		return []ComponentLine{{Text: CellText(m.EmptyLabel, width), Role: "hint"}}
	}
	at := 0
	for n, i := range rows {
		if i.ID == m.FocusedID() {
			at = n
		}
	}
	p := m.parent()
	top := max(0, min(m.top[p], at))
	if at >= top+height {
		top = at - height + 1
	}
	top = min(top, max(0, len(rows)-height))
	m.top[p] = top
	out := []ComponentLine{}
	for n := top; n < len(rows) && len(out) < height; n++ {
		i := rows[n]
		if i.Separator {
			dash := "─"
			if ascii {
				dash = "-"
			}
			out = append(out, ComponentLine{Text: strings.Repeat(dash, width), Role: "hint", Value: "@separator"})
			continue
		}
		focused := i.ID == m.FocusedID()
		role := "surface"
		if i.Disabled {
			role = "disabled"
		} else if focused {
			role = "selection"
		}
		prefix := "  "
		if focused {
			prefix = "> "
		}
		icon := i.Icon
		if ascii {
			icon = i.ASCIIIcon
			if icon == "" && i.Icon != "" {
				icon = "*"
			}
		}
		if icon != "" {
			prefix += icon + " "
		}
		label := prefix + menuLabel(i)
		if i.ID == "@back" {
			label = prefix + "< " + i.Label
		}
		if i.Secondary != "" {
			label += "  " + i.Secondary
		}
		suffix := ""
		if len(m.children[i.ID]) > 0 {
			suffix = " ›"
			if ascii {
				suffix = " >"
			}
		}
		shortcut := cleanTreeText(i.Shortcut)
		reserve := min(width/3, gridTextWidth(shortcut))
		if reserve > 0 {
			reserve++
		}
		tail := suffix
		if reserve > 0 {
			tail = " " + gridFit(shortcut, reserve-1, 0, "clip") + suffix
		}
		tw := min(width, gridTextWidth(tail))
		if tw > 0 {
			tail = gridFit(tail, tw, 0, "clip")
		}
		line := ComponentLine{ID: i.ID, Role: role, Focused: focused, Spans: []ComponentSpan{{Start: 0, Width: width, Text: CellText(label, max(0, width-tw)), Role: role, Focused: focused}}}
		if tw > 0 {
			secondaryRole := role
			if role == "surface" {
				secondaryRole = "hint"
			}
			line.Spans = append(line.Spans, ComponentSpan{Start: width - tw, Width: tw, Text: tail, Role: secondaryRole, Focused: focused})
		}
		out = append(out, line)
	}
	return out
}
func (m *Menu) BarLayout(width int) MenuBarLayout {
	out := MenuBarLayout{}
	width = min(65535, max(0, width))
	if width < 3 {
		return out
	}
	ids := m.children[""]
	if len(ids) == 0 {
		return out
	}
	target := 0
	for n, id := range ids {
		if id == m.bar {
			target = n
		}
	}
	m.barFirst = max(0, min(m.barFirst, target))
	size := func(n int) int { return min(24, gridTextWidth(menuLabel(m.items[m.index[ids[n]]]))+2) }
	for m.barFirst < target {
		used := 0
		for n := m.barFirst; n <= target; n++ {
			used += size(n)
		}
		if used <= width-2 {
			break
		}
		m.barFirst++
	}
	for m.barFirst > 0 {
		used := 0
		for n := m.barFirst - 1; n <= target; n++ {
			used += size(n)
		}
		if used > width-2 {
			break
		}
		m.barFirst--
	}
	x := 1
	last := m.barFirst
	for n := m.barFirst; n < len(ids) && x < width-1; n++ {
		i := m.items[m.index[ids[n]]]
		if i.Separator {
			continue
		}
		w := min(size(n), width-1-x)
		role := "header"
		focused := i.ID == m.bar
		if focused {
			role = "selection"
		}
		if i.Disabled {
			role = "disabled"
		}
		out.Cells = append(out.Cells, MenuBarCell{i.ID, CellText(" "+menuLabel(i)+" ", w), role, x, w, focused})
		x += w
		last = n + 1
	}
	out.Previous = m.barFirst > 0
	out.Next = last < len(ids)
	return out
}
func (m *Menu) BarClick(x, width int) MenuEvent {
	l := m.BarLayout(width)
	if x == 0 && l.Previous {
		return m.HandleBar("previous", "")
	}
	if x == width-1 && l.Next {
		return m.HandleBar("next", "")
	}
	for _, c := range l.Cells {
		if x >= c.Start && x < c.Start+c.Width && m.usable(c.ID, "") {
			m.bar = c.ID
			return MenuEvent{Kind: "open_request", ID: c.ID}
		}
	}
	return MenuEvent{}
}

// MenuPlacement clamps only the popup rectangle. Hosts choose anchors, panel
// padding and when/where the popup is shown; no backdrop or screen layout is owned.
func MenuPlacement(anchor, viewport CellRect, width, height int) CellRect {
	vw, vh := max(0, viewport.Width), max(0, viewport.Height)
	w, h := min(vw, max(0, width)), min(vh, max(0, height))
	x := max(viewport.X, min(viewport.X+vw-w, anchor.X))
	y := anchor.Y + max(0, anchor.Height)
	if y+h > viewport.Y+vh {
		y = anchor.Y - h
	}
	y = max(viewport.Y, min(viewport.Y+vh-h, y))
	return CellRect{X: x, Y: y, Width: w, Height: h}
}
