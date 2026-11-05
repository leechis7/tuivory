package tuivory

import (
	"encoding/csv"
	"fmt"
	"io"
	"strings"
	"unicode/utf8"
)

// GridColumnLayout orders every column by stable ID. Pin is "", "left", or "right".
type GridColumnLayout struct {
	ID, Pin string
	Hidden  bool
}

// GridViewState is plain host-persisted state; no file I/O is performed.
type GridViewState struct {
	Columns                                                            []GridColumnLayout
	Widths                                                             map[string]int
	ColumnOptions                                                      map[string]GridColumnOptions
	RowID, ColumnID, TopRowID, LeftColumnID, SortColumn, SortDirection string
	Selected                                                           GridRange
	SelectedRow, SelectedColumn, Selection, Filter                     string
}
type GridValue struct {
	Text string
	Null bool
}
type GridEditOptions struct {
	Enabled, StartTyping, AllowNull bool
	// Prepare may reject a cell or supply its typed initial value. It must not mutate the grid.
	Prepare func(GridRecord, GridColumn) (GridValue, bool)
}
type GridEditSession struct {
	ID              uint64
	RowID, ColumnID string
	Original, Value GridValue
	Pending         bool
	Error           string
}
type GridChange struct {
	RowID, ColumnID string
	Value           GridValue
}
type GridPasteRequest struct {
	ID      uint64
	Changes []GridChange
}
type GridPasteOptions struct {
	MaxCells  int
	NullText  string
	ParseNull bool
}
type GridFindOptions struct {
	CaseSensitive, UseDisplay bool
	MaxCells                  int
}
type GridCellRef struct{ RowID, ColumnID string }
type gridWork struct {
	detailsEnabled bool

	editDragging bool

	rowEdited func(GridRecord) bool

	findBuffer     *TextBuffer
	dragMoveColumn string
	dragMoved      bool

	hidden        map[string]bool
	pins          map[string]string
	epoch, serial uint64
	editOptions   GridEditOptions
	edit          *GridEditSession
	buffer        *TextBuffer
	editEpoch     uint64
	move          string
	paste         *GridPasteRequest
	pasteEpoch    uint64
	query         string
	findOptions   GridFindOptions
	detail        *TextDocument
	detailTitle   string
}

// InvalidateRequests rejects late edits/pastes and data responses on host context changes.
func (g *Grid) InvalidateRequests() { g.nextRequest() }
func (g *Grid) invalidateWork() {
	g.work.epoch++
	g.work.edit = nil
	g.work.buffer = nil
	g.work.paste = nil
	g.work.detail = nil
	g.work.findBuffer = nil
}
func (g *Grid) workID() uint64 { g.work.serial++; return g.work.serial }
func (g *Grid) reconcileVisible() {
	if len(g.columns) == 0 {
		return
	}
	if g.work.hidden[g.ColumnID] {
		for i, c := range g.columns {
			if !g.work.hidden[c.ID] {
				g.Column = i
				g.ColumnID = c.ID
				return
			}
		}
		g.ColumnID = ""
	}
}
func (g *Grid) ColumnLayout() []GridColumnLayout {
	out := []GridColumnLayout{}
	for _, c := range g.columns {
		out = append(out, GridColumnLayout{ID: c.ID, Pin: g.work.pins[c.ID], Hidden: g.work.hidden[c.ID]})
	}
	return out
}

