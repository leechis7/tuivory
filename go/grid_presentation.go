package tuivory

import (
	"fmt"
	"github.com/rivo/uniseg"
	"strconv"
	"strings"
)

func gridTextWidth(s string) int { return uniseg.StringWidth(cleanTreeText(s)) }
func gridFit(s string, width, offset int, overflow string) string {
	width = max(0, width)
	s = cleanTreeText(s)
	if overflow == "scroll" && offset > 0 {
		gr := uniseg.NewGraphemes(s)
		used := 0
		var out strings.Builder
		for gr.Next() {
			w := gr.Width()
			if used >= offset {
				out.WriteString(gr.Str())
			} else if used+w > offset {
				out.WriteString(strings.Repeat(" ", used+w-offset))
			}
			used += w
		}
		s = out.String()
	}
	if overflow == "clip" {
		var out strings.Builder
		used := 0
		gr := uniseg.NewGraphemes(s)
		for gr.Next() {
			if used+gr.Width() > width {
				break
			}
			out.WriteString(gr.Str())
			used += gr.Width()
		}
		return out.String()
	}
	return CellText(s, width)
}
func gridAlign(s string, width int, align string) string {
	left := 0
	pad := max(0, width-gridTextWidth(s))
	if align == "right" {
		left = pad
	} else if align == "center" {
		left = pad / 2
	}
	return strings.Repeat(" ", left) + s + strings.Repeat(" ", pad-left)
}

// GridPalette returns derived semantic styles without changing shared token roles.
// Existing grid.* overrides in palette are retained.
func GridPalette(palette Palette) Palette {
	p := Palette{}
	for k, v := range palette {
		p[k] = v
	}
	base := p["surface"]
	base.FG = p["body"].FG
	current := base
	current.BG = p["body"].BG
	current.Bold = true
	stripe := base
	if editor, ok := p["editor"]; ok {
		stripe.BG = editor.BG
	}
	hint := p["hint"]
	hint.BG = base.BG
	aliases := map[string]Pair{"grid.base": base, "grid.stripe": stripe, "grid.current-row": current, "grid.active": p["selection"], "grid.range": p["selection"], "grid.edited": p["edited"], "grid.header-active": p["header"], "grid.gutter": hint, "grid.divider": hint, "grid.status": p["header"], "grid.null": hint, "grid.readonly": hint, "grid.loading": hint}
	for k, v := range aliases {
		if _, ok := p[k]; !ok {
			p[k] = v
		}
	}
	return p
}

type gridWindow struct {
	geometry GridGeometry
	records  []GridRecord
}

