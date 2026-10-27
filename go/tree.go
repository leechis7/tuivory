package tuivory

import (
	"fmt"
	"strings"
	"unicode"

	"github.com/gdamore/tcell/v2"
	"github.com/rivo/tview"
	"github.com/rivo/uniseg"
)

// TreeNode is application-supplied data. Parents must precede children; IDs are
// unique and stable across replacement. Branch permits unloaded children.
type TreeNode struct {
	ID, Parent, Name, Secondary, Icon, ASCIIIcon string
	Count                                        *uint64
	Branch                                       bool
}

type TreeRow struct {
	Node  TreeNode
	Depth int
}
type Tree struct {
	rows  []TreeRow
	index map[string]int
}

func NewTree(nodes []TreeNode) (*Tree, error) {
	t := &Tree{index: map[string]int{}}
	children := map[string][]TreeNode{}
	seen := map[string]bool{}
	for _, n := range nodes {
		if n.ID == "" || seen[n.ID] || (n.Parent != "" && !seen[n.Parent]) {
			return nil, fmt.Errorf("tree: empty/duplicate ID or parent must precede child: %q", n.ID)
		}
		seen[n.ID] = true
		if n.Count != nil {
			count := *n.Count
			n.Count = &count
		}
		children[n.Parent] = append(children[n.Parent], n)
	}
	var visit func(string, int) error
	visit = func(parent string, depth int) error {
		if depth > 128 && len(children[parent]) > 0 {
			return fmt.Errorf("tree: maximum depth is 128")
		}
		for _, n := range children[parent] {
			n.Branch = n.Branch || len(children[n.ID]) > 0
			t.index[n.ID] = len(t.rows)
			t.rows = append(t.rows, TreeRow{n, depth})
			if err := visit(n.ID, depth+1); err != nil {
				return err
			}
		}
		return nil
	}
	if err := visit("", 0); err != nil {
		return nil, err
	}
	return t, nil
}

// TreeState is owned by the host, independently of palette or input focus.
type TreeState struct {
	Selected           string
	Expanded           map[string]bool
	Scroll, Horizontal int
}
type TreeAction uint8

const (
	TreeUp TreeAction = iota
	TreeDown
	TreeLeft
	TreeRight
	TreeToggle
	TreeActivate
	TreeHome
	TreeEnd
	TreePageUp
	TreePageDown
	TreePanLeft
	TreePanRight
)

// TreeEvent describes an application action; the library never loads data.
// Kind is "select", "expand", "collapse", "activate", or empty for no action.
type TreeEvent struct{ Kind, ID string }

func (t *Tree) Visible(s *TreeState) []TreeRow {
	var out []TreeRow
	hidden := -1
	for _, row := range t.rows {
		if hidden >= 0 && row.Depth > hidden {
			continue
		}
		hidden = -1
		out = append(out, row)
		if row.Node.Branch && !s.Expanded[row.Node.ID] {
			hidden = row.Depth
		}
	}
	return out
}

// Reconcile retains stable IDs after data changes; a hidden selection moves to
// its nearest visible ancestor. Removed selections fall back to the first row.
func (t *Tree) Reconcile(s *TreeState, height int) []TreeRow {
	if s.Expanded == nil {
		s.Expanded = map[string]bool{}
	}
	for id := range s.Expanded {
		if _, ok := t.index[id]; !ok {
			delete(s.Expanded, id)
		}
	}
	rows := t.Visible(s)
	visible := map[string]int{}
	for i, r := range rows {
		visible[r.Node.ID] = i
	}
	for s.Selected != "" {
		if _, ok := visible[s.Selected]; ok {
			break
		}
		i, ok := t.index[s.Selected]
		if !ok {
			s.Selected = ""
			break
		}
		s.Selected = t.rows[i].Node.Parent
	}
	if s.Selected == "" && len(rows) > 0 {
		s.Selected = rows[0].Node.ID
	}
	height = max(1, height)
	s.Scroll = min(max(0, s.Scroll), max(0, len(rows)-height))
	s.Horizontal = min(65535, max(0, s.Horizontal))
	if i, ok := visible[s.Selected]; ok {
		if i < s.Scroll {
			s.Scroll = i
		}
		if i >= s.Scroll+height {
			s.Scroll = i - height + 1
		}
	}
	return rows
}

