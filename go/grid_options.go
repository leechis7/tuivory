package tuivory

import (
	"fmt"
	"strings"
)

// GridOptions configures the existing Grid; its zero value preserves v0.2.0.
// SetOptions never replaces data, IDs, column widths, or stored selections.
type GridOptions struct {
	RowNumbers, HideMarkers, VerticalLines, HorizontalLines, Striped, UseSurface                 bool
	HideHeader, ScrollHeader, StatusBar, ASCII                                                   bool
	HighlightCell, HighlightRow, PreserveEdited, HideSelectionMarker, ShowCellMarkers            bool
	DisableKeyboard, DisableMouse, DisableEditing, DisableCopy, DisableResize, DisableHeaderSort bool
	Padding, RowSpacing, GutterWidth, MaxCopyCells                                               int
	Selection                                                                                    string   // Empty preserves the current mode; cell, row, or range.
	StatusFields                                                                                 []string // nil: all built-in status items.
}

type GridColumnOptions struct {
	Align              string // left, center, right, numeric (host-classified numeric cells).
	MinWidth, MaxWidth int
	AutoFit            bool // Measure only the displayed window; never scan the source.
	Expand             int
	Overflow           string // ellipsis (default), clip, scroll.
}

// GridCellInfo is host presentation metadata. GridRecord.Cells remain raw values.
type GridCellInfo struct {
	Display                   string
	HasDisplay, Null, Numeric bool
	State                     ControlState
	Metadata                  string
}
type GridRange struct{ AnchorRow, AnchorColumn, EndRow, EndColumn string }
type GridDataStatus struct {
	TotalRows               int // 0: use loaded source length.
	Metadata, Filter, Error string
	Loading, HasMore        bool
}
type GridGeometry struct {
	Top, Left, Gutter, HeaderRows, FooterRows, BodyRows, Stride int
	Columns                                                     []GridSpan
}

func GridPreset(name string) (GridOptions, error) {
	switch name {
	case "simple", "":
		return GridOptions{}, nil
	case "data":
		return GridOptions{RowNumbers: true, VerticalLines: true, UseSurface: true, Padding: 1, StatusBar: true, HighlightCell: true, HighlightRow: true, PreserveEdited: true, HideSelectionMarker: true, ShowCellMarkers: true}, nil
	}
	return GridOptions{}, fmt.Errorf("unknown grid preset %q", name)
}

