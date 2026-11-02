package tuivory

import (
	"fmt"
	"github.com/gdamore/tcell/v2"
	"hash/fnv"
	"slices"
	"sort"
)

// DropPosition is relative to a stable target ID; inside appends a last child.
type DropPosition string

const (
	DropBefore DropPosition = "before"
	DropAfter  DropPosition = "after"
	DropInside DropPosition = "inside"
)

// DropRequest never changes source data. Hosts approve it before ApplyDrop.
// Revision rejects requests against replaced data, even if IDs still exist.
type DropRequest struct {
	SourceID, TargetID string
	Position           DropPosition
	Revision           uint64
}

// DragOptions controls local interaction. Zero Threshold means two cells.
// Locked blocks source and target IDs (including host-disabled tree nodes).
// AutoScroll advances one item per edge move; HoverExpand is opt-in/immediate.
type DragOptions struct {
	Threshold               int
	AutoScroll, HoverExpand bool
	Locked                  []string
}
type DragPointer struct {
	Action              string
	X, Y, Width, Height int
}
type DragMove string

const (
	DragPrevious DragMove = "previous"
	DragNext     DragMove = "next"
	DragInside   DragMove = "inside"
	DragOutside  DragMove = "outside"
)

// DragState owns only transient preview state. Cancel leaves application data,
// selection, focus, expansion and scroll untouched. Result is drop/reject/cancel/stale.
type DragState struct {
	Phase, Result       string
	SourceID, TargetID  string
	Position            DropPosition
	Allowed             bool
	Reason              string
	revision            uint64
	stateRevision       uint64
	x, y, width, height int
	first, scroll       int
	expanded            map[string]bool
	request             DropRequest
	renderKey           string
}

func (d *DragState) Captured() bool { return d != nil && (d.Phase == "armed" || d.Phase == "dragging") }
func (d *DragState) Cancel() {
	if d != nil {
		key := d.renderKey
		*d = DragState{Result: "cancel", renderKey: key}
	}
}

// RenderKey cancels a captured gesture if the host moves/resizes/restyles the
// component. Call every frame; Go views and Rust widgets do this automatically.
func (d *DragState) RenderKey(key string) {
	if d.Captured() && d.renderKey != "" && d.renderKey != key {
		d.Cancel()
		d.Result = "stale"
	}
	d.renderKey = key
}
func dragRevision(parts ...string) uint64 {
	h := fnv.New64a()
	for _, s := range parts {
		fmt.Fprintf(h, "%d:%s", len(s), s)
	}
	return h.Sum64()
}
func (t *Tabs) dragRevision() uint64 {
	var p []string
	for _, i := range t.items {
		p = append(p, i.ID, i.Title, fmt.Sprint(i.Edited), fmt.Sprint(i.Closable), fmt.Sprint(i.Disabled))
	}
	return dragRevision(p...)
}
func (t *Tree) dragRevision() uint64 {
	var p []string
	for _, r := range t.rows {
		n := r.Node
		count := ""
		if n.Count != nil {
			count = fmt.Sprint(*n.Count)
		}
		p = append(p, n.ID, n.Parent, n.Name, n.Secondary, n.Icon, n.ASCIIIcon, count, fmt.Sprint(n.Branch))
	}
	return dragRevision(p...)
}
func dragLocked(o DragOptions, id string) bool { return slices.Contains(o.Locked, id) }
func (d *DragState) begin(id string, revision uint64, p DragPointer) {
	key := d.renderKey
	*d = DragState{Phase: "armed", SourceID: id, revision: revision, x: p.X, y: p.Y, width: p.Width, height: p.Height, renderKey: key}
}
func (d *DragState) prepare(rev uint64, p DragPointer, o DragOptions) bool {
	if !d.Captured() {
		return false
	}
	if d.revision != rev || p.Width != d.width || p.Height != d.height {
		d.Cancel()
		d.Result = "stale"
		return false
	}
	if p.Action == "cancel" {
		d.Cancel()
		return false
	}
	threshold := o.Threshold
	if threshold <= 0 {
		threshold = 2
	}
	if max(dragDistance(p.X, d.x), dragDistance(p.Y, d.y)) >= uint(threshold) {
		d.Phase = "dragging"
	}
	return true
}
func dragDistance(a, b int) uint {
	if a >= b {
		return uint(a) - uint(b)
	}
	return uint(b) - uint(a)
}
func tabDragStateRevision(s *TabState) uint64 {
	return dragRevision(s.Active, s.Focused, fmt.Sprint(s.First))
}
func treeDragStateRevision(s *TreeState) uint64 {
	p := []string{s.Selected, fmt.Sprint(s.Scroll), fmt.Sprint(s.Horizontal)}
	var keys []string
	for k, v := range s.Expanded {
		if v {
			keys = append(keys, k)
		}
	}
	sort.Strings(keys)
	return dragRevision(append(p, keys...)...)
}

