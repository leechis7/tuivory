package catalog

import ui "github.com/leechis7/tuivory/go"

// This source is deliberately host-owned: approving a request updates synthetic data only.
type editableDemoRows struct {
	base    ui.GridSource
	changes map[ui.GridCellRef]ui.GridValue
}

func newEditableRows(base ui.GridSource) *editableDemoRows {
	return &editableDemoRows{base: base, changes: map[ui.GridCellRef]ui.GridValue{}}
}
func (s *editableDemoRows) Len() int              { return s.base.Len() }
func (s *editableDemoRows) IndexOf(id string) int { return s.base.IndexOf(id) }
func (s *editableDemoRows) Row(i int) ui.GridRecord {
	r := s.base.Row(i)
	cells := map[string]string{}
	for k, v := range r.Cells {
		cells[k] = v
	}
	r.Cells = cells
	for ref, v := range s.changes {
		if ref.RowID == r.ID {
			r.Cells[ref.ColumnID] = v.Text
		}
	}
	return r
}
func respondGrid(g *ui.Grid, s *editableDemoRows, e ui.GridEvent) {
	if e.Kind == "edit_submit" {
		v, ok := g.EditSession()
		if !ok {
			return
		}
		if v.Value.Text == "reject" || v.Value.Text == "거절" {
			g.ResolveEdit(v.ID, g.Labels["rejected"], nil)
			return
		}
		s.changes[ui.GridCellRef{RowID: v.RowID, ColumnID: v.ColumnID}] = v.Value
		g.ResolveEdit(v.ID, "", nil)
	}
	if e.Kind == "paste_request" {
		p, ok := g.PendingPaste()
		if !ok {
			return
		}
		for _, v := range p.Changes {
			s.changes[ui.GridCellRef{RowID: v.RowID, ColumnID: v.ColumnID}] = v.Value
		}
		g.ResolvePaste(p.ID, nil)
	}
}