// SetColumnLayout validates atomically; at least one column must remain visible.
func (g *Grid) SetColumnLayout(layout []GridColumnLayout) error {
	if len(layout) != len(g.columns) {
		return fmt.Errorf("column layout must include all IDs")
	}
	seen := map[string]bool{}
	hidden := map[string]bool{}
	pins := map[string]string{}
	cols := []GridColumn{}
	visible := 0
	for _, v := range layout {
		i := g.columnIndex(v.ID)
		if i < 0 || seen[v.ID] || (v.Pin != "" && v.Pin != "left" && v.Pin != "right") {
			return fmt.Errorf("invalid column layout")
		}
		seen[v.ID] = true
		hidden[v.ID] = v.Hidden
		pins[v.ID] = v.Pin
		cols = append(cols, g.columns[i])
		if !v.Hidden {
			visible++
		}
	}
	if visible == 0 && len(cols) > 0 {
		return fmt.Errorf("at least one visible column required")
	}
	current := g.ColumnID
	g.invalidateWork()
	g.columns = cols
	g.work.hidden = hidden
	g.work.pins = pins
	g.Column = max(0, g.columnIndex(current))
	g.reconcile()
	return nil
}
func (g *Grid) MoveColumn(id string, at int) bool {
	l := g.ColumnLayout()
	i := g.columnIndex(id)
	if i < 0 || at < 0 || at >= len(l) {
		return false
	}
	v := l[i]
	l = append(l[:i], l[i+1:]...)
	l = append(l, GridColumnLayout{})
	copy(l[at+1:], l[at:])
	l[at] = v
	return g.SetColumnLayout(l) == nil
}
func (g *Grid) HideColumn(id string, hidden bool) bool {
	l := g.ColumnLayout()
	i := g.columnIndex(id)
	if i < 0 {
		return false
	}
	l[i].Hidden = hidden
	return g.SetColumnLayout(l) == nil
}
func (g *Grid) PinColumn(id, side string) bool {
	l := g.ColumnLayout()
	i := g.columnIndex(id)
	if i < 0 {
		return false
	}
	l[i].Pin = side
	return g.SetColumnLayout(l) == nil
}
func (g *Grid) visibleIndices() []int {
	out := []int{}
	for _, pin := range []string{"left", "", "right"} {
		for i, c := range g.columns {
			if !g.work.hidden[c.ID] && g.work.pins[c.ID] == pin {
				out = append(out, i)
			}
		}
	}
	return out
}
func (g *Grid) SaveViewState() GridViewState {
	s := GridViewState{Columns: g.ColumnLayout(), Widths: map[string]int{}, ColumnOptions: map[string]GridColumnOptions{}, RowID: g.RowID, ColumnID: g.ColumnID, SortColumn: g.SortColumn, SortDirection: g.SortDirection, Selected: g.selection, SelectedRow: g.SelectedRow, SelectedColumn: g.SelectedColumn, Selection: g.mode(), Filter: g.Status.Filter}
	for _, c := range g.columns {
		s.Widths[c.ID] = c.Width
		s.ColumnOptions[c.ID] = g.columnOptions[c.ID]
	}
	if g.Top >= 0 && g.Top < g.source.Len() {
		s.TopRowID = g.source.Row(g.Top).ID
	}
	if g.Left >= 0 && g.Left < len(g.columns) {
		s.LeftColumnID = g.columns[g.Left].ID
	}
	return s
}