func dragMarker(d *DragState, ascii, tree bool) string {
	if !d.Allowed {
		return "!"
	}
	if !tree {
		if ascii {
			return "|"
		}
		return "│"
	}
	if ascii {
		switch d.Position {
		case DropBefore:
			return "^"
		case DropInside:
			return "+"
		default:
			return "v"
		}
	}
	switch d.Position {
	case DropBefore:
		return "↑"
	case DropInside:
		return "↳"
	default:
		return "↓"
	}
}
func dragFeedbackStyle(p Palette, d *DragState) tcell.Style {
	role := "info"
	if !d.Allowed {
		role = "error"
	}
	st, err := TextOnSurface(p, role, "surface")
	if err != nil {
		st = p["body"].Style()
	}
	return st.Bold(true).Underline(true)
}

func dragRenderKey(p Palette, x, y, w, h int, ascii bool) string {
	keys := make([]string, 0, len(p))
	for key := range p {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	hash := fnv.New64a()
	fmt.Fprintf(hash, "%d,%d,%d,%d/%t", x, y, w, h, ascii)
	for _, key := range keys {
		fg, bg, attrs := p[key].Style().Decompose()
		fmt.Fprintf(hash, "/%s:%d:%d:%d", key, uint64(fg), uint64(bg), uint64(attrs))
	}
	return fmt.Sprint(hash.Sum64())
}
func (d *DragState) finish(p DragPointer) *DropRequest {
	if p.Action != "up" {
		return nil
	}
	request := d.request
	allowed := d.Phase == "dragging" && d.Allowed
	active := d.Phase == "dragging"
	d.Cancel()
	d.Result = ""
	if allowed {
		d.Result = "drop"
		return &request
	}
	if active {
		d.Result = "reject"
	}
	return nil
}
func (d *DragState) preview(r DropRequest, err error) {
	d.TargetID = r.TargetID
	d.Position = r.Position
	d.request = r
	d.Allowed = err == nil
	d.Reason = ""
	if err != nil {
		d.Reason = err.Error()
	}
}
func (t *Tabs) Items() []TabItem { return append([]TabItem(nil), t.items...) }
func (t *Tree) Nodes() []TreeNode {
	out := make([]TreeNode, len(t.rows))
	for i, r := range t.rows {
		out[i] = r.Node
		if r.Node.Count != nil {
			count := *r.Node.Count
			out[i].Count = &count
		}
	}
	return out
}

func (t *Tabs) RequestDrop(source, target string, pos DropPosition, o DragOptions, allow func(DropRequest) bool) (DropRequest, error) {
	r := DropRequest{source, target, pos, t.dragRevision()}
	if dragLocked(o, source) || dragLocked(o, target) {
		return r, fmt.Errorf("locked")
	}
	_, err := t.ApplyDrop(r)
	if err == nil && allow != nil && !allow(r) {
		err = fmt.Errorf("policy")
	}
	return r, err
}

// ApplyDrop returns a new model after host approval. The original stays intact.
func (t *Tabs) ApplyDrop(r DropRequest) (*Tabs, error) {
	if r.Revision != t.dragRevision() {
		return nil, fmt.Errorf("stale")
	}
	if r.SourceID == r.TargetID {
		return nil, fmt.Errorf("self")
	}
	if r.Position != DropBefore && r.Position != DropAfter {
		return nil, fmt.Errorf("position")
	}
	source, target := -1, -1
	for i, item := range t.items {
		if item.ID == r.SourceID {
			source = i
		}
		if item.ID == r.TargetID {
			target = i
		}
	}
	if source < 0 || target < 0 {
		return nil, fmt.Errorf("missing")
	}
	if t.items[source].Disabled || t.items[target].Disabled {
		return nil, fmt.Errorf("disabled")
	}
	items := t.Items()
	item := items[source]
	items = slices.Delete(items, source, source+1)
	if source < target {
		target--
	}
	if r.Position == DropAfter {
		target++
	}
	if source == target {
		return nil, fmt.Errorf("unchanged")
	}
	items = slices.Insert(items, target, item)
	return NewTabs(items)
}
func (t *Tabs) KeyboardDrop(s *TabState, move DragMove, o DragOptions, allow func(DropRequest) bool) (DropRequest, error) {
	for i, item := range t.items {
		if item.ID != s.Focused {
			continue
		}
		target, pos := i-1, DropBefore
		if move == DragNext {
			target, pos = i+1, DropAfter
		} else if move != DragPrevious {
			return DropRequest{}, fmt.Errorf("position")
		}
		if target < 0 || target >= len(t.items) {
			break
		}
		return t.RequestDrop(item.ID, t.items[target].ID, pos, o, allow)
	}
	return DropRequest{}, fmt.Errorf("missing")
}

// DragLayout uses an independent preview viewport, retaining actual focus/scroll.
func (t *Tabs) DragLayout(s *TabState, d *DragState, width int) TabLayout {
	if !d.Captured() {
		return t.Layout(s, width)
	}
	if d.revision != t.dragRevision() || width != d.width || d.stateRevision != tabDragStateRevision(s) {
		d.Cancel()
		d.Result = "stale"
		return t.Layout(s, width)
	}
	first := min(max(0, d.first), max(0, len(t.items)-1))
	out := TabLayout{Previous: first > 0}
	if width <= 2 {
		return out
	}
	x := 1
	for i := first; i < len(t.items) && x < width-1; i++ {
		item := t.items[i]
		w := min(width-1-x, min(24, max(6, TaggedStringWidth(cleanTreeText(item.Title))+5)))
		out.Cells = append(out.Cells, TabCell{item.ID, tabText(item, w, item.ID == s.Active, item.ID == s.Focused), x, w, item.ID == s.Active, item.ID == s.Focused, item.Disabled})
		x += w
	}
	out.Next = first+len(out.Cells) < len(t.items)
	return out
}

// Drag accepts down/move/up/cancel in inner-viewport cell coordinates. Capture
// all move/up events after down, including outside coordinates. Up rechecks policy.
func (t *Tabs) Drag(s *TabState, d *DragState, p DragPointer, o DragOptions, allow func(DropRequest) bool) *DropRequest {
	if p.Action == "down" {
		d.Cancel()
		if p.X < 0 || p.X >= p.Width || p.Y != 0 || p.Height < 1 {
			return nil
		}
		layout := t.Layout(s, p.Width)
		for _, c := range layout.Cells {
			if p.X >= c.Start && p.X < c.Start+c.Width && !c.Disabled && !dragLocked(o, c.ID) {
				d.begin(c.ID, t.dragRevision(), p)
				d.first = s.First
				d.stateRevision = tabDragStateRevision(s)
				break
			}
		}
		return nil
	}
	if d.Captured() && d.stateRevision != tabDragStateRevision(s) {
		d.Cancel()
		d.Result = "stale"
		return nil
	}
	if !d.prepare(t.dragRevision(), p, o) {
		return nil
	}
	if d.Phase == "dragging" {
		if o.AutoScroll && p.Action == "move" {
			if p.X <= 0 {
				d.first = max(0, d.first-1)
			} else if p.X >= p.Width-1 {
				d.first = min(max(0, len(t.items)-1), d.first+1)
			}
		}
		r := DropRequest{SourceID: d.SourceID, Revision: d.revision}
		err := fmt.Errorf("outside")
		if p.X >= 0 && p.X < p.Width && p.Y == 0 {
			layout := t.DragLayout(s, d, p.Width)
			for _, c := range layout.Cells {
				if p.X >= c.Start && p.X < c.Start+c.Width {
					pos := DropBefore
					if p.X-c.Start >= c.Width/2 {
						pos = DropAfter
					}
					r, err = t.RequestDrop(d.SourceID, c.ID, pos, o, allow)
					break
				}
			}
		}
		d.preview(r, err)
	}
	return d.finish(p)
}

func (t *Tree) RequestDrop(source, target string, pos DropPosition, o DragOptions, allow func(DropRequest) bool) (DropRequest, error) {
	r := DropRequest{source, target, pos, t.dragRevision()}
	if dragLocked(o, source) || dragLocked(o, target) {
		return r, fmt.Errorf("locked")
	}
	_, err := t.ApplyDrop(r)
	if err == nil && allow != nil && !allow(r) {
		err = fmt.Errorf("policy")
	}
	return r, err
}
func (t *Tree) ApplyDrop(r DropRequest) (*Tree, error) {
	if r.Revision != t.dragRevision() {
		return nil, fmt.Errorf("stale")
	}
	si, sok := t.index[r.SourceID]
	ti, tok := t.index[r.TargetID]
	if !sok || !tok {
		return nil, fmt.Errorf("missing")
	}
	if si == ti {
		return nil, fmt.Errorf("self")
	}
	for id := r.TargetID; id != ""; {
		if id == r.SourceID {
			return nil, fmt.Errorf("cycle")
		}
		id = t.rows[t.index[id]].Node.Parent
	}
	if r.Position != DropBefore && r.Position != DropAfter && r.Position != DropInside {
		return nil, fmt.Errorf("position")
	}
	if r.Position == DropInside && !t.rows[ti].Node.Branch {
		return nil, fmt.Errorf("leaf")
	}
	end := si + 1
	for end < len(t.rows) && t.rows[end].Depth > t.rows[si].Depth {
		end++
	}
	all := t.Nodes()
	block := append([]TreeNode(nil), all[si:end]...)
	all = slices.Delete(all, si, end)
	pos := 0
	for all[pos].ID != r.TargetID {
		pos++
	}
	parent := all[pos].Parent
	if r.Position == DropInside {
		parent = all[pos].ID
	}
	if r.Position != DropBefore {
		depth := t.rows[ti].Depth
		pos++
		for pos < len(all) && t.rows[t.index[all[pos].ID]].Depth > depth {
			pos++
		}
	}
	block[0].Parent = parent
	all = slices.Insert(all, pos, block...)
	unchanged := len(all) == len(t.rows)
	if unchanged {
		for i, n := range all {
			if n.ID != t.rows[i].Node.ID || n.Parent != t.rows[i].Node.Parent {
				unchanged = false
				break
			}
		}
	}
	if unchanged {
		return nil, fmt.Errorf("unchanged")
	}
	return NewTree(all)
}
func (t *Tree) KeyboardDrop(s *TreeState, move DragMove, o DragOptions, allow func(DropRequest) bool) (DropRequest, error) {
	i, ok := t.index[s.Selected]
	if !ok {
		return DropRequest{}, fmt.Errorf("missing")
	}
	node := t.rows[i].Node
	if move == DragOutside && node.Parent != "" {
		return t.RequestDrop(node.ID, node.Parent, DropAfter, o, allow)
	}
	var siblings []string
	current := 0
	for _, r := range t.rows {
		if r.Node.Parent == node.Parent {
			if r.Node.ID == node.ID {
				current = len(siblings)
			}
			siblings = append(siblings, r.Node.ID)
		}
	}
	target, pos := current-1, DropBefore
	switch move {
	case DragNext:
		target, pos = current+1, DropAfter
	case DragInside:
		pos = DropInside
	case DragPrevious:
	default:
		return DropRequest{}, fmt.Errorf("position")
	}
	if target < 0 || target >= len(siblings) {
		return DropRequest{}, fmt.Errorf("missing")
	}
	return t.RequestDrop(node.ID, siblings[target], pos, o, allow)
}

// DragRows exposes temporary scroll/expansion without modifying TreeState.
func (t *Tree) DragRows(s *TreeState, d *DragState, height int) ([]TreeRow, int) {
	if !d.Captured() {
		rows := t.Reconcile(s, height)
		return rows, s.Scroll
	}
	if d.revision != t.dragRevision() || height != d.height || d.stateRevision != treeDragStateRevision(s) {
		d.Cancel()
		d.Result = "stale"
		rows := t.Reconcile(s, height)
		return rows, s.Scroll
	}
	preview := *s
	preview.Expanded = d.expanded
	rows := t.Visible(&preview)
	d.scroll = min(max(0, d.scroll), max(0, len(rows)-max(1, height)))
	return rows, d.scroll
}
func (t *Tree) Drag(s *TreeState, d *DragState, p DragPointer, o DragOptions, allow func(DropRequest) bool) *DropRequest {
	if p.Action == "down" {
		d.Cancel()
		if p.X < 0 || p.X >= p.Width || p.Y < 0 || p.Y >= p.Height {
			return nil
		}
		rows := t.Visible(s)
		i := s.Scroll + p.Y
		if i < 0 || i >= len(rows) || dragLocked(o, rows[i].Node.ID) {
			return nil
		}
		d.begin(rows[i].Node.ID, t.dragRevision(), p)
		d.scroll = s.Scroll
		d.stateRevision = treeDragStateRevision(s)
		d.expanded = map[string]bool{}
		for k, v := range s.Expanded {
			d.expanded[k] = v
		}
		return nil
	}
	if d.Captured() && d.stateRevision != treeDragStateRevision(s) {
		d.Cancel()
		d.Result = "stale"
		return nil
	}
	if !d.prepare(t.dragRevision(), p, o) {
		return nil
	}
	if d.Phase == "dragging" {
		rows, scroll := t.DragRows(s, d, p.Height)
		if o.AutoScroll && p.Action == "move" {
			if p.Y <= 0 {
				d.scroll = max(0, scroll-1)
			} else if p.Y >= p.Height-1 {
				d.scroll = min(max(0, len(rows)-max(1, p.Height)), scroll+1)
			}
		}
		r := DropRequest{SourceID: d.SourceID, Revision: d.revision}
		err := fmt.Errorf("outside")
		i := d.scroll + p.Y
		if p.X >= 0 && p.X < p.Width && p.Y >= 0 && p.Y < p.Height && i >= 0 && i < len(rows) {
			target := rows[i]
			pos := DropAfter
			if p.X <= 2+target.Depth*2 {
				pos = DropBefore
			} else if target.Node.Branch && p.X < p.Width-2 {
				pos = DropInside
			}
			r, err = t.RequestDrop(d.SourceID, target.Node.ID, pos, o, allow)
			if err == nil && o.HoverExpand && pos == DropInside {
				d.expanded[target.Node.ID] = true
			}
		}
		d.preview(r, err)
	}
	return d.finish(p)
}
