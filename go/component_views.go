package tuivory

import (
	"fmt"
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
)

func componentPalette(p Palette, roles ...string) (Palette, error) {
	for _, role := range roles {
		if _, ok := p[role]; !ok {
			return nil, fmt.Errorf("component: missing palette role %q", role)
		}
	}
	copy := Palette{}
	for role, pair := range p {
		copy[role] = pair
	}
	return copy, nil
}
func fillComponent(screen tcell.Screen, x, y, w, h int, style tcell.Style) {
	for row := 0; row < h; row++ {
		for col := 0; col < w; col++ {
			screen.SetContent(x+col, y+row, ' ', nil, style)
		}
	}
}

type TabView struct {
	*tview.Box
	tabs    *Tabs
	state   *TabState
	palette Palette
	OnEvent func(TabEvent)
}

func NewTabView(tabs *Tabs, state *TabState, palette Palette) (*TabView, error) {
	if tabs == nil || state == nil {
		return nil, fmt.Errorf("tabs: model and state required")
	}
	v := &TabView{Box: tview.NewBox(), tabs: tabs, state: state}
	if err := v.SetPalette(palette); err != nil {
		return nil, err
	}
	return v, nil
}
func (v *TabView) SetPalette(palette Palette) error {
	p, err := componentPalette(palette, "surface", "body", "header", "hint", "selection", "disabled")
	if err != nil {
		return err
	}
	v.palette = p
	return nil
}
func (v *TabView) SetTabs(tabs *Tabs) error {
	if tabs == nil {
		return fmt.Errorf("tabs: model required")
	}
	v.tabs = tabs
	tabs.Reconcile(v.state)
	return nil
}
func (v *TabView) Draw(screen tcell.Screen) {
	x, y, w, h := v.GetInnerRect()
	fillComponent(screen, x, y, w, h, v.palette["surface"].Style())
	if h == 0 {
		return
	}
	layout := v.tabs.Layout(v.state, w)
	if layout.Previous {
		drawTreeText(screen, x, y, w, 0, "<", v.palette["hint"].Style())
	}
	if layout.Next && w > 0 {
		drawTreeText(screen, x+w-1, y, 1, 0, ">", v.palette["hint"].Style())
	}
	for _, cell := range layout.Cells {
		role := "body"
		if cell.Active {
			role = "header"
		}
		if cell.Disabled {
			role = "disabled"
		}
		st := disabledCue(v.palette, role, v.palette[role].Style())
		if cell.Focused && v.HasFocus() {
			st = v.palette["selection"].Style().Underline(true)
		}
		fillComponent(screen, x+cell.Start, y, cell.Width, 1, st)
		drawTreeText(screen, x+cell.Start, y, cell.Width, 0, cell.Text, st)
	}
}
func (v *TabView) dispatch(action TabAction) {
	e := v.tabs.Handle(v.state, action)
	if e.Kind != "" && v.OnEvent != nil {
		v.OnEvent(e)
	}
}
func (v *TabView) InputHandler() func(*tcell.EventKey, func(tview.Primitive)) {
	return v.WrapInputHandler(func(e *tcell.EventKey, _ func(tview.Primitive)) {
		switch e.Key() {
		case tcell.KeyLeft:
			v.dispatch(TabPrevious)
		case tcell.KeyRight:
			v.dispatch(TabNext)
		case tcell.KeyHome:
			v.dispatch(TabFirst)
		case tcell.KeyEnd:
			v.dispatch(TabLast)
		case tcell.KeyEnter:
			v.dispatch(TabActivate)
		case tcell.KeyDelete:
			v.dispatch(TabClose)
		default:
			if e.Rune() == 'x' {
				v.dispatch(TabClose)
			}
		}
	})
}
func (v *TabView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return v.WrapMouseHandler(func(a tview.MouseAction, e *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		x, y := e.Position()
		left, top, w, h := v.GetInnerRect()
		if x < left || x >= left+w || y != top || h == 0 {
			return false, nil
		}
		if a == tview.MouseScrollUp {
			v.dispatch(TabPrevious)
			return true, nil
		}
		if a == tview.MouseScrollDown {
			v.dispatch(TabNext)
			return true, nil
		}
		if a != tview.MouseLeftClick {
			return false, nil
		}
		event := v.tabs.Click(v.state, x-left, w)
		if event.Kind != "" {
			focus(v)
		}
		if event.Kind != "" && v.OnEvent != nil {
			v.OnEvent(event)
		}
		return true, nil
	})
}