func (g *Grid) window(width, height int) gridWindow {
	width = min(65535, max(0, width))
	height = min(4096, max(0, height))
	o := g.options
	result := gridWindow{}
	geo := &result.geometry
	geo.Stride = 1 + o.RowSpacing
	if o.HorizontalLines {
		geo.Stride++
	}
	if width == 0 || height == 0 || len(g.columns) == 0 {
		return result
	}
	geo.Gutter = 3
	if o.HideMarkers {
		geo.Gutter = 0
	}
	if o.RowNumbers {
		geo.Gutter = len(strconv.Itoa(max(1, g.source.Len()))) + 3
		if o.HideMarkers {
			geo.Gutter--
		}
	}
	geo.Gutter = min(width, max(geo.Gutter, o.GutterWidth))
	if !o.HideHeader {
		geo.HeaderRows = 1
	}
	if o.StatusBar && height >= 3 {
		geo.FooterRows = 1
	}
	rows := max(0, (height-geo.HeaderRows-geo.FooterRows+geo.Stride-1)/geo.Stride)
	geo.Top = max(0, min(g.Top, g.Row))
	if rows > 0 && g.Row >= geo.Top+rows {
		geo.Top = g.Row - rows + 1
	}
	geo.Top = min(geo.Top, max(0, g.source.Len()-rows))
	if o.ScrollHeader && geo.Top > 0 {
		geo.HeaderRows = 0
		rows = max(0, (height-geo.FooterRows+geo.Stride-1)/geo.Stride)
	}
	geo.BodyRows = rows
	for n := geo.Top; n < g.source.Len() && len(result.records) < rows; n++ {
		result.records = append(result.records, g.source.Row(n))
	}
	widths := make([]int, len(g.columns))
	for c, col := range g.columns {
		opts := g.columnOptions[col.ID]
		lo, hi := columnBounds(opts)
		w := col.Width
		if opts.AutoFit {
			w = gridTextWidth(col.Label) + 2
			for _, r := range result.records {
				info := g.info(r, col)
				s := r.Cells[col.ID]
				if info.HasDisplay {
					s = info.Display
				}
				if info.Null && !info.HasDisplay {
					s = g.label("null", "NULL")
				}
				w = max(w, gridTextWidth(s)+func() int {
					if o.ShowCellMarkers {
						return 2
					}
					return 0
				}())
			}
		}
		widths[c] = max(lo, min(hi, w))
	}
	physical := func(c int) int { return widths[c] + 2*o.Padding + 1 }
	geo.Left = max(0, min(g.Left, g.Column))
	capacity := max(0, width-geo.Gutter)
	for geo.Left < g.Column {
		used := 0
		for c := geo.Left; c <= g.Column; c++ {
			used += physical(c)
		}
		if used <= capacity {
			break
		}
		geo.Left++
	}
	used := 0
	end := geo.Left
	for end < len(g.columns) && used < capacity {
		used += physical(end)
		end++
	}
	extra := max(0, capacity-used)
	weight := 0
	for c := geo.Left; c < end; c++ {
		weight += g.columnOptions[g.columns[c].ID].Expand
	}
	if weight > 0 && extra > 0 {
		for c := geo.Left; c < end; c++ {
			opt := g.columnOptions[g.columns[c].ID]
			add := extra * opt.Expand / weight
			_, hi := columnBounds(opt)
			widths[c] = min(hi, widths[c]+add)
		}
	}
	x := geo.Gutter
	for c := geo.Left; c < len(g.columns) && x < width; c++ {
		w := min(width-x, widths[c]+2*o.Padding)
		geo.Columns = append(geo.Columns, GridSpan{g.columns[c].ID, x, w})
		x += w + 1
	}
	return result
}
func (g *Grid) Geometry(width, height int) GridGeometry { return g.window(width, height).geometry }
func (g *Grid) cellText(row GridRecord, column GridColumn, width int, selected bool) string {
	o := g.options
	co := g.columnOptions[column.ID]
	info := g.info(row, column)
	state := combineGridState(row.State, info.State)
	if g.rangeMode && selected && o.ShowCellMarkers {
		state.Selected = true
	}
	raw := row.Cells[column.ID]
	if info.HasDisplay {
		raw = info.Display
	} else if info.Null {
		raw = g.label("null", "NULL")
	}
	prefix := ""
	if selected && !o.HideSelectionMarker {
		prefix = "> "
	}
	if o.ShowCellMarkers {
		prefix += state.Visual().Markers
		if prefix != "" {
			prefix += " "
		}
	}
	content := max(0, width-2*o.Padding)
	text := gridFit(prefix+raw, content, g.cellPan[column.ID], co.Overflow)
	align := co.Align
	if align == "numeric" {
		align = "left"
		if info.Numeric {
			align = "right"
		}
	}
	return gridFit(strings.Repeat(" ", min(o.Padding, width))+gridAlign(text, content, align)+strings.Repeat(" ", min(o.Padding, width)), width, 0, "clip")
}
func (g *Grid) selected(row, col int, r GridRecord, c GridColumn) bool {
	if g.rangeMode && !g.WholeRow {
		r1, r2, c1, c2, ok := g.rangeBounds()
		return ok && row >= r1 && row <= r2 && col >= c1 && col <= c2
	}
	return r.ID == g.SelectedRow && (g.WholeRow || c.ID == g.SelectedColumn)
}
func (g *Grid) rowRole(row GridRecord, index int) string {
	role := row.State.Visual().Role
	if role == "body" {
		if g.options.UseSurface {
			role = "grid.base"
		}
		if g.options.Striped && index%2 == 1 {
			role = "grid.stripe"
		}
		if g.options.HighlightRow && row.ID == g.RowID {
			role = "grid.current-row"
		}
	}
	return role
}
func (g *Grid) cellRole(row GridRecord, col GridColumn, index int, selected bool) string {
	info := g.info(row, col)
	s := combineGridState(row.State, info.State)
	role := g.rowRole(row, index)
	switch {
	case s.Disabled:
		return "disabled"
	case s.Invalid:
		return "error"
	case s.Edited && g.options.PreserveEdited:
		return "grid.edited"
	case g.options.HighlightCell && row.ID == g.RowID && col.ID == g.ColumnID:
		return "grid.active"
	case selected:
		if g.rangeMode && !g.WholeRow {
			return "grid.range"
		}
		return "selection"
	case s.Edited:
		return "edited"
	case s.Busy && (g.options.UseSurface || g.cellInfo != nil):
		return "grid.loading"
	case s.ReadOnly && (g.options.UseSurface || g.cellInfo != nil):
		return "grid.readonly"
	case info.Null:
		return "grid.null"
	}
	return role
}
func (g *Grid) decorations(line *ComponentLine, geo GridGeometry, width int, header bool, row GridRecord, index int) {
	o := g.options
	vertical := "│"
	if o.ASCII {
		vertical = "|"
	}
	if o.RowNumbers && geo.Gutter > 0 {
		label := "#"
		role := "grid.gutter"
		if header {
			role = "header"
		} else {
			label = strconv.Itoa(index + 1)
			if !o.HideMarkers {
				if row.State.Edited {
					label = "*" + label
				}
				if row.ID == g.RowID {
					label = ">" + label
				}
			}
		}
		w := geo.Gutter
		if o.VerticalLines {
			w = max(0, w-1)
		}
		line.Spans = append(line.Spans, ComponentSpan{Start: 0, Width: w, Text: gridAlign(gridFit(label, w, 0, "clip"), w, "right"), Role: role})
	}
	if o.VerticalLines {
		if geo.Gutter > 0 {
			line.Spans = append(line.Spans, ComponentSpan{Start: geo.Gutter - 1, Width: 1, Text: vertical, Role: "grid.divider"})
		}
		for _, span := range geo.Columns {
			at := span.Start + span.Width
			if at < width {
				line.Spans = append(line.Spans, ComponentSpan{Start: at, Width: 1, Text: vertical, Role: "grid.divider"})
			}
		}
	}
}
func (g *Grid) Layout(width, height int) []ComponentLine {
	g.reconcile()
	width = min(65535, max(0, width))
	height = min(4096, max(0, height))
	g.lastWidth = width
	g.lastHeight = height
	if width == 0 || height == 0 || len(g.columns) == 0 {
		return nil
	}
	window := g.window(width, height)
	geo := window.geometry
	o := g.options
	out := []ComponentLine{}
	if geo.HeaderRows > 0 {
		header := ComponentLine{Role: "header", Value: "@header"}
		for _, s := range geo.Columns {
			col := g.columns[g.columnIndex(s.ID)]
			label := col.Label
			if s.ID == g.SortColumn {
				label += " " + g.SortDirection
			}
			if s.ID == g.ColumnID && !o.HideSelectionMarker {
				label = "> " + label
			}
			role := "header"
			if s.ID == g.ColumnID && o.HighlightCell {
				role = "grid.header-active"
			}
			content := max(0, s.Width-2*o.Padding)
			label = strings.Repeat(" ", min(o.Padding, s.Width)) + gridAlign(CellText(label, content), content, g.columnOptions[s.ID].Align)
			header.Spans = append(header.Spans, ComponentSpan{Start: s.Start, Width: s.Width, Text: label, Role: role, Focused: s.ID == g.ColumnID})
		}
		g.decorations(&header, geo, width, true, GridRecord{}, 0)
		out = append(out, header)
	}
	bodyLimit := height - geo.FooterRows
	if g.source.Len() == 0 && len(out) < bodyLimit {
		message, role := g.Empty, "hint"
		if g.Status.Loading {
			message = g.label("loading", "loading")
		}
		if g.Status.Error != "" {
			message = g.Status.Error
			role = "error"
		}
		out = append(out, ComponentLine{Text: CellText(message, width), Role: role})
	}
	for i, row := range window.records {
		if len(out) >= bodyLimit {
			break
		}
		index := geo.Top + i
		v := row.State.Visual()
		marker := "  "
		if row.ID == g.RowID {
			marker = "> "
		}
		if o.HideMarkers {
			marker = ""
		}
		line := ComponentLine{ID: row.ID, Text: marker + v.Markers, Role: g.rowRole(row, index), Focused: row.ID == g.RowID}
		for _, s := range geo.Columns {
			colindex := g.columnIndex(s.ID)
			col := g.columns[colindex]
			selected := g.selected(index, colindex, row, col)
			line.Spans = append(line.Spans, ComponentSpan{Start: s.Start, Width: s.Width, Text: g.cellText(row, col, s.Width, selected), Role: g.cellRole(row, col, index, selected), Focused: row.ID == g.RowID && s.ID == g.ColumnID})
		}
		g.decorations(&line, geo, width, false, row, index)
		out = append(out, line)
		for pad := 0; pad < o.RowSpacing && len(out) < bodyLimit; pad++ {
			blank := line
			blank.Text = ""
			blank.Value = "@padding"
			blank.Focused = false
			blank.Spans = append([]ComponentSpan(nil), line.Spans...)
			for j := range blank.Spans {
				blank.Spans[j].Text = ""
				blank.Spans[j].Focused = false
			}
			g.decorations(&blank, geo, width, false, row, index)
			out = append(out, blank)
		}
		if o.HorizontalLines && i+1 < len(window.records) && len(out) < bodyLimit {
			dash := "─"
			cross := "┼"
			if o.ASCII {
				dash = "-"
				cross = "+"
			}
			separator := ComponentLine{Text: strings.Repeat(dash, width), Role: "grid.divider", Value: "@separator"}
			if o.VerticalLines {
				if geo.Gutter > 0 {
					separator.Spans = append(separator.Spans, ComponentSpan{Start: geo.Gutter - 1, Width: 1, Text: cross, Role: "grid.divider"})
				}
				for _, s := range geo.Columns {
					if s.Start+s.Width < width {
						separator.Spans = append(separator.Spans, ComponentSpan{Start: s.Start + s.Width, Width: 1, Text: cross, Role: "grid.divider"})
					}
				}
			}
			out = append(out, separator)
		}
	}
	if geo.FooterRows > 0 {
		for len(out) < height-1 {
			out = append(out, ComponentLine{Role: "grid.base"})
		}
		bar := StatusLine(g.StatusItems(), width)
		text := ""
		for _, run := range bar.Runs {
			text += run.Text
		}
		role := "grid.status"
		if g.Status.Error != "" {
			role = "error"
		}
		out = append(out, ComponentLine{Text: text, Role: role, Value: "@status"})
	}
	return out
}