func (t *Tree) Handle(s *TreeState, action TreeAction, height int) TreeEvent {
	rows := t.Reconcile(s, height)
	if len(rows) == 0 {
		return TreeEvent{}
	}
	i := 0
	for j, row := range rows {
		if row.Node.ID == s.Selected {
			i = j
			break
		}
	}
	node := rows[i].Node
	target := i
	switch action {
	case TreeUp:
		target--
	case TreeDown:
		target++
	case TreeHome:
		target = 0
	case TreeEnd:
		target = len(rows) - 1
	case TreePageUp:
		target -= max(1, height)
	case TreePageDown:
		target += max(1, height)
	case TreePanLeft:
		s.Horizontal = max(0, s.Horizontal-4)
	case TreePanRight:
		s.Horizontal = min(65535, s.Horizontal+4)
	case TreeActivate:
		return TreeEvent{"activate", node.ID}
	case TreeLeft:
		if s.Expanded[node.ID] && node.Branch {
			delete(s.Expanded, node.ID)
			t.Reconcile(s, height)
			return TreeEvent{"collapse", node.ID}
		}
		if node.Parent != "" {
			s.Selected = node.Parent
		}
	case TreeRight, TreeToggle:
		if node.Branch {
			if action == TreeToggle && s.Expanded[node.ID] {
				delete(s.Expanded, node.ID)
				t.Reconcile(s, height)
				return TreeEvent{"collapse", node.ID}
			}
			if !s.Expanded[node.ID] {
				s.Expanded[node.ID] = true
				t.Reconcile(s, height)
				return TreeEvent{"expand", node.ID}
			}
			if i+1 < len(rows) && rows[i+1].Depth > rows[i].Depth {
				target++
			}
		}
	}
	if target != i {
		s.Selected = rows[min(max(target, 0), len(rows)-1)].Node.ID
	}
	t.Reconcile(s, height)
	if s.Selected != node.ID {
		return TreeEvent{"select", s.Selected}
	}
	return TreeEvent{}
}

// Click coordinates are relative to the inner tree viewport.
func (t *Tree) Click(s *TreeState, column, row, height int) TreeEvent {
	rows := t.Reconcile(s, height)
	if row < 0 || row >= height || column < 0 || s.Scroll+row >= len(rows) {
		return TreeEvent{}
	}
	target := rows[s.Scroll+row]
	old := s.Selected
	s.Selected = target.Node.ID
	if column >= 2 && column+s.Horizontal == 2+target.Depth*2 {
		if event := t.Handle(s, TreeToggle, height); event.Kind != "" {
			return event
		}
	}
	if old != s.Selected {
		return TreeEvent{"select", s.Selected}
	}
	return TreeEvent{}
}

// TreeView adapts the shared model to tview, preserving the host's TreeState.
// SetPalette changes styles only. It does not replace input/focus callbacks.
type TreeView struct {
	*tview.Box
	tree    *Tree
	state   *TreeState
	palette Palette
	ASCII   bool
	OnEvent func(TreeEvent)
}

func NewTreeView(tree *Tree, state *TreeState, palette Palette) (*TreeView, error) {
	if tree == nil || state == nil {
		return nil, fmt.Errorf("tree: model and state are required")
	}
	v := &TreeView{Box: tview.NewBox(), tree: tree, state: state}
	if err := v.SetPalette(palette); err != nil {
		return nil, err
	}
	v.SetBorder(true)
	return v, nil
}

func (v *TreeView) SetTree(tree *Tree) error {
	if tree == nil {
		return fmt.Errorf("tree: model is required")
	}
	v.tree = tree
	_, _, _, h := v.GetInnerRect()
	tree.Reconcile(v.state, h)
	return nil
}
func (v *TreeView) SetPalette(palette Palette) error {
	for _, role := range []string{"body", "hint", "surface", "selection", "focus.border"} {
		if _, ok := palette[role]; !ok {
			return fmt.Errorf("tree: missing palette role %s", role)
		}
	}
	v.palette = Palette{}
	for role, pair := range palette {
		v.palette[role] = pair
	}
	return nil
}

func cleanTreeText(text string) string {
	return strings.Map(func(r rune) rune {
		if unicode.IsControl(r) {
			return ' '
		}
		return r
	}, text)
}

// drawTreeText clips complete grapheme clusters to terminal cells, including
// horizontal offsets through wide glyphs. Text is literal, never tview markup.
func drawTreeText(screen tcell.Screen, x, y, width, offset int, text string, st tcell.Style) int {
	graphemes := uniseg.NewGraphemes(cleanTreeText(text))
	column := 0
	for graphemes.Next() {
		w := graphemes.Width()
		if column >= offset && column+w <= offset+width && w > 0 {
			runes := []rune(graphemes.Str())
			screen.SetContent(x+column-offset, y, runes[0], runes[1:], st)
		}
		column += w
	}
	return column
}

