package widgets

import (
	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go/internal/drawing"
	style "github.com/leechis7/tuivory/go/internal/style"
	"github.com/rivo/tview"
)

func (s Styler) Text(view *tview.TextView, surface style.Surface, role style.TextRole) {
	p := s.Styles
	s.Box(view.Box, p.SurfaceColor(surface), p.SurfaceText(surface))
	view.SetTextStyle(p.TextStyle(surface, role))
}

func (s Styler) DropDown(field *tview.DropDown) {
	p := s.Styles
	s.Box(field.Box, p.Surface, p.Text)
	field.SetLabelStyle(p.TextStyle(style.Panel, style.Body))
	normal := p.DropDownStyle()
	field.SetFieldStyle(normal).SetFocusedStyle(p.SelectionStyle().Underline(true)).
		SetListStyles(normal, p.SelectionStyle()).SetPrefixStyle(normal)
}

// Choice preserves its own colors when a Form reapplies shared input attributes.
// Its open list uses the shared repair for both edges of overlapping wide glyphs.
type Choice struct {
	*tview.DropDown
	foreground, background tcell.Color
}

func NewChoice(label string, options []string, selected int, changed func(string, int)) *Choice {
	return &Choice{DropDown: tview.NewDropDown().SetLabel(label).SetOptions(options, changed).
		SetCurrentOption(selected).SetFieldWidth(40).SetTextOptions("", "", " ", " ▾", " ▾")}
}

func (s Styler) Choice(field *Choice) {
	s.DropDown(field.DropDown)
	field.foreground, field.background, _ = s.Styles.DropDownStyle().Decompose()
}

func (c *Choice) SetFormAttributes(width int, label, background, _, _ tcell.Color) tview.FormItem {
	c.DropDown.SetFormAttributes(width, label, background, c.foreground, c.background)
	return c
}

func (c *Choice) Draw(screen tcell.Screen) {
	if c.IsOpen() {
		c.DropDown.Draw(drawing.SafeScreen(screen))
		return
	}
	c.DropDown.Draw(screen)
}

// Tree reads semantic node roles from the host; labels never determine a role.
func (s Styler) Tree(tree *tview.TreeView, roles map[*tview.TreeNode]style.TextRole) {
	p := s.Styles
	s.Box(tree.Box, p.Background, p.Text)
	tree.SetGraphicsColor(p.Muted)
	if root := tree.GetRoot(); root != nil {
		root.Walk(func(node, parent *tview.TreeNode) bool {
			node.SetTextStyle(p.TextStyle(style.Canvas, roles[node])).SetSelectedTextStyle(p.SelectionStyle())
			return true
		})
	}
}

func (s Styler) Tab(button *tview.Button, active bool) {
	s.Button(button)
	button.SetStyle(s.Styles.TabStyle(active))
}

func (s Styler) FooterButton(button *tview.Button) {
	s.Button(button)
	button.SetStyle(s.Styles.TextStyle(style.Footer, style.Body))
}

func (s Styler) TableOn(table *tview.Table, surface style.Surface) {
	s.table(table)
	p := s.Styles
	s.Box(table.Box, p.SurfaceColor(surface), p.SurfaceText(surface))
	for row := 0; row < table.GetRowCount(); row++ {
		for col := 0; col < table.GetColumnCount(); col++ {
			cell := table.GetCell(row, col)
			st := p.TextStyle(surface, style.Body)
			if row == 0 && cell.NotSelectable {
				st = st.Foreground(p.Accent).Underline(true)
			}
			cell.SetStyle(st).SetTransparency(false)
		}
	}
}

// Grid styles data only; hit testing, gutter geometry and app data stay in the host.
// state is called for body cells and must be safe for the displayed coordinates.
func (s Styler) Grid(table *tview.Table, state func(row, col int) style.CellState) {
	p := s.Styles
	selectedRow, selectedCol := table.GetSelection()
	edited := false
	if selectedRow > 0 && selectedRow < table.GetRowCount() && selectedCol >= 0 && selectedCol < table.GetColumnCount() && state != nil {
		edited = state(selectedRow, selectedCol).Edited
	}
	s.Box(table.Box, p.GridColors().Background, p.Text)
	table.SetBordersColor(p.GridDividerColor()).SetSelectedStyle(p.GridActiveStyle(table.HasFocus(), edited))
	for row := 0; row < table.GetRowCount(); row++ {
		for col := 0; col < table.GetColumnCount(); col++ {
			st := p.GridHeaderStyle(col == selectedCol)
			if row > 0 {
				cellState := style.CellState{Row: row, CurrentRow: row == selectedRow}
				if state != nil {
					cellState = state(row, col)
					cellState.Row = row
					cellState.CurrentRow = row == selectedRow
				}
				st = p.GridCellStyle(cellState)
			}
			table.GetCell(row, col).SetStyle(st).SetTransparency(false)
		}
	}
}

// Comparison styles a header/current-column/section table, such as the original
// keymap comparison. Column 0 is the label column. Section rows are host-defined.
func (s Styler) Comparison(table *tview.Table, currentColumn int, section func(row int) bool) {
	p := s.Styles
	s.Box(table.Box, p.Surface, p.Text)
	table.SetBordersColor(p.Muted).SetSelectedStyle(p.SelectionStyle())
	for row := 0; row < table.GetRowCount(); row++ {
		for col := 0; col < table.GetColumnCount(); col++ {
			st := p.TextStyle(style.Panel, style.Body)
			if row == 0 {
				st = p.ComparisonHeaderStyle(col > 0 && col == currentColumn)
			} else if section != nil && section(row) {
				st = p.GridHeaderStyle(false)
			}
			table.GetCell(row, col).SetStyle(st).SetTransparency(false)
		}
	}
}
