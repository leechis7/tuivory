package tuivory

import (
	"fmt"
	"strings"
)

type GridColumn struct {
	ID, Label string
	Width     int
	Editable  bool
}
type GridRecord struct {
	ID    string
	Cells map[string]string
	State ControlState
}

// GridSource enables lazy/windowed application data. IndexOf must locate stable
// IDs without a full scan for large sources; Row returns data only on demand.
type GridSource interface {
	Len() int
	Row(int) GridRecord
	IndexOf(string) int
}
type MemoryRows struct {
	rows  []GridRecord
	index map[string]int
}

func NewMemoryRows(rows []GridRecord) (*MemoryRows, error) {
	m := &MemoryRows{index: map[string]int{}}
	for _, r := range rows {
		if r.ID == "" {
			return nil, fmt.Errorf("empty row ID")
		}
		if _, ok := m.index[r.ID]; ok {
			return nil, fmt.Errorf("duplicate row ID")
		}
		copy := r
		copy.Cells = map[string]string{}
		for k, v := range r.Cells {
			copy.Cells[k] = v
		}
		m.index[r.ID] = len(m.rows)
		m.rows = append(m.rows, copy)
	}
	return m, nil
}
func (m *MemoryRows) Len() int { return len(m.rows) }
func (m *MemoryRows) IndexOf(id string) int {
	if n, ok := m.index[id]; ok {
		return n
	}
	return -1
}
func (m *MemoryRows) Row(n int) GridRecord {
	if n < 0 || n >= len(m.rows) {
		return GridRecord{}
	}
	r := m.rows[n]
	copy := map[string]string{}
	for k, v := range r.Cells {
		copy[k] = v
	}
	r.Cells = copy
	return r
}

type GridEvent struct{ Kind, RowID, ColumnID, Text, Direction string }
type Grid struct {
	columns                                                                 []GridColumn
	source                                                                  GridSource
	RowID, ColumnID, SelectedRow, SelectedColumn, SortColumn, SortDirection string
	Row, Column, Top, Left                                                  int
	WholeRow                                                                bool
	Empty                                                                   string
	options                                                                 GridOptions
	columnOptions                                                           map[string]GridColumnOptions
	cellInfo                                                                func(GridRecord, GridColumn) GridCellInfo
	selection                                                               GridRange
	rangeMode                                                               bool
	revision, appliedRevision                                               uint64
	cellPan                                                                 map[string]int
	Labels                                                                  map[string]string
	Status                                                                  GridDataStatus
	lastWidth, lastHeight                                                   int
	dragColumn                                                              string
	dragX, dragWidth                                                        int
	dragAnchor                                                              GridRange
}