// WithDensity returns a spacing option bundle; other options are retained.
func (o GridOptions) WithDensity(name string) (GridOptions, error) {
	switch name {
	case "compact":
		o.Padding = 0
		o.RowSpacing = 0
	case "normal":
		o.Padding = 1
		o.RowSpacing = 0
	case "comfortable":
		o.Padding = 1
		o.RowSpacing = 1
	default:
		return o, fmt.Errorf("invalid grid density %q", name)
	}
	return o, nil
}
func (g *Grid) SetOptions(o GridOptions) error {
	if o.Padding < 0 || o.Padding > 8 || o.RowSpacing < 0 || o.RowSpacing > 4 || o.GutterWidth < 0 || o.GutterWidth > 128 || o.MaxCopyCells < 0 || o.MaxCopyCells > 1000000 {
		return fmt.Errorf("invalid grid option bounds")
	}
	if o.Selection != "" && o.Selection != "cell" && o.Selection != "row" && o.Selection != "range" {
		return fmt.Errorf("invalid grid selection mode")
	}
	valid := map[string]bool{"position": true, "column": true, "selection": true, "sort": true, "filter": true, "loading": true, "more": true, "meta": true, "error": true}
	seen := map[string]bool{}
	for _, s := range o.StatusFields {
		if !valid[s] || seen[s] {
			return fmt.Errorf("invalid grid status field %q", s)
		}
		seen[s] = true
	}
	if o.StatusFields != nil {
		o.StatusFields = append([]string{}, o.StatusFields...)
	}
	if o.Selection != "" {
		g.setMode(o.Selection)
	}
	g.options = o
	return nil
}
func (g *Grid) Options() GridOptions {
	o := g.options
	if o.StatusFields != nil {
		o.StatusFields = append([]string{}, o.StatusFields...)
	}
	return o
}
func (g *Grid) SetColumnOptions(id string, o GridColumnOptions) error {
	found := false
	for _, c := range g.columns {
		if c.ID == id {
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("unknown grid column %q", id)
	}
	if o.Align != "" && o.Align != "left" && o.Align != "center" && o.Align != "right" && o.Align != "numeric" {
		return fmt.Errorf("invalid grid alignment")
	}
	if o.Overflow != "" && o.Overflow != "ellipsis" && o.Overflow != "clip" && o.Overflow != "scroll" {
		return fmt.Errorf("invalid grid overflow")
	}
	low, high := columnBounds(o)
	if o.MinWidth < 0 || o.MaxWidth < 0 || low > high || high > 4096 || o.Expand < 0 || o.Expand > 1000000 {
		return fmt.Errorf("invalid grid column bounds")
	}
	if g.columnOptions == nil {
		g.columnOptions = map[string]GridColumnOptions{}
	}
	g.columnOptions[id] = o
	return nil
}
func columnBounds(o GridColumnOptions) (int, int) {
	low, high := max(1, o.MinWidth), o.MaxWidth
	if high == 0 {
		high = 4096
	}
	return low, high
}
func (g *Grid) ColumnOptions(id string) GridColumnOptions                  { return g.columnOptions[id] }
func (g *Grid) SetCellInfo(info func(GridRecord, GridColumn) GridCellInfo) { g.cellInfo = info }
func (g *Grid) info(row GridRecord, c GridColumn) GridCellInfo {
	if g.cellInfo != nil {
		return g.cellInfo(row, c)
	}
	return GridCellInfo{}
}
func combineGridState(a, b ControlState) ControlState {
	return ControlState{Disabled: a.Disabled || b.Disabled, ReadOnly: a.ReadOnly || b.ReadOnly, Busy: a.Busy || b.Busy, Selected: a.Selected || b.Selected, Edited: a.Edited || b.Edited, Invalid: a.Invalid || b.Invalid}
}
func (g *Grid) mode() string {
	if g.WholeRow {
		return "row"
	}
	if g.rangeMode {
		return "range"
	}
	return "cell"
}
func (g *Grid) SelectionMode() string { return g.mode() }
func (g *Grid) setMode(mode string)   { g.WholeRow = mode == "row"; g.rangeMode = mode == "range" }
func (g *Grid) SetSelectionMode(mode string) error {
	if mode != "cell" && mode != "row" && mode != "range" {
		return fmt.Errorf("invalid grid selection mode")
	}
	g.setMode(mode)
	return nil
}
func (g *Grid) columnIndex(id string) int {
	for i, c := range g.columns {
		if c.ID == id {
			return i
		}
	}
	return -1
}
func (g *Grid) rangeBounds() (int, int, int, int, bool) {
	r := g.selection
	ar, er := g.source.IndexOf(r.AnchorRow), g.source.IndexOf(r.EndRow)
	ac, ec := g.columnIndex(r.AnchorColumn), g.columnIndex(r.EndColumn)
	if ar < 0 || er < 0 || ar >= g.source.Len() || er >= g.source.Len() || ac < 0 || ec < 0 {
		return 0, 0, 0, 0, false
	}
	return min(ar, er), max(ar, er), min(ac, ec), max(ac, ec), true
}
func (g *Grid) SelectRange(r GridRange) bool {
	old := g.selection
	g.selection = r
	if _, _, _, _, ok := g.rangeBounds(); !ok {
		g.selection = old
		return false
	}
	g.setMode("range")
	g.SelectedRow = r.EndRow
	g.SelectedColumn = r.EndColumn
	return true
}
func (g *Grid) SelectedRange() GridRange { return g.selection }
func (g *Grid) Revision() uint64         { return g.revision }
func (g *Grid) ApplySource(revision uint64, source GridSource) bool {
	if source == nil || revision != g.revision || revision <= g.appliedRevision {
		return false
	}
	g.SetSource(source)
	g.appliedRevision = revision
	return true
}
func (g *Grid) label(key, fallback string) string {
	if s, ok := g.Labels[key]; ok {
		return s
	}
	return fallback
}
func (g *Grid) nextRequest() { g.revision++ }
func (g *Grid) RequestPage() GridEvent {
	if !g.Status.HasMore || g.Status.Loading {
		return GridEvent{}
	}
	g.nextRequest()
	return GridEvent{Kind: "load_more"}
}
func tsvValue(s string) string {
	if strings.ContainsAny(s, "\t\r\n\"") {
		return "\"" + strings.ReplaceAll(s, "\"", "\"\"") + "\""
	}
	return s
}
func (g *Grid) copyRange() GridEvent {
	e := GridEvent{Kind: "copy", RowID: g.RowID, ColumnID: g.ColumnID}
	r1, r2, c1, c2, ok := g.rangeBounds()
	if !ok {
		return GridEvent{}
	}
	limit := g.options.MaxCopyCells
	if limit == 0 {
		limit = 10000
	}
	if r2-r1+1 > limit/(c2-c1+1) {
		e.Kind = "copy_request"
		return e
	}
	rows := []string{}
	for r := r1; r <= r2; r++ {
		row := g.source.Row(r)
		cells := []string{}
		for c := c1; c <= c2; c++ {
			cells = append(cells, tsvValue(row.Cells[g.columns[c].ID]))
		}
		rows = append(rows, strings.Join(cells, "\t"))
	}
	e.Text = strings.Join(rows, "\n")
	return e
}
func (g *Grid) extraAction(action string, height int) (GridEvent, bool) {
	e := GridEvent{RowID: g.RowID, ColumnID: g.ColumnID}
	if strings.HasPrefix(action, "extend_") {
		anchor := g.selection
		if _, _, _, _, ok := g.rangeBounds(); !ok || !g.rangeMode {
			anchor = GridRange{AnchorRow: g.RowID, AnchorColumn: g.ColumnID}
		}
		event := g.Handle(strings.TrimPrefix(action, "extend_"), height)
		if event.Kind != "" {
			anchor.EndRow = g.RowID
			anchor.EndColumn = g.ColumnID
			g.SelectRange(anchor)
			event.Kind = "select"
		}
		return event, true
	}
	switch action {
	case "range_start":
		g.SelectRange(GridRange{g.RowID, g.ColumnID, g.RowID, g.ColumnID})
		e.Kind = "select"
		return e, true
	case "range_mode":
		g.rangeMode = !g.rangeMode
		g.WholeRow = false
		if g.rangeMode {
			g.SelectRange(GridRange{g.RowID, g.ColumnID, g.RowID, g.ColumnID})
		}
		e.Kind = "mode"
		return e, true
	case "cancel":
		g.selection = GridRange{}
		g.rangeMode = false
		g.SelectedRow = ""
		g.SelectedColumn = ""
		e.Kind = "cancel"
		return e, true
	case "copy_range":
		if g.options.DisableCopy {
			return GridEvent{}, true
		}
		return g.copyRange(), true
	case "copy":
		if g.options.DisableCopy {
			return GridEvent{}, true
		}
		if g.rangeMode && !g.WholeRow {
			return g.copyRange(), true
		}
	case "copy_cell", "copy_row":
		if g.options.DisableCopy || g.RowID == "" {
			return GridEvent{}, true
		}
		r := g.source.Row(g.Row)
		e.Kind = "copy"
		e.Text = r.Cells[g.ColumnID]
		if action == "copy_row" {
			v := []string{}
			for _, c := range g.columns {
				v = append(v, r.Cells[c.ID])
			}
			e.Text = strings.Join(v, "\t")
		}
		return e, true
	case "details":
		if g.RowID != "" {
			e.Kind = "details"
			e.Text = g.source.Row(g.Row).Cells[g.ColumnID]
		}
		return e, true
	case "load_more":
		return g.RequestPage(), true
	case "cell_pan_left", "cell_pan_right":
		if g.cellPan == nil {
			g.cellPan = map[string]int{}
		}
		delta := 1
		if action == "cell_pan_left" {
			delta = -1
		}
		g.cellPan[g.ColumnID] = max(0, min(1000000, g.cellPan[g.ColumnID]+delta))
		e.Kind = "pan"
		return e, true
	case "autofit":
		if !g.options.DisableResize && g.AutoFitColumn(g.ColumnID, height) {
			e.Kind = "resize"
		}
		return e, true
	case "widen", "narrow":
		if g.options.DisableResize {
			return GridEvent{}, true
		}
	}
	return GridEvent{}, false
}
func (g *Grid) AutoFitColumn(id string, height int) bool {
	col := g.columnIndex(id)
	if col < 0 {
		return false
	}
	c := g.columns[col]
	width := gridTextWidth(c.Label) + 2
	geo := g.Geometry(max(1, g.lastWidth), height)
	top := geo.Top
	end := min(g.source.Len(), top+max(1, geo.BodyRows))
	for n := top; n < end; n++ {
		r := g.source.Row(n)
		info := g.info(r, c)
		s := r.Cells[id]
		if info.HasDisplay {
			s = info.Display
		}
		width = max(width, gridTextWidth(s))
	}
	lo, hi := columnBounds(g.columnOptions[id])
	return g.ResizeColumn(id, max(lo, min(hi, width)))
}