// RestoreViewState requires the same column schema. Missing row IDs fall back safely.
func (g *Grid) RestoreViewState(s GridViewState) error {
	if s.Selection != "cell" && s.Selection != "row" && s.Selection != "range" {
		return fmt.Errorf("invalid selection")
	}
	if s.SortDirection != "" && s.SortDirection != "asc" && s.SortDirection != "desc" {
		return fmt.Errorf("invalid sort")
	}
	for id, w := range s.Widths {
		if g.columnIndex(id) < 0 || w < 1 || w > 4096 {
			return fmt.Errorf("invalid width")
		}
	}
	// Validate column options against a temporary grid before changing live state.
	tmp := *g
	tmp.columnOptions = map[string]GridColumnOptions{}
	for id, o := range s.ColumnOptions {
		if err := tmp.SetColumnOptions(id, o); err != nil {
			return err
		}
	}
	if err := tmp.SetColumnLayout(s.Columns); err != nil {
		return err
	}
	if s.SortColumn != "" && tmp.columnIndex(s.SortColumn) < 0 {
		return fmt.Errorf("invalid sort column")
	}
	for id, w := range s.Widths {
		lo, hi := columnBounds(tmp.columnOptions[id])
		if w < lo || w > hi {
			return fmt.Errorf("width outside bounds")
		}
	}
	g.invalidateWork()
	g.columns = tmp.columns
	g.work.hidden = tmp.work.hidden
	g.work.pins = tmp.work.pins
	g.columnOptions = tmp.columnOptions
	for i := range g.columns {
		if w, ok := s.Widths[g.columns[i].ID]; ok {
			g.columns[i].Width = w
		}
	}
	g.SortColumn = s.SortColumn
	g.SortDirection = s.SortDirection
	g.Status.Filter = s.Filter
	g.SelectedRow = s.SelectedRow
	g.SelectedColumn = s.SelectedColumn
	g.selection = s.Selected
	g.setMode(s.Selection)
	g.Focus(s.RowID, s.ColumnID)
	g.Top = max(0, g.source.IndexOf(s.TopRowID))
	g.Left = max(0, g.columnIndex(s.LeftColumnID))
	g.reconcile()
	if _, _, _, _, ok := g.rangeBounds(); !ok {
		g.selection = GridRange{}
	}
	if g.source.IndexOf(g.SelectedRow) < 0 {
		g.SelectedRow = ""
		g.SelectedColumn = ""
	}
	return nil
}
func (g *Grid) SetEditOptions(o GridEditOptions) { g.CancelEdit(); g.work.editOptions = o }
func (g *Grid) editable(row GridRecord, c GridColumn) bool {
	return !g.options.DisableEditing && !g.work.hidden[c.ID] && c.Editable && combineGridState(row.State, g.info(row, c).State).Visual().Editable
}
func (g *Grid) BeginEdit(first string) bool {
	if !g.work.editOptions.Enabled || g.work.edit != nil || g.work.paste != nil || g.RowID == "" || g.ColumnID == "" {
		return false
	}
	row := g.source.Row(g.Row)
	c := g.columns[g.Column]
	if !g.editable(row, c) {
		return false
	}
	info := g.info(row, c)
	v := GridValue{Text: row.Cells[c.ID], Null: info.Null}
	if prepare := g.work.editOptions.Prepare; prepare != nil {
		var ok bool
		v, ok = prepare(row, c)
		if !ok {
			return false
		}
	}
	g.dragColumn = ""
	g.dragAnchor = GridRange{}
	g.work.dragMoveColumn = ""
	g.work.edit = &GridEditSession{ID: g.workID(), RowID: row.ID, ColumnID: c.ID, Original: v, Value: v}
	g.work.editEpoch = g.work.epoch
	g.work.buffer = NewTextBuffer(v.Text)
	g.work.buffer.SingleLine = true
	if first != "" {
		g.work.buffer.Select(0, len(clusters(v.Text)))
		g.work.buffer.Handle("insert", first)
		g.work.edit.Value = GridValue{Text: g.work.buffer.Text()}
	}
	return true
}
func (g *Grid) EditSession() (GridEditSession, bool) {
	if g.work.edit == nil {
		return GridEditSession{}, false
	}
	return *g.work.edit, true
}
func (g *Grid) CancelEdit() {
	g.work.edit = nil
	g.work.buffer = nil
	g.work.move = ""
	g.work.editDragging = false
}