// PanelView wraps a host-owned primitive; no content or event callbacks are replaced.
type PanelView struct {
	*tview.Box
	Child    tview.Primitive
	palette  Palette
	ASCII    bool
	bordered bool
}

func (v *PanelView) SetBorder(show bool) *PanelView {
	v.bordered = show
	v.Box.SetBorder(show)
	return v
}
func (v *PanelView) GetBorder() bool { return v.bordered }

func NewPanelView(child tview.Primitive, palette Palette) (*PanelView, error) {
	if child == nil {
		return nil, fmt.Errorf("panel: child required")
	}
	v := &PanelView{Box: tview.NewBox(), Child: child}
	v.SetBorder(true)
	v.SetBorderPadding(1, 1, 1, 1)
	if err := v.SetPalette(palette); err != nil {
		return nil, err
	}
	return v, nil
}
func (v *PanelView) SetPalette(palette Palette) error {
	p, err := componentPalette(palette, "surface", "body", "hint", "focus.border")
	if err != nil {
		return err
	}
	v.palette = p
	return nil
}
func (v *PanelView) StyleChildren() []tview.Primitive     { return []tview.Primitive{v.Child} }
func (v *PanelView) HasFocus() bool                       { return v.Child.HasFocus() }
func (v *PanelView) Focus(delegate func(tview.Primitive)) { delegate(v.Child) }
func (v *PanelView) Blur()                                { v.Child.Blur() }
func (v *PanelView) AtTabBoundary(previous bool) bool     { return tabBoundary(v.Child, previous) }
func (v *PanelView) Draw(screen tcell.Screen) {
	screen = WideSafeScreen(screen)
	x, y, w, h := v.GetRect()
	fillComponent(screen, x, y, w, h, v.palette["surface"].Style())
	focused := v.HasFocus()
	// A menu uses its current item and open state instead of panel focus decoration.
	if _, menu := v.Child.(*MenuView); menu {
		focused = false
	}
	border := v.palette["hint"].Style()
	if focused {
		border = v.palette["focus.border"].Style().Bold(true)
	}
	if v.GetBorder() && w > 0 && h > 0 {
		tl, tr, bl, br, hz, vt := '┌', '┐', '└', '┘', '─', '│'
		if focused {
			tl, tr, bl, br, hz, vt = '╔', '╗', '╚', '╝', '═', '║'
		}
		if v.ASCII {
			tl, tr, bl, br, hz, vt = '+', '+', '+', '+', '-', '|'
		}
		for col := 0; col < w; col++ {
			screen.SetContent(x+col, y, hz, nil, border)
			if h > 1 {
				screen.SetContent(x+col, y+h-1, hz, nil, border)
			}
		}
		for row := 0; row < h; row++ {
			screen.SetContent(x, y+row, vt, nil, border)
			if w > 1 {
				screen.SetContent(x+w-1, y+row, vt, nil, border)
			}
		}
		screen.SetContent(x, y, tl, nil, border)
		if w > 1 {
			screen.SetContent(x+w-1, y, tr, nil, border)
		}
		if h > 1 {
			screen.SetContent(x, y+h-1, bl, nil, border)
			if w > 1 {
				screen.SetContent(x+w-1, y+h-1, br, nil, border)
			}
		}
		title := v.GetTitle()
		if focused {
			title = "> " + title
		}
		drawTreeText(screen, x+1, y, max(0, w-2), 0, CellText(title, max(0, w-2)), border)
	}
	left, top, cw, ch := v.GetInnerRect()
	v.Child.SetRect(left, top, cw, ch)
	if cw > 0 && ch > 0 {
		v.Child.Draw(screen)
	}
}
func (v *PanelView) InputHandler() func(*tcell.EventKey, func(tview.Primitive)) {
	return v.WrapInputHandler(func(e *tcell.EventKey, focus func(tview.Primitive)) {
		if handler := v.Child.InputHandler(); handler != nil {
			handler(e, focus)
		}
	})
}
func (v *PanelView) PasteHandler() func(string, func(tview.Primitive)) {
	return v.WrapPasteHandler(func(text string, focus func(tview.Primitive)) {
		if handler := v.Child.PasteHandler(); handler != nil {
			handler(text, focus)
		}
	})
}
func (v *PanelView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return v.WrapMouseHandler(func(a tview.MouseAction, e *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		if handler := v.Child.MouseHandler(); handler != nil {
			return handler(a, e, focus)
		}
		return false, nil
	})
}

