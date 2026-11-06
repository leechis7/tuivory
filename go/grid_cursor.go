package tuivory

import "strings"

// GridCursor is an editor caret in local terminal-cell coordinates, not bytes.
// Views apply their own origin, focus and final screen clipping.
type GridCursor struct {
	X, Y  int
	Width int
}

// gridEditorWindow shares its grapheme viewport with drawing and mouse input.
// Reserve the next complete glyph (or a blank at end); never insert a fake caret.
func gridEditorWindow(value string, cursor, width int) (text string, x, start int) {
	gs := clusters(value)
	cursor = max(0, min(cursor, len(gs)))
	start = cursor
	reserve := 1
	if cursor < len(gs) {
		reserve = max(1, gridTextWidth(gs[cursor]))
	}
	reserve = min(max(0, width), reserve)
	for start > 0 {
		w := gridTextWidth(gs[start-1])
		if x+w > max(0, width-reserve) {
			break
		}
		start--
		x += w
	}
	text = gridFit(strings.Join(gs[start:], ""), width, 0, "clip")
	return
}

// EditCursor returns a visible editor position for this viewport. Pending, NULL,
// invalidated, uneditable and clipped editors have no caret. Focus is view-owned.
func (g *Grid) EditCursor(width, height int) (GridCursor, bool) {
	e := g.work.edit
	if e == nil || e.Pending || e.Value.Null || g.work.detail != nil || g.work.findBuffer != nil || width <= 0 || height <= 0 {
		return GridCursor{}, false
	}
	row := g.source.IndexOf(e.RowID)
	col := g.columnIndex(e.ColumnID)
	if row < 0 || row >= g.source.Len() || col < 0 || g.source.Row(row).ID != e.RowID || !g.editable(g.source.Row(row), g.columns[col]) || !g.prepared(g.source.Row(row), g.columns[col]) {
		return GridCursor{}, false
	}
	geo := g.Geometry(width, height)
	y := geo.HeaderRows + (row-geo.Top)*geo.Stride
	if row < geo.Top || row >= geo.Top+geo.BodyRows || y < geo.HeaderRows || y >= height-geo.FooterRows {
		return GridCursor{}, false
	}
	for _, s := range geo.Columns {
		if s.ID != e.ColumnID {
			continue
		}
		extra := 0
		if g.info(g.source.Row(row), g.columns[col]).State.Edited {
			extra = 2
		}
		space := s.Width - 2*g.options.Padding - extra
		if space <= 0 {
			return GridCursor{}, false
		}
		_, cx, _ := gridEditorWindow(g.work.buffer.Text(), g.work.buffer.Cursor, space)
		cw := 1
		gs := clusters(g.work.buffer.Text())
		if g.work.buffer.Cursor < len(gs) {
			cw = max(1, gridTextWidth(gs[g.work.buffer.Cursor]))
			if cw > space {
				cw = 1
			}
		}
		return GridCursor{X: s.Start + g.options.Padding + extra + cx, Y: y, Width: cw}, true
	}
	return GridCursor{}, false
}
