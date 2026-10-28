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
			g.columns[i].Width = width
			return true
		}
	}
	return false
}
func (g *Grid) RequestFilter(query string) GridEvent { return GridEvent{Kind: "filter", Text: query} }
func (g *Grid) Handle(action string, height int) GridEvent {
	g.reconcile()
	if len(g.columns) == 0 {
		return GridEvent{}
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
		if g.columns[g.Column].Editable && row.State.Visual().Editable {
			event.Kind = "edit"
			event.Text = row.Cells[g.ColumnID]
		}
		return event
	case "sort":
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
		g.Row = max(0, g.Row-max(1, height-2))
	case "page_down":
		g.Row = min(g.source.Len()-1, g.Row+max(1, height-2))
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
	event.Kind = "focus"
	event.RowID = g.RowID
	event.ColumnID = g.ColumnID
	return event
}

type GridSpan struct {
	ID           string
	Start, Width int
}

func (g *Grid) spans(width int) []GridSpan {
	left := min(g.Left, g.Column)
	capacity := max(0, width-3)
	for left < g.Column {
		used := 0
		for c := left; c <= g.Column; c++ {
			used += g.columns[c].Width + 1
		}
		if used <= capacity {
			break
		}
		left++
	}
	out := []GridSpan{}
	x := 3
	for col := left; col < len(g.columns) && x < width; col++ {
		w := min(g.columns[col].Width, width-x)
		out = append(out, GridSpan{ID: g.columns[col].ID, Start: x, Width: w})
		x += w + 1
	}
	return out
}
func (g *Grid) Layout(width, height int) []ComponentLine {
	g.reconcile()
	if width <= 0 || height <= 0 || len(g.columns) == 0 {
		return nil
	}
	spans := g.spans(width)
	header := ComponentLine{Role: "header", Value: "@header"}
	for _, s := range spans {
		label := ""
		for _, c := range g.columns {
			if c.ID == s.ID {
				label = c.Label
			}
		}
		if s.ID == g.SortColumn {
			label += " " + g.SortDirection
		}
		header.Spans = append(header.Spans, ComponentSpan{Start: s.Start, Width: s.Width, Text: func() string {
			if s.ID == g.ColumnID {
				return "> " + label
			}
			return label
		}(), Role: "header", Focused: s.ID == g.ColumnID})
	}
	out := []ComponentLine{header}
	if g.source.Len() == 0 {
		return append(out, ComponentLine{Text: CellText(g.Empty, width), Role: "hint"})[:min(height, 2)]
	}
	top := min(g.Top, g.Row)
	if g.Row >= top+max(1, height-1) {
		top = g.Row - max(1, height-1) + 1
	}
	top = max(0, min(top, max(0, g.source.Len()-max(1, height-1))))
	for n := top; n < g.source.Len() && len(out) < height; n++ {
		r := g.source.Row(n)
		v := r.State.Visual()
		marker := "  "
		if r.ID == g.RowID {
			marker = "> "
		}
		line := ComponentLine{ID: r.ID, Text: marker + v.Markers, Role: v.Role, Focused: r.ID == g.RowID}
		for _, s := range spans {
			state := r.State
			if r.ID == g.SelectedRow && (g.WholeRow || s.ID == g.SelectedColumn) {
				state.Selected = true
			}
			role := state.Visual().Role
			line.Spans = append(line.Spans, ComponentSpan{Start: s.Start, Width: s.Width, Text: func() string {
				if state.Selected {
					return "> " + r.Cells[s.ID]
				}
				return r.Cells[s.ID]
			}(), Role: role, Focused: r.ID == g.RowID && s.ID == g.ColumnID})
		}
		out = append(out, line)
	}
	return out
}
func (g *Grid) Click(rowID, kind string, x, width, height int) GridEvent {
	for _, s := range g.spans(width) {
		if x >= s.Start && x < s.Start+s.Width {
			if kind == "@header" {
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