// SplitView supports columns or rows. Compact mode shows ActiveSecond's pane.
// Hosts route resize keys through ResizeKey when a child owns application focus.
type SplitView struct {
	*tview.Box
	First, Second             tview.Primitive
	Spec                      SplitSpec
	State                     *SplitState
	Rows, ActiveSecond, ASCII bool
	palette                   Palette
	dragging                  bool
}

func NewSplitView(first, second tview.Primitive, state *SplitState, spec SplitSpec, palette Palette) (*SplitView, error) {
	if first == nil || second == nil || state == nil {
		return nil, fmt.Errorf("split: two children and state required")
	}
	v := &SplitView{Box: tview.NewBox(), First: first, Second: second, State: state, Spec: spec}
	if err := v.SetPalette(palette); err != nil {
		return nil, err
	}
	return v, nil
}
func (v *SplitView) SetPalette(palette Palette) error {
	p, e := componentPalette(palette, "surface", "hint", "focus.border")
	if e != nil {
		return e
	}
	v.palette = p
	return nil
}
func (v *SplitView) StyleChildren() []tview.Primitive { return []tview.Primitive{v.First, v.Second} }
func (v *SplitView) HasFocus() bool                   { return v.First.HasFocus() || v.Second.HasFocus() }
func (v *SplitView) Focus(delegate func(tview.Primitive)) {
	if v.ActiveSecond {
		delegate(v.Second)
	} else {
		delegate(v.First)
	}
}
func (v *SplitView) Blur() { v.First.Blur(); v.Second.Blur() }
func (v *SplitView) geometry() (int, int, int, int, SplitLayout) {
	x, y, w, h := v.GetInnerRect()
	total := w
	if v.Rows {
		total = h
	}
	return x, y, w, h, v.Spec.Layout(v.State, total)
}
func (v *SplitView) Draw(screen tcell.Screen) {
	x, y, w, h, l := v.geometry()
	fillComponent(screen, x, y, w, h, v.palette["surface"].Style())
	if l.Compact {
		v.First.SetRect(x, y, 0, 0)
		v.Second.SetRect(x, y, 0, 0)
		child := v.First
		if v.ActiveSecond {
			child = v.Second
		}
		child.SetRect(x, y, w, h)
		child.Draw(screen)
		return
	}
	if v.Rows {
		v.First.SetRect(x, y, w, l.First)
		v.Second.SetRect(x, y+l.First+1, w, l.Second)
	} else {
		v.First.SetRect(x, y, l.First, h)
		v.Second.SetRect(x+l.First+1, y, l.Second, h)
	}
	v.First.Draw(screen)
	v.Second.Draw(screen)
	st := v.palette["hint"].Style()
	if v.dragging {
		st = v.palette["focus.border"].Style().Bold(true)
	}
	symbol := '│'
	if v.Rows {
		symbol = '─'
	}
	if v.ASCII {
		symbol = '|'
		if v.Rows {
			symbol = '-'
		}
	}
	length := h
	if v.Rows {
		length = w
	}
	for i := 0; i < length; i++ {
		cx, cy := x+l.First, y+i
		if v.Rows {
			cx, cy = x+i, y+l.First
		}
		screen.SetContent(cx, cy, symbol, nil, st)
	}
}
func (v *SplitView) ResizeKey(e *tcell.EventKey) bool {
	if e.Modifiers()&tcell.ModCtrl == 0 {
		return false
	}
	delta := 0
	if (!v.Rows && e.Key() == tcell.KeyLeft) || (v.Rows && e.Key() == tcell.KeyUp) {
		delta = -1
	}
	if (!v.Rows && e.Key() == tcell.KeyRight) || (v.Rows && e.Key() == tcell.KeyDown) {
		delta = 1
	}
	if delta == 0 {
		return false
	}
	_, _, w, h, l := v.geometry()
	total := w
	if v.Rows {
		total = h
	}
	v.Spec.Resize(v.State, total, l.First+delta)
	return true
}
func (v *SplitView) InputHandler() func(*tcell.EventKey, func(tview.Primitive)) {
	return v.WrapInputHandler(func(e *tcell.EventKey, focus func(tview.Primitive)) {
		if v.ResizeKey(e) {
			return
		}
		child := v.First
		if v.ActiveSecond {
			child = v.Second
		}
		if handler := child.InputHandler(); handler != nil {
			handler(e, focus)
		}
	})
}
func (v *SplitView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return v.WrapMouseHandler(func(a tview.MouseAction, e *tcell.EventMouse, focus func(tview.Primitive)) (bool, tview.Primitive) {
		x, y, w, h, l := v.geometry()
		mx, my := e.Position()
		inside := mx >= x && mx < x+w && my >= y && my < y+h
		position := mx - x
		total := w
		if v.Rows {
			position = my - y
			total = h
		}
		if v.dragging {
			if a == tview.MouseLeftUp {
				v.Spec.Resize(v.State, total, position)
				v.dragging = false
				return true, nil
			}
			v.Spec.Resize(v.State, total, position)
			return true, v
		}
		if !inside {
			return false, nil
		}
		if !l.Compact && position == l.First && a == tview.MouseLeftDown {
			v.dragging = true
			return true, v
		}
		child := v.First
		if l.Compact {
			if v.ActiveSecond {
				child = v.Second
			}
		} else if position > l.First {
			child = v.Second
			v.ActiveSecond = true
		} else {
			v.ActiveSecond = false
		}
		if handler := child.MouseHandler(); handler != nil {
			return handler(a, e, focus)
		}
		return false, nil
	})
}