// EditInput consumes only internal editor actions. Submit/next/previous wait for ResolveEdit.
func (g *Grid) EditInput(action, text string) GridEvent {
	e := g.work.edit
	if e == nil {
		return GridEvent{}
	}
	i, c := g.source.IndexOf(e.RowID), g.columnIndex(e.ColumnID)
	if i < 0 || i >= g.source.Len() || c < 0 || g.source.Row(i).ID != e.RowID || (!g.editable(g.source.Row(i), g.columns[c]) || !g.prepared(g.source.Row(i), g.columns[c])) {
		g.CancelEdit()
		return GridEvent{Kind: "edit_cancel"}
	}
	out := GridEvent{RowID: e.RowID, ColumnID: e.ColumnID}
	if action == "cancel" {
		g.CancelEdit()
		out.Kind = "edit_cancel"
		return out
	}
	if e.Pending {
		return GridEvent{}
	}
	if action == "submit" || action == "next" || action == "previous" {
		e.ID = g.workID()
		e.Pending = true
		e.Error = ""
		g.work.move = action
		out.Kind = "edit_submit"
		out.Text = e.Value.Text
		return out
	}
	if action == "null" {
		if g.work.editOptions.AllowNull {
			e.Value.Null = !e.Value.Null
		}
		return GridEvent{Kind: "edit_change", RowID: e.RowID, ColumnID: e.ColumnID}
	}
	v := g.work.buffer.Handle(action, text)
	if v.Kind == "copy" || v.Kind == "cut" {
		return GridEvent{Kind: v.Kind, Text: v.Text, RowID: e.RowID, ColumnID: e.ColumnID}
	}
	e.Value.Text = g.work.buffer.Text()
	if action == "insert" || action == "paste" || action == "backspace" || action == "delete" {
		e.Value.Null = false
		e.Error = ""
	}
	out.Kind = "edit_change"
	return out
}

// ResolveEdit accepts only the active pending request. A source is applied only on success.
func (g *Grid) ResolveEdit(id uint64, message string, source GridSource) bool {
	e := g.work.edit
	if e == nil || !e.Pending || e.ID != id || g.work.editEpoch != g.work.epoch {
		return false
	}
	i := g.source.IndexOf(e.RowID)
	c := g.columnIndex(e.ColumnID)
	if i < 0 || i >= g.source.Len() || c < 0 || g.source.Row(i).ID != e.RowID || (!g.editable(g.source.Row(i), g.columns[c]) || !g.prepared(g.source.Row(i), g.columns[c])) {
		g.CancelEdit()
		return false
	}
	if message != "" {
		e.Pending = false
		e.Error = message
		return true
	}
	row, col, move := e.RowID, e.ColumnID, g.work.move
	g.CancelEdit()
	if source != nil {
		g.SetSource(source)
	}
	if !g.Focus(row, col) {
		return true
	}
	if move == "next" || move == "previous" {
		if g.MoveEditable(move == "previous") {
			g.BeginEdit("")
		}
	}
	return true
}
func (g *Grid) prepared(r GridRecord, c GridColumn) bool {
	if p := g.work.editOptions.Prepare; p != nil {
		_, ok := p(r, c)
		return ok
	}
	return true
}
func (g *Grid) MoveEditable(previous bool) bool {
	cols := g.visibleIndices()
	ci := -1
	for i, c := range cols {
		if c == g.Column {
			ci = i
		}
	}
	if ci < 0 || len(cols) == 0 {
		return false
	}
	step := 1
	if previous {
		step = -1
	}
	start := g.Row*len(cols) + ci
	limit := g.source.Len() * len(cols)
	for at := start + step; at >= 0 && at < limit; at += step {
		r, c := at/len(cols), cols[at%len(cols)]
		if g.editable(g.source.Row(r), g.columns[c]) && g.prepared(g.source.Row(r), g.columns[c]) {
			return g.Focus(g.source.Row(r).ID, g.columns[c].ID)
		}
	}
	return false
}