// StatusItems may be rendered separately by the public StatusView as well.
func (g *Grid) StatusItems() []StatusItem {
	total := max(g.source.Len(), g.Status.TotalRows)
	row := 0
	if g.RowID != "" {
		row = g.Row + 1
	}
	col := 0
	if g.ColumnID != "" {
		col = g.Column + 1
	}
	all := map[string]StatusItem{
		"position": {ID: "position", Text: fmt.Sprintf("%s %d/%d %s %d/%d", g.label("row", "R"), row, total, g.label("column", "C"), col, len(g.columns)), Priority: 30, Role: "body"},
	}
	if col > 0 {
		c := g.columns[g.Column]
		all["column"] = StatusItem{ID: "column", Text: c.Label, Priority: 20, Role: "hint"}
	}
	if r1, r2, c1, c2, ok := g.rangeBounds(); ok && g.rangeMode {
		all["selection"] = StatusItem{ID: "selection", Text: fmt.Sprintf("%s %dx%d", g.label("selected", "selected"), r2-r1+1, c2-c1+1), Priority: 40, Role: "info"}
	}
	if g.SortColumn != "" {
		all["sort"] = StatusItem{ID: "sort", Text: g.label("sort", "sort") + " " + g.SortColumn + " " + g.SortDirection, Priority: 10, Role: "hint"}
	}
	if g.Status.Filter != "" {
		all["filter"] = StatusItem{ID: "filter", Text: g.label("filter", "filter") + " " + g.Status.Filter, Priority: 10, Role: "hint"}
	}
	if g.Status.Loading {
		all["loading"] = StatusItem{ID: "loading", Text: g.label("loading", "loading"), Priority: 80, Role: "info"}
	}
	if g.Status.HasMore {
		all["more"] = StatusItem{ID: "more", Text: g.label("more", "more"), Priority: 50, Role: "info"}
	}
	meta := g.Status.Metadata
	if g.cellInfo != nil && g.RowID != "" && col > 0 {
		cellMeta := g.info(g.source.Row(g.Row), g.columns[g.Column]).Metadata
		if cellMeta != "" {
			if meta != "" {
				meta += " / "
			}
			meta += cellMeta
		}
	}
	if meta != "" {
		all["meta"] = StatusItem{ID: "meta", Text: meta, Priority: 15, Role: "hint"}
	}
	if g.Status.Error != "" {
		all["error"] = StatusItem{ID: "error", Text: g.Status.Error, Priority: 100, Role: "error"}
	}
	fields := g.options.StatusFields
	if fields == nil {
		fields = []string{"error", "position", "column", "selection", "loading", "more", "sort", "filter", "meta"}
	}
	out := []StatusItem{}
	for _, key := range fields {
		if item, ok := all[key]; ok {
			out = append(out, item)
		}
	}
	return out
}