type BreadcrumbView struct {
	*tview.Box
	Items      []PathItem
	palette    Palette
	OnNavigate func(string)
}

func NewBreadcrumbView(items []PathItem, palette Palette) (*BreadcrumbView, error) {
	v := &BreadcrumbView{Box: tview.NewBox(), Items: append([]PathItem(nil), items...)}
	if err := v.SetPalette(palette); err != nil {
		return nil, err
	}
	return v, nil
}
func (v *BreadcrumbView) SetPalette(palette Palette) error {
	p, e := componentPalette(palette, "surface", "body", "hint")
	if e != nil {
		return e
	}
	v.palette = p
	return nil
}
func drawLineRuns(screen tcell.Screen, x, y, w, h int, runs []LineRun, palette Palette) {
	fillComponent(screen, x, y, w, h, palette["surface"].Style())
	if h <= 0 {
		return
	}
	for _, run := range runs {
		drawTreeText(screen, x+run.Start, y, max(0, w-run.Start), 0, run.Text, componentStyle(palette, run.Role))
	}
}
func (v *BreadcrumbView) Draw(screen tcell.Screen) {
	x, y, w, h := v.GetInnerRect()
	drawLineRuns(screen, x, y, w, h, Breadcrumbs(v.Items, w), v.palette)
}
func (v *BreadcrumbView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return v.WrapMouseHandler(func(a tview.MouseAction, e *tcell.EventMouse, _ func(tview.Primitive)) (bool, tview.Primitive) {
		x, y := e.Position()
		left, top, w, h := v.GetInnerRect()
		if a != tview.MouseLeftClick || h == 0 || y != top || x < left || x >= left+w {
			return false, nil
		}
		for _, run := range Breadcrumbs(v.Items, w) {
			if run.ID != "" && x-left >= run.Start && x-left < run.Start+run.Width && v.OnNavigate != nil {
				v.OnNavigate(run.ID)
				return true, nil
			}
		}
		return false, nil
	})
}

type StatusView struct {
	*tview.Box
	items   []StatusItem
	palette Palette
	Omitted int
}

func NewStatusView(items []StatusItem, palette Palette) (*StatusView, error) {
	v := &StatusView{Box: tview.NewBox()}
	if err := v.SetPalette(palette); err != nil {
		return nil, err
	}
	if err := v.SetItems(items); err != nil {
		return nil, err
	}
	return v, nil
}
func (v *StatusView) SetPalette(palette Palette) error {
	roles := []string{"surface", "body", "hint"}
	for _, item := range v.items {
		if item.Role != "" {
			roles = append(roles, item.Role)
		}
	}
	p, e := componentPalette(palette, roles...)
	if e != nil {
		return e
	}
	v.palette = p
	return nil
}
func (v *StatusView) SetItems(items []StatusItem) error {
	for _, item := range items {
		if item.Role != "" {
			if _, ok := v.palette[item.Role]; !ok {
				return fmt.Errorf("status: missing role %q", item.Role)
			}
		}
	}
	v.items = append([]StatusItem(nil), items...)
	return nil
}
func (v *StatusView) Draw(screen tcell.Screen) {
	x, y, w, h := v.GetInnerRect()
	layout := StatusLine(v.items, w)
	v.Omitted = layout.Omitted
	drawLineRuns(screen, x, y, w, h, layout.Runs, v.palette)
}
