package tuivory

// Pointer consumes local grid coordinates. Hosts translate their own mouse
// protocol; down/move/up support range dragging and header-divider resizing.
func (g *Grid) Pointer(action string, x, y, width, height int, extend bool) GridEvent {
	switch action {
	case "down", "move", "up", "click", "double", "wheel_up", "wheel_down", "wheel_left", "wheel_right":
	default:
		return GridEvent{}
	}
	if g.options.DisableMouse {
		return GridEvent{}
	}
	if action == "up" {
		g.dragColumn = ""
		g.dragAnchor = GridRange{}
		return GridEvent{}
	}
	if action == "wheel_up" {
		return g.Handle("up", height)
	}
	if action == "wheel_down" {
		return g.Handle("down", height)
	}
	if action == "wheel_left" {
		return g.Handle("left", height)
	}
	if action == "wheel_right" {
		return g.Handle("right", height)
	}
	if action == "move" && g.dragColumn != "" {
		lo, hi := columnBounds(g.columnOptions[g.dragColumn])
		w := max(lo, min(hi, g.dragWidth+x-g.dragX))
		if g.ResizeColumn(g.dragColumn, w) {
			return GridEvent{Kind: "resize", ColumnID: g.dragColumn}
		}
		return GridEvent{}
	}
	if action == "move" && g.dragAnchor.AnchorRow == "" {
		return GridEvent{}
	}
	if x < 0 || y < 0 || x >= width || y >= height {
		return GridEvent{}
	}
	geo := g.Geometry(width, height)
	if y < geo.HeaderRows {
		if action == "down" && !g.options.DisableResize {
			for _, s := range geo.Columns {
				if x == s.Start+s.Width {
					g.dragColumn = s.ID
					g.dragX = x
					g.dragWidth = max(1, s.Width-2*g.options.Padding)
					return GridEvent{Kind: "resize_start", ColumnID: s.ID}
				}
			}
		}
		if action == "click" || action == "double" {
			return g.Click("", "@header", x, width, height)
		}
		return GridEvent{}
	}
	if y >= height-geo.FooterRows || geo.Stride <= 0 {
		return GridEvent{}
	}
	offset := y - geo.HeaderRows
	if g.options.HorizontalLines && offset%geo.Stride == geo.Stride-1 {
		return GridEvent{}
	}
	index := geo.Top + offset/geo.Stride
	if index >= g.source.Len() {
		return GridEvent{}
	}
	row := g.source.Row(index)
	column := ""
	for _, s := range geo.Columns {
		if x >= s.Start && x < s.Start+s.Width {
			column = s.ID
			break
		}
	}
	if column == "" {
		if x < geo.Gutter && g.options.RowNumbers && g.ColumnID != "" {
			column = g.ColumnID
			if action == "click" || action == "down" {
				g.setMode("row")
			}
		} else {
			return GridEvent{}
		}
	}
	if action == "down" && !extend && !g.WholeRow {
		g.selection = GridRange{}
		g.rangeMode = false
	}
	before := GridRange{AnchorRow: g.RowID, AnchorColumn: g.ColumnID}
	if !g.Focus(row.ID, column) {
		return GridEvent{}
	}
	if action == "down" {
		g.dragAnchor = GridRange{row.ID, column, row.ID, column}
	}
	if action == "move" {
		if g.dragAnchor.AnchorRow == "" {
			return GridEvent{}
		}
		if row.ID == g.dragAnchor.AnchorRow && column == g.dragAnchor.AnchorColumn {
			return GridEvent{}
		}
		r := g.dragAnchor
		r.EndRow = row.ID
		r.EndColumn = column
		if g.SelectRange(r) {
			return GridEvent{Kind: "select", RowID: row.ID, ColumnID: column}
		}
		return GridEvent{}
	}
	if action == "double" {
		return g.Handle("activate", height)
	}
	if action != "down" && action != "click" {
		return GridEvent{}
	}
	if extend {
		r := g.selection
		if _, _, _, _, ok := g.rangeBounds(); !ok {
			r = before
		}
		r.EndRow = row.ID
		r.EndColumn = column
		g.SelectRange(r)
	}
	return g.Handle("select", height)
}
