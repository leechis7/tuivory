package tuivory

import (
	"fmt"
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
	"github.com/rivo/uniseg"
)

type ContainerChild struct {
	Item  LayoutItem
	Child tview.Primitive
}
type ContainerView struct {
	*tview.Box
	Options ContainerOptions
	State   ContainerState
	// CycleFocus enables Tab/Backtab within this container; disable it when a
	// child form owns Tab. Hosts can also call FocusID/MoveFocus explicitly.
	CycleFocus       bool
	children         []ContainerChild
	rects            []NamedRect
	palette          Palette
	capture          tview.Primitive
	ScrollX, ScrollY int
}

func NewContainer(options ContainerOptions, children []ContainerChild, palette Palette) (*ContainerView, error) {
	p, e := componentPalette(palette, "surface")
	if e != nil {
		return nil, e
	}
	options.Rows = append([]Track(nil), options.Rows...)
	options.Columns = append([]Track(nil), options.Columns...)
	v := &ContainerView{Box: tview.NewBox(), Options: options, CycleFocus: true, palette: p}
	if e = v.SetChildren(children); e != nil {
		return nil, e
	}
	return v, nil
}
func NewRow(children []ContainerChild, palette Palette) (*ContainerView, error) {
	return NewContainer(ContainerOptions{Kind: "row"}, children, palette)
}
func NewColumn(children []ContainerChild, palette Palette) (*ContainerView, error) {
	return NewContainer(ContainerOptions{Kind: "column"}, children, palette)
}
func NewLayoutGrid(rows, columns []Track, children []ContainerChild, palette Palette) (*ContainerView, error) {
	return NewContainer(ContainerOptions{Kind: "grid", Rows: rows, Columns: columns}, children, palette)
}
func NewLayerStack(children []ContainerChild, palette Palette) (*ContainerView, error) {
	return NewContainer(ContainerOptions{Kind: "layers"}, children, palette)
}
func (v *ContainerView) SetOptions(options ContainerOptions) error {
	if _, e := ComputeContainer(CellRect{Width: 80, Height: 24}, v.items(), options); e != nil {
		return e
	}
	options.Rows = append([]Track(nil), options.Rows...)
	options.Columns = append([]Track(nil), options.Columns...)
	v.Options = options
	return nil
}
func (v *ContainerView) items() []LayoutItem {
	out := make([]LayoutItem, len(v.children))
	for i, c := range v.children {
		out[i] = c.Item
	}
	return out
}
func (v *ContainerView) SetChildren(children []ContainerChild) error {
	items := make([]LayoutItem, len(children))
	for i, c := range children {
		if c.Child == nil {
			return fmt.Errorf("container child required")
		}
		items[i] = c.Item
	}
	if _, e := ComputeContainer(CellRect{Width: 80, Height: 24}, items, v.Options); e != nil {
		return e
	}
	wasFocused := v.HasFocus()
	oldCaptured := v.child(v.State.Captured)
	for _, old := range v.children {
		found := false
		for _, next := range children {
			if next.Child == old.Child {
				found = true
			}
		}
		if !found {
			old.Child.Blur()
		}
	}
	v.children = append([]ContainerChild(nil), children...)
	v.State.Reconcile(items)
	if v.State.Captured == "" || oldCaptured != v.child(v.State.Captured) {
		v.capture = nil
		v.State.Captured = ""
	}
	if wasFocused {
		v.focusCurrent()
	}
	return nil
}
func (v *ContainerView) SetPalette(p Palette) error {
	next, e := componentPalette(p, "surface")
	if e == nil {
		v.palette = next
	}
	return e
}
func (v *ContainerView) StyleChildren() []tview.Primitive {
	out := []tview.Primitive{}
	for _, c := range v.children {
		out = append(out, c.Child)
	}
	return out
}
func (v *ContainerView) child(id string) tview.Primitive {
	for _, c := range v.children {
		if c.Item.ID == id && !c.Item.Hidden {
			return c.Child
		}
	}
	return nil
}
func focusLocal(p tview.Primitive) {
	if p != nil {
		p.Focus(focusLocal)
	}
}
func (v *ContainerView) focusCurrent() {
	for _, c := range v.children {
		if c.Item.ID != v.State.Focused {
			c.Child.Blur()
		}
	}
	focusLocal(v.child(v.State.Focused))
}
func (v *ContainerView) Focus(delegate func(tview.Primitive)) {
	v.Box.Focus(delegate)
	v.State.Reconcile(v.items())
	v.focusCurrent()
}
func (v *ContainerView) Blur() {
	v.Box.Blur()
	for _, c := range v.children {
		c.Child.Blur()
	}
}
func (v *ContainerView) FocusID(id string) bool {
	for _, eligible := range v.State.Eligible(v.items()) {
		if id == eligible {
			v.State.Focused = id
			v.focusCurrent()
			return true
		}
	}
	return false
}
func (v *ContainerView) MoveFocus(previous bool) string {
	v.State.Move(v.items(), previous)
	v.focusCurrent()
	return v.State.Focused
}
func tabBoundary(p tview.Primitive, previous bool) bool {
	if scope, ok := p.(interface{ AtTabBoundary(bool) bool }); ok {
		return scope.AtTabBoundary(previous)
	}
	return true
}
func (v *ContainerView) AtTabBoundary(previous bool) bool {
	ids := v.State.Eligible(v.items())
	if len(ids) == 0 {
		return true
	}
	edge := ids[len(ids)-1]
	if previous {
		edge = ids[0]
	}
	return v.State.Focused == edge && tabBoundary(v.child(edge), previous)
}
func (v *ContainerView) Layout() ([]NamedRect, error) {
	x, y, w, h := v.GetInnerRect()
	width, height := max(w, v.Options.VirtualWidth), max(h, v.Options.VirtualHeight)
	if width > 65535 || height > 65535 || int64(width)*int64(height) > 1000000 {
		return nil, fmt.Errorf("virtual canvas exceeds renderer limits")
	}
	v.ScrollX = max(0, min(v.ScrollX, max(0, width-w)))
	v.ScrollY = max(0, min(v.ScrollY, max(0, height-h)))
	return ComputeContainer(CellRect{X: x - v.ScrollX, Y: y - v.ScrollY, Width: width, Height: height}, v.items(), v.Options)
}
func (v *ContainerView) Draw(screen tcell.Screen) {
	x, y, w, h := v.GetInnerRect()
	viewport := CellRect{X: x, Y: y, Width: w, Height: h}
	fillComponent(WideSafeScreen(screen), x, y, w, h, v.palette["surface"].Style())
	rects, e := v.Layout()
	if e != nil {
		return
	}
	v.rects = rects
	v.State.Reconcile(v.items())
	for _, r := range rects {
		child := v.child(r.ID)
		if child == nil || r.Rect.Width == 0 || r.Rect.Height == 0 {
			continue
		}
		child.SetRect(r.Rect.X, r.Rect.Y, r.Rect.Width, r.Rect.Height)
		child.Draw(&containerScreen{Screen: screen, clip: intersectRect(viewport, r.Rect)})
	}
}
func (v *ContainerView) scopeFocus(p tview.Primitive) { focusLocal(p) }
func (v *ContainerView) InputHandler() func(*tcell.EventKey, func(tview.Primitive)) {
	return v.WrapInputHandler(func(e *tcell.EventKey, _ func(tview.Primitive)) {
		if v.CycleFocus && len(v.State.Eligible(v.items())) > 1 && (e.Key() == tcell.KeyTab || e.Key() == tcell.KeyBacktab) && tabBoundary(v.child(v.State.Focused), e.Key() == tcell.KeyBacktab) {
			v.MoveFocus(e.Key() == tcell.KeyBacktab)
			return
		}
		v.State.Reconcile(v.items())
		if child := v.child(v.State.Focused); child != nil {
			if f := child.InputHandler(); f != nil {
				f(e, v.scopeFocus)
			}
		}
	})
}
func (v *ContainerView) PasteHandler() func(string, func(tview.Primitive)) {
	return v.WrapPasteHandler(func(text string, _ func(tview.Primitive)) {
		v.State.Reconcile(v.items())
		if child := v.child(v.State.Focused); child != nil {
			if f := child.PasteHandler(); f != nil {
				f(text, v.scopeFocus)
			}
		}
	})
}
func (v *ContainerView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return v.WrapMouseHandler(func(a tview.MouseAction, e *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		v.State.Reconcile(v.items())
		if v.State.Captured == "" {
			v.capture = nil
		}
		child := v.capture
		id := v.State.Captured
		x, y := e.Position()
		if child == nil {
			if !v.InRect(x, y) {
				return false, nil
			}
			id = v.State.Hit(v.items(), v.rects, x, y)
			child = v.child(id)
		}
		if child == nil {
			return true, nil
		}
		if a == tview.MouseLeftDown || a == tview.MouseLeftClick {
			focus(v)
			v.FocusID(id)
		}
		if f := child.MouseHandler(); f != nil {
			used, capture := f(a, e, v.scopeFocus)
			v.capture = capture
			if capture != nil {
				v.State.Captured = id
				return used, v
			}
			v.State.Captured = ""
			return used, nil
		}
		return true, nil
	})
}
func intersectRect(a, b CellRect) CellRect {
	x, y := max(a.X, b.X), max(a.Y, b.Y)
	return CellRect{X: x, Y: y, Width: max(0, min(a.X+a.Width, b.X+b.Width)-x), Height: max(0, min(a.Y+a.Height, b.Y+b.Height)-y)}
}

type containerScreen struct {
	tcell.Screen
	clip CellRect
}

func (s *containerScreen) SetContent(x, y int, r rune, comb []rune, style tcell.Style) {
	if x < s.clip.X || y < s.clip.Y || x >= s.clip.X+s.clip.Width || y >= s.clip.Y+s.clip.Height {
		return
	}
	if uniseg.StringWidth(string(r)+string(comb)) > 1 && x+1 >= s.clip.X+s.clip.Width {
		r = ' '
		comb = nil
	}
	WideSafeScreen(s.Screen).SetContent(x, y, r, comb, style)
}
func (s *containerScreen) Fill(r rune, style tcell.Style) {
	for y := s.clip.Y; y < s.clip.Y+s.clip.Height; y++ {
		for x := s.clip.X; x < s.clip.X+s.clip.Width; x++ {
			s.SetContent(x, y, r, nil, style)
		}
	}
}
func (s *containerScreen) Clear() { s.Fill(' ', tcell.StyleDefault) }