// RequestPaste parses quoted TSV, validates the whole batch and never mutates source values.
func (g *Grid) RequestPaste(text string, o GridPasteOptions) (GridPasteRequest, error) {
	fail := func() (GridPasteRequest, error) {
		return GridPasteRequest{}, fmt.Errorf("paste rejected: bounds, limits or non-editable cell")
	}
	limit := o.MaxCells
	if limit == 0 {
		limit = 10000
	}
	if limit < 1 || limit > 1000000 || !utf8.ValidString(text) || len(text) > 16*1024*1024 || g.work.edit != nil || g.work.paste != nil || g.RowID == "" {
		return fail()
	}
	r := csv.NewReader(strings.NewReader(text))
	r.Comma = '\t'
	r.FieldsPerRecord = -1
	r.ReuseRecord = true
	cols := g.visibleIndices()
	start := -1
	for i, c := range cols {
		if c == g.Column {
			start = i
		}
	}
	if start < 0 {
		return fail()
	}
	req := GridPasteRequest{}
	width := -1
	ri := 0
	for {
		values, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return GridPasteRequest{}, err
		}
		if width < 0 {
			width = len(values)
		}
		if len(values) != width || g.Row+ri >= g.source.Len() || start+width > len(cols) || len(req.Changes)+width > limit {
			return fail()
		}
		row := g.source.Row(g.Row + ri)
		if row.ID == "" || g.source.IndexOf(row.ID) != g.Row+ri {
			return fail()
		}
		for j, value := range values {
			c := g.columns[cols[start+j]]
			if !g.editable(row, c) || !g.prepared(row, c) {
				return fail()
			}
			req.Changes = append(req.Changes, GridChange{RowID: row.ID, ColumnID: c.ID, Value: GridValue{Text: value, Null: o.ParseNull && value == o.NullText}})
		}
		ri++
	}
	if len(req.Changes) == 0 {
		return fail()
	}
	req.ID = g.workID()
	g.work.paste = &req
	g.work.pasteEpoch = g.work.epoch
	copyReq := req
	copyReq.Changes = append([]GridChange(nil), req.Changes...)
	return copyReq, nil
}
func (g *Grid) PendingPaste() (GridPasteRequest, bool) {
	if g.work.paste == nil {
		return GridPasteRequest{}, false
	}
	r := *g.work.paste
	r.Changes = append([]GridChange(nil), r.Changes...)
	return r, true
}
func (g *Grid) ResolvePaste(id uint64, source GridSource) bool {
	p := g.work.paste
	if p == nil || p.ID != id || g.work.pasteEpoch != g.work.epoch {
		return false
	}
	for _, v := range p.Changes {
		i, c := g.source.IndexOf(v.RowID), g.columnIndex(v.ColumnID)
		if i < 0 || i >= g.source.Len() || c < 0 || g.source.Row(i).ID != v.RowID || (!g.editable(g.source.Row(i), g.columns[c]) || !g.prepared(g.source.Row(i), g.columns[c])) {
			g.work.paste = nil
			return false
		}
	}
	g.work.paste = nil
	if source != nil {
		g.SetSource(source)
	}
	return true
}
func (g *Grid) CancelPaste()                            { g.work.paste = nil }
func (g *Grid) SetFind(query string, o GridFindOptions) { g.work.query = query; g.work.findOptions = o }
func (g *Grid) matches(row GridRecord, col GridColumn) bool {
	q := g.work.query
	if q == "" {
		return false
	}
	v := row.Cells[col.ID]
	if g.work.findOptions.UseDisplay {
		i := g.info(row, col)
		if i.HasDisplay {
			v = i.Display
		} else if i.Null {
			v = g.label("null", "NULL")
		}
	}
	if !g.work.findOptions.CaseSensitive {
		q = strings.ToLower(q)
		v = strings.ToLower(v)
	}
	return strings.Contains(v, q)
}