func (v *TreeView) Draw(screen tcell.Screen) {
	surface := v.palette["surface"].Style()
	v.SetBackgroundColor(v.palette["surface"].BG).SetTitleColor(v.palette["body"].FG)
	border := v.palette["hint"].Style()
	if v.HasFocus() {
		border = v.palette["focus.border"].Style().Bold(true)
	}
	v.SetBorderStyle(border)
	v.Box.DrawForSubclass(screen, v)
	x, y, w, h := v.GetInnerRect()
	rows := v.tree.Reconcile(v.state, h)
	for line := 0; line < h; line++ {
		st := surface
		index := v.state.Scroll + line
		selected := index < len(rows) && rows[index].Node.ID == v.state.Selected
		if selected {
			st = v.palette["selection"].Style()
			if v.HasFocus() {
				st = st.Underline(true)
			}
		}
		for col := 0; col < w; col++ {
			screen.SetContent(x+col, y+line, ' ', nil, st)
		}
		if index >= len(rows) {
			continue
		}
		row := rows[index]
		n := row.Node
		marker := "  "
		if selected {
			marker = "> "
		}
		drawTreeText(screen, x, y+line, w, 0, marker, st)
		arrow := "·"
		if v.ASCII {
			arrow = "."
		}
		if n.Branch {
			arrow = "▸"
			if v.ASCII {
				arrow = ">"
			}
			if v.state.Expanded[n.ID] {
				arrow = "▾"
				if v.ASCII {
					arrow = "v"
				}
			}
		}
		icon := n.Icon
		if v.ASCII {
			icon = n.ASCIIIcon
		}
		prefix := strings.Repeat(" ", row.Depth*2) + arrow + " "
		if icon != "" {
			prefix += icon + " "
		}
		name := prefix + n.Name
		if n.Count != nil {
			name += fmt.Sprintf(" (%d)", *n.Count)
		}
		column := drawTreeText(screen, x+2, y+line, max(0, w-2), v.state.Horizontal, name, st)
		secondary := v.palette["hint"].Style().Background(v.palette["surface"].BG)
		if selected {
			secondary = st
		}
		drawTreeText(screen, x+2, y+line, max(0, w-2), v.state.Horizontal-column, "  "+n.Secondary, secondary)
	}
}

func (v *TreeView) dispatch(action TreeAction) {
	_, _, _, h := v.GetInnerRect()
	event := v.tree.Handle(v.state, action, h)
	if event.Kind != "" && v.OnEvent != nil {
		v.OnEvent(event)
	}
}
func (v *TreeView) InputHandler() func(*tcell.EventKey, func(tview.Primitive)) {
	return v.WrapInputHandler(func(e *tcell.EventKey, _ func(tview.Primitive)) {
		if e.Modifiers()&tcell.ModAlt != 0 {
			if e.Key() == tcell.KeyLeft {
				v.dispatch(TreePanLeft)
			}
			if e.Key() == tcell.KeyRight {
				v.dispatch(TreePanRight)
			}
			return
		}
		keys := map[tcell.Key]TreeAction{tcell.KeyUp: TreeUp, tcell.KeyDown: TreeDown, tcell.KeyLeft: TreeLeft, tcell.KeyRight: TreeRight, tcell.KeyHome: TreeHome, tcell.KeyEnd: TreeEnd, tcell.KeyPgUp: TreePageUp, tcell.KeyPgDn: TreePageDown, tcell.KeyEnter: TreeActivate}
		if a, ok := keys[e.Key()]; ok {
			v.dispatch(a)
		} else if e.Rune() == ' ' {
			v.dispatch(TreeToggle)
		}
	})
}
func (v *TreeView) MouseHandler() func(tview.MouseAction, *tcell.EventMouse, func(tview.Primitive)) (bool, tview.Primitive) {
	return v.WrapMouseHandler(func(action tview.MouseAction, e *tcell.EventMouse, setFocus func(tview.Primitive)) (bool, tview.Primitive) {
		x, y := e.Position()
		left, top, w, h := v.GetInnerRect()
		if x < left || x >= left+w || y < top || y >= top+h {
			return false, nil
		}
		if action == tview.MouseScrollUp {
			v.dispatch(TreeUp)
			return true, nil
		}
		if action == tview.MouseScrollDown {
			v.dispatch(TreeDown)
			return true, nil
		}
		if action != tview.MouseLeftClick {
			return false, nil
		}
		setFocus(v)
		event := v.tree.Click(v.state, x-left, y-top, h)
		if event.Kind != "" && v.OnEvent != nil {
			v.OnEvent(event)
		}
		return true, nil
	})
}