func NewGrid(columns []GridColumn, source GridSource) (*Grid, error) {
	seen := map[string]bool{}
	columns = append([]GridColumn(nil), columns...)
	for i := range columns {
		c := &columns[i]
		if c.ID == "" || seen[c.ID] {
			return nil, fmt.Errorf("invalid column ID")
		}
		seen[c.ID] = true
		if c.Width <= 0 {
			c.Width = 12
		}
		c.Width = min(c.Width, 4096)
	}
	g := &Grid{columns: columns, Empty: "(empty)"}
	if source == nil {
		return nil, fmt.Errorf("row source required")
	}
	g.SetSource(source)
	return g, nil
}
func (g *Grid) Columns() []GridColumn { return append([]GridColumn(nil), g.columns...) }
func (g *Grid) SetSource(source GridSource) {
	if source == nil {
		return
	}
	g.source = source
	if at := source.IndexOf(g.RowID); at >= 0 && at < source.Len() {
		g.Row = at
	}
	if source.IndexOf(g.SelectedRow) < 0 {
		g.SelectedRow = ""
		g.SelectedColumn = ""
	}
	if _, _, _, _, ok := g.rangeBounds(); !ok {
		g.selection = GridRange{}
	}
	g.reconcile()
}
func (g *Grid) reconcile() {
	if len(g.columns) == 0 {
		g.ColumnID = ""
		g.RowID = ""
		return
	}
	g.Column = max(0, min(g.Column, len(g.columns)-1))
	g.ColumnID = g.columns[g.Column].ID
	if g.source.Len() <= 0 {
		g.Row = 0
		g.RowID = ""
		return
	}
	g.Row = max(0, min(g.Row, g.source.Len()-1))
	if g.source.Row(g.Row).State.Disabled {
		found := -1
		for i := g.Row; i < g.source.Len(); i++ {
			if !g.source.Row(i).State.Disabled {
				found = i
				break
			}
		}
		if found < 0 {
			for i := g.Row - 1; i >= 0; i-- {
				if !g.source.Row(i).State.Disabled {
					found = i
					break
				}
			}
		}
		if found < 0 {
			g.RowID = ""
			return
		}
		g.Row = found
	}
	g.RowID = g.source.Row(g.Row).ID
	g.Top = max(0, min(g.Top, g.Row))
	g.Left = max(0, min(g.Left, g.Column))
}
func (g *Grid) Focus(rowID, columnID string) bool {
	row := g.source.IndexOf(rowID)
	if row < 0 || row >= g.source.Len() || g.source.Row(row).State.Disabled || g.source.Row(row).ID != rowID {
		return false
	}
	for col, c := range g.columns {
		if c.ID == columnID {
			g.Row = row
			g.Column = col
			g.reconcile()
			return true
		}
	}
	return false
}
func (g *Grid) ResizeColumn(id string, width int) bool {
	if width < 1 || width > 4096 {
		return false
	}
	for i := range g.columns {
		if g.columns[i].ID == id {
			lo, hi := columnBounds(g.columnOptions[id])
			if width < lo || width > hi {
				return false
			}
			g.columns[i].Width = width
			opts := g.columnOptions[id]
			if opts.AutoFit || opts.Expand > 0 {
				opts.AutoFit = false
				opts.Expand = 0
				g.columnOptions[id] = opts
			}
			return true
		}
	}
	return false
}
func (g *Grid) RequestFilter(query string) GridEvent {
	g.nextRequest()
	return GridEvent{Kind: "filter", Text: query}
}
func (g *Grid) Handle(action string, height int) GridEvent {
	g.reconcile()
	if len(g.columns) == 0 {
		return GridEvent{}
	}
	if event, handled := g.extraAction(action, height); handled {
		return event
	}
	event := GridEvent{RowID: g.RowID, ColumnID: g.ColumnID}
	row := GridRecord{}
	if g.source.Len() > 0 {
		row = g.source.Row(g.Row)
	}
	old := g.Row
	if action != "sort" && g.RowID == "" {
		return GridEvent{}
	}
	switch action {
	case "copy":
		event.Kind = "copy"
		if g.WholeRow {
			values := []string{}
			for _, c := range g.columns {
				values = append(values, row.Cells[c.ID])
			}
			event.Text = strings.Join(values, "\t")
		} else {
			event.Text = row.Cells[g.ColumnID]
		}
		return event
	case "activate":
		if !g.options.DisableEditing && g.columns[g.Column].Editable && combineGridState(row.State, g.info(row, g.columns[g.Column]).State).Visual().Editable {
			event.Kind = "edit"
			event.Text = row.Cells[g.ColumnID]
		}
		return event
	case "sort":
		g.nextRequest()
		same := g.SortColumn == g.ColumnID
		g.SortColumn = g.ColumnID
		if same && g.SortDirection == "asc" {
			g.SortDirection = "desc"
		} else {
			g.SortDirection = "asc"
		}
		event.Kind = "sort"
		event.Direction = g.SortDirection
		return event
	case "select":
		g.SelectedRow = g.RowID
		g.SelectedColumn = g.ColumnID
		event.Kind = "select"
		return event
	case "row_mode":
		g.WholeRow = !g.WholeRow
		g.rangeMode = false
		return GridEvent{Kind: "mode"}
	case "left":
		g.Column = max(0, g.Column-1)
	case "right":
		g.Column = min(len(g.columns)-1, g.Column+1)
	case "up":
		g.Row = max(0, g.Row-1)
	case "down":
		g.Row = min(g.source.Len()-1, g.Row+1)
	case "first":
		g.Row = 0
	case "last":
		g.Row = g.source.Len() - 1
	case "page_up":
		g.Row = max(0, g.Row-g.pageRows(height))
	case "page_down":
		g.Row = min(g.source.Len()-1, g.Row+g.pageRows(height))
	case "widen":
		g.ResizeColumn(g.ColumnID, min(4096, g.columns[g.Column].Width+1))
	case "narrow":
		g.ResizeColumn(g.ColumnID, max(1, g.columns[g.Column].Width-1))
	default:
		return GridEvent{}
	}
	if g.Row != old {
		step := 1
		if g.Row < old {
			step = -1
		}
		for g.source.Row(g.Row).State.Disabled {
			next := g.Row + step
			if next < 0 || next >= g.source.Len() {
				g.Row = old
				break
			}
			g.Row = next
		}
	}
	g.reconcile()
	if g.lastWidth > 0 {
		geo := g.window(g.lastWidth, height).geometry
		g.Top = geo.Top
		g.Left = geo.Left
	}
	if g.rangeMode && !g.WholeRow && g.RowID != "" {
		r := g.selection
		if r.AnchorRow == "" {
			r.AnchorRow = event.RowID
			r.AnchorColumn = event.ColumnID
		}
		r.EndRow = g.RowID
		r.EndColumn = g.ColumnID
		g.SelectRange(r)
	}
	event.Kind = "focus"
	event.RowID = g.RowID
	event.ColumnID = g.ColumnID
	return event
}

type GridSpan struct {
	ID           string
	Start, Width int
}

// Click is the legacy row-ID and horizontal-coordinate mouse entry point.
//
// Deprecated: Use Pointer for local mouse coordinates, or Focus and Handle for programmatic selection/sorting.
func (g *Grid) Click(rowID, kind string, x, width, height int) GridEvent {
	return g.click(rowID, kind, x, width, height)
}

func (g *Grid) click(rowID, kind string, x, width, height int) GridEvent {
	for _, s := range g.Geometry(width, height).Columns {
		if x >= s.Start && x < s.Start+s.Width {
			if kind == "@header" {
				if g.options.DisableHeaderSort {
					return GridEvent{}
				}
				for i, c := range g.columns {
					if c.ID == s.ID {
						g.Column = i
					}
				}
				return g.Handle("sort", height)
			}
			if g.Focus(rowID, s.ID) {
				return g.Handle("select", height)
			}
		}
	}
	return GridEvent{}
}

func (g *Grid) pageRows(height int) int {
	if g.options.RowSpacing > 0 || g.options.HorizontalLines {
		return max(1, g.Geometry(max(1, g.lastWidth), height).BodyRows)
	}
	return max(1, height-2)
}