// FindNext is bounded and scans only the supplied (loaded) source, wrapping once.
func (g *Grid) FindNext(previous bool) (GridCellRef, bool) {
	cols := g.visibleIndices()
	if len(cols) == 0 || g.work.query == "" {
		return GridCellRef{}, false
	}
	limit := g.work.findOptions.MaxCells
	if limit == 0 {
		limit = 100000
	}
	if limit < 1 {
		return GridCellRef{}, false
	}
	ci := 0
	for i, c := range cols {
		if c == g.Column {
			ci = i
		}
	}
	n := g.source.Len() * len(cols)
	if n == 0 {
		return GridCellRef{}, false
	}
	start := g.Row*len(cols) + ci
	step := 1
	if previous {
		step = -1
	}
	for i := 1; i <= min(n, limit); i++ {
		at := ((start+step*i)%n + n) % n
		r := g.source.Row(at / len(cols))
		c := g.columns[cols[at%len(cols)]]
		if !r.State.Disabled && g.matches(r, c) {
			g.Focus(r.ID, c.ID)
			return GridCellRef{r.ID, c.ID}, true
		}
	}
	return GridCellRef{}, false
}
func (g *Grid) RequestSearch(query string) GridEvent {
	g.nextRequest()
	return GridEvent{Kind: "search_request", Text: query}
}

// SetDetailsEnabled opts into built-in handling of the existing details request.
func (g *Grid) SetDetailsEnabled(enabled bool) {
	g.work.detailsEnabled = enabled
	if !enabled {
		g.CloseDetails()
	}
}
func (g *Grid) OpenDetails() bool {
	if g.RowID == "" || g.ColumnID == "" {
		return false
	}
	r := g.source.Row(g.Row)
	g.work.detail = NewTextView(r.Cells[g.ColumnID])
	g.work.detail.Buffer.State.ReadOnly = true
	g.work.detailTitle = g.columns[g.Column].Label
	return true
}
func (g *Grid) CloseDetails() { g.work.detail = nil }
func (g *Grid) workAction(action string, height int) (GridEvent, bool) {
	if g.work.detail != nil {
		if action == "cancel" {
			g.CloseDetails()
		} else {
			g.work.detail.Handle(action, "")
		}
		return GridEvent{}, true
	}
	if g.work.edit != nil {
		if action == "activate" {
			action = "submit"
		}
		return g.EditInput(action, ""), true
	}
	if action == "activate" && g.work.editOptions.Enabled {
		if g.BeginEdit("") {
			return GridEvent{Kind: "edit_begin", RowID: g.RowID, ColumnID: g.ColumnID}, true
		}
		return GridEvent{}, true
	}
	switch action {
	case "details":
		if g.RowID == "" {
			return GridEvent{}, true
		}
		if g.work.detailsEnabled {
			g.OpenDetails()
		}
		value := ""
		if g.RowID != "" {
			value = g.source.Row(g.Row).Cells[g.ColumnID]
		}
		return GridEvent{Kind: "details", RowID: g.RowID, ColumnID: g.ColumnID, Text: value}, true
	case "find_next", "find_previous":
		r, ok := g.FindNext(action == "find_previous")
		if ok {
			return GridEvent{Kind: "find", RowID: r.RowID, ColumnID: r.ColumnID}, true
		}
		return GridEvent{}, true
	case "next", "previous":
		g.MoveEditable(action == "previous")
		return GridEvent{Kind: "focus", RowID: g.RowID, ColumnID: g.ColumnID}, true
	case "hide_column":
		g.HideColumn(g.ColumnID, true)
		return GridEvent{Kind: "columns"}, true
	case "pin_column":
		side := "left"
		if g.work.pins[g.ColumnID] != "" {
			side = ""
		}
		g.PinColumn(g.ColumnID, side)
		return GridEvent{Kind: "columns"}, true
	case "column_previous", "column_next":
		at := g.Column - 1
		if action == "column_next" {
			at = g.Column + 1
		}
		g.MoveColumn(g.ColumnID, at)
		return GridEvent{Kind: "columns"}, true
	case "left", "right":
		cols := g.visibleIndices()
		for i, c := range cols {
			if c == g.Column {
				j := i - 1
				if action == "right" {
					j = i + 1
				}
				if j >= 0 && j < len(cols) {
					g.Column = cols[j]
					g.ColumnID = g.columns[g.Column].ID
				}
				return GridEvent{Kind: "focus", RowID: g.RowID, ColumnID: g.ColumnID}, true
			}
		}
	}
	return GridEvent{}, false
}

func (g *Grid) cellState(row GridRecord, info GridCellInfo) ControlState {
	s := row.State
	s.Edited = false
	return combineGridState(s, info.State)
}
func (g *Grid) rowEdited(row GridRecord) bool {
	if g.work.rowEdited != nil {
		return g.work.rowEdited(row)
	}
	return row.State.Edited
}

// SetRowEdited supplies an independent aggregate gutter marker without coloring cells.
func (g *Grid) SetRowEdited(fn func(GridRecord) bool) { g.work.rowEdited = fn }
func (g *Grid) columnSpans(width, gutter int, widths []int) (int, []GridSpan) {
	visible := g.visibleIndices()
	left, right, normal := []int{}, []int{}, []int{}
	for _, c := range visible {
		switch g.work.pins[g.columns[c].ID] {
		case "left":
			left = append(left, c)
		case "right":
			right = append(right, c)
		default:
			normal = append(normal, c)
		}
	}
	physical := func(c int) int { return widths[c] + 2*g.options.Padding + 1 }
	capacity := max(0, width-gutter)
	pinned := 0
	for _, c := range append(append([]int{}, left...), right...) {
		pinned += physical(c)
	}
	// Keep at least one usable ordinary cell when pinned columns fill a narrow view.
	budget := min(capacity, pinned)
	if len(normal) > 0 {
		budget = min(budget, max(0, capacity-min(8, capacity)))
	}
	start := 0
	for i, c := range normal {
		if c <= g.Left {
			start = i
		}
	}
	target := -1
	for i, c := range normal {
		if c == g.Column {
			target = i
		}
	}
	if target >= 0 {
		if start > target {
			start = target
		}
		for start < target {
			used := 0
			for i := start; i <= target; i++ {
				used += physical(normal[i])
			}
			if used <= capacity-budget {
				break
			}
			start++
		}
	}
	if len(left) > 0 {
		for i, c := range left {
			if c == g.Column {
				left = left[i:]
				break
			}
		}
	}
	if len(right) > 0 {
		for i, c := range right {
			if c == g.Column {
				right = right[i:]
				break
			}
		}
	}
	spans := []GridSpan{}
	x := gutter
	remaining := budget
	add := func(c int, limit int) {
		if x >= limit {
			return
		}
		w := min(limit-x, widths[c]+2*g.options.Padding)
		if w <= 0 {
			return
		}
		spans = append(spans, GridSpan{g.columns[c].ID, x, w})
		x += w + 1
	}
	// Split the pin budget across both sides; clipped cells never overlap.
	leftBudget := remaining
	if len(right) > 0 && len(left) > 0 {
		leftBudget = (budget + 1) / 2
	}
	leftEnd := min(width, gutter+leftBudget)
	for _, c := range left {
		add(c, leftEnd)
	}
	remaining -= max(0, x-gutter)
	remaining = max(0, remaining)
	rightWidth := 0
	for _, c := range right {
		rightWidth += physical(c)
	}
	rightWidth = min(remaining, rightWidth)
	rightStart := max(x, width-rightWidth)
	end := start
	used := 0
	for end < len(normal) && used < rightStart-x {
		used += physical(normal[end])
		end++
	}
	extra := max(0, rightStart-x-used)
	weight := 0
	for i := start; i < end; i++ {
		weight += g.columnOptions[g.columns[normal[i]].ID].Expand
	}
	if weight > 0 {
		for i := start; i < end; i++ {
			c := normal[i]
			o := g.columnOptions[g.columns[c].ID]
			_, hi := columnBounds(o)
			widths[c] = min(hi, widths[c]+extra*o.Expand/weight)
		}
	}
	for i := start; i < len(normal); i++ {
		add(normal[i], rightStart)
	}
	x = rightStart
	for _, c := range right {
		add(c, width)
	}
	scroll := g.Left
	if start < len(normal) {
		scroll = normal[start]
	}
	return scroll, spans
}
func (g *Grid) detailLayout(width, height int) []ComponentLine {
	if width < 4 || height < 4 {
		return g.work.detail.Layout(width, height)
	}
	w, h := width-2, height-2
	body := g.work.detail.Layout(max(1, w-2), max(1, h-2))
	rows := []ComponentLine{}
	top, bottom, side := "═", "═", "║"
	tl, tr, bl, br := "╔", "╗", "╚", "╝"
	if g.options.ASCII {
		top = "-"
		bottom = "-"
		side = "|"
		tl = "+"
		tr = "+"
		bl = "+"
		br = "+"
	}
	rows = append(rows, ComponentLine{Role: "grid.base"})
	title := CellText(" "+g.work.detailTitle+" ", max(0, w-2))
	title += strings.Repeat(top, max(0, w-2-gridTextWidth(title)))
	rows = append(rows, ComponentLine{Role: "grid.base", Spans: []ComponentSpan{{Start: 1, Width: w, Text: tl + title + tr, Role: "header"}}})
	for i := 0; i < h-2; i++ {
		l := ComponentLine{Role: "grid.base"}
		if i < len(body) {
			l = body[i]
			l.Text = ""
			for j := range l.Spans {
				l.Spans[j].Start += 2
			}
			l.Spans = append([]ComponentSpan{{Start: 2, Width: max(0, w-2), Text: body[i].Text, Role: body[i].Role}}, l.Spans...)
		}
		l.Spans = append(l.Spans, ComponentSpan{Start: 1, Width: 1, Text: side, Role: "header"}, ComponentSpan{Start: width - 2, Width: 1, Text: side, Role: "header"})
		rows = append(rows, l)
	}
	rows = append(rows, ComponentLine{Role: "grid.base", Spans: []ComponentSpan{{Start: 1, Width: w, Text: bl + strings.Repeat(bottom, max(0, w-2)) + br, Role: "header"}}})
	return rows
}

func (g *Grid) editPoint(action string, x, y, width, height int, extend bool) GridEvent {
	e := g.work.edit
	if e == nil {
		return GridEvent{}
	}
	if action == "up" {
		g.work.editDragging = false
		return GridEvent{}
	}
	if e.Pending {
		return GridEvent{}
	}
	geo := g.Geometry(width, height)
	row := g.source.IndexOf(e.RowID)
	at := geo.HeaderRows + (row-geo.Top)*geo.Stride
	for _, s := range geo.Columns {
		if s.ID != e.ColumnID || y != at || x < s.Start || x >= s.Start+s.Width {
			continue
		}
		if action != "down" && action != "click" && action != "double" && !(action == "move" && g.work.editDragging) {
			return GridEvent{}
		}
		b := g.work.buffer
		before := strings.Join(clusters(b.Text())[:b.Cursor], "")
		tail := tailCells(before, max(0, s.Width-2*g.options.Padding-1))
		start := b.Cursor - len(clusters(tail))
		extra := 0
		if g.info(g.source.Row(row), g.columns[g.columnIndex(s.ID)]).State.Edited {
			extra = 2
		}
		offset := max(0, x-s.Start-g.options.Padding-extra)
		caret := gridTextWidth(strings.Join(clusters(b.Text())[start:b.Cursor], ""))
		if offset > caret {
			offset--
		}
		pos := start
		used := 0
		for _, c := range clusters(b.Text())[start:] {
			w := gridTextWidth(c)
			if used+w > offset {
				break
			}
			used += w
			pos++
		}
		anchor := pos
		if extend || action == "move" {
			anchor = b.Anchor
		}
		b.Select(anchor, pos)
		g.work.editDragging = action != "click" && action != "double"
		return GridEvent{Kind: "edit_select", RowID: e.RowID, ColumnID: e.ColumnID}
	}
	if action == "down" || action == "click" || action == "double" {
		return GridEvent{Kind: "edit_blocked"}
	}
	return GridEvent{}
}
