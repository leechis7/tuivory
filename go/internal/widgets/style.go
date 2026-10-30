// Package widgets applies LazyOra-derived TUIVORY styles to stock tview widgets.
// It owns no application, focus, data, or terminal lifecycle.
package widgets

import (
	"github.com/gdamore/tcell/v2"
	style "github.com/leechis7/tuivory/go/internal/style"
	"github.com/rivo/tview"
)

// Styler is a value; create a new one and reapply it when switching themes.
type Styler struct{ Styles style.Styles }

func New(theme, profile string) (Styler, error) {
	s, err := style.NewStyles(theme, profile)
	return Styler{Styles: s}, err
}

func (s Styler) Box(box *tview.Box, background, foreground tcell.Color) {
	box.SetBackgroundColor(background).SetBorderColor(s.Styles.Button).SetTitleColor(foreground)
}

func (s Styler) Button(button *tview.Button) {
	button.SetStyle(s.Styles.ButtonStyle()).SetActivatedStyle(s.Styles.ButtonFocusStyle()).SetDisabledStyle(s.Styles.DisabledStyle())
}

func (s Styler) Input(field *tview.InputField) {
	p := s.Styles
	s.Box(field.Box, p.Surface, p.Text)
	field.SetFieldStyle(p.TextStyle(style.Field, style.Body)).SetLabelStyle(tcell.StyleDefault.Foreground(p.Muted).Background(p.Surface)).
		SetPlaceholderStyle(tcell.StyleDefault.Foreground(p.Placeholder).Background(p.Field))
}

func (s Styler) Editor(editor *tview.TextArea) {
	p := s.Styles
	s.Box(editor.Box, p.Editor, p.EditorText)
	editor.SetTextStyle(p.EditorStyle()).SetSelectedStyle(p.SelectionStyle())
}

func (s Styler) List(list *tview.List) {
	p := s.Styles
	s.Box(list.Box, p.Surface, p.Text)
	list.SetMainTextStyle(tcell.StyleDefault.Foreground(p.Text).Background(p.Surface)).
		SetSecondaryTextStyle(tcell.StyleDefault.Foreground(p.Muted).Background(p.Surface)).
		SetShortcutStyle(tcell.StyleDefault.Foreground(p.Accent).Background(p.Surface)).
		SetSelectedStyle(p.SelectionStyle()).SetHighlightFullLine(true)
}

func (s Styler) Checkbox(box *tview.Checkbox) {
	p := s.Styles
	s.Box(box.Box, p.Surface, p.Text)
	box.SetLabelStyle(tcell.StyleDefault.Foreground(p.Text).Background(p.Surface)).
		SetCheckedStyle(p.TextStyle(style.Field, style.Body)).SetUncheckedStyle(p.TextStyle(style.Field, style.Body)).SetActivatedStyle(p.SelectionStyle()).
		SetCheckedString(tview.Escape("[x]")).SetUncheckedString(tview.Escape("[ ]"))
}

// Form owns the form items' DrawFunc hooks to reapply styles after tview's
// per-draw attributes. Apply before installing custom hooks, or use Input etc.
func (s Styler) Form(form *tview.Form) {
	p := s.Styles
	s.Box(form.Box, p.Surface, p.Text)
	form.SetBorderPadding(1, 1, 2, 2)
	form.SetButtonsAlign(tview.AlignCenter)
	form.SetLabelColor(p.Muted).SetFieldStyle(p.TextStyle(style.Field, style.Body)).
		SetButtonStyle(p.ButtonStyle()).SetButtonActivatedStyle(p.ButtonFocusStyle()).SetButtonDisabledStyle(p.DisabledStyle())
	for i := 0; i < form.GetFormItemCount(); i++ {
		switch item := form.GetFormItem(i).(type) {
		case *tview.InputField:
			s.Input(item)
			item.SetDrawFunc(func(_ tcell.Screen, x, y, width, height int) (int, int, int, int) {
				label := tcell.StyleDefault.Foreground(p.Muted).Background(p.Surface)
				input := p.TextStyle(style.Field, style.Body)
				if item.HasFocus() {
					label = label.Foreground(p.Accent).Bold(true)
					input = input.Underline(true)
				}
				item.SetLabelStyle(label).SetFieldStyle(input)
				return x, y, width, height
			})
		case *tview.TextView:
			s.Box(item.Box, p.Surface, p.Text)
			item.SetTextColor(p.Text)
			item.SetDrawFunc(func(_ tcell.Screen, x, y, width, height int) (int, int, int, int) {
				item.SetTextColor(p.Text)
				return x, y, width, height
			})
		case *tview.Checkbox:
			s.Checkbox(item)
		case *Choice:
			s.Choice(item)
		case *tview.DropDown:
			s.DropDown(item)
			item.SetDrawFunc(func(_ tcell.Screen, x, y, width, height int) (int, int, int, int) {
				s.DropDown(item)
				return x, y, width, height
			})
		}
	}
}

func (s Styler) Modal(modal *tview.Modal) {
	p := s.Styles
	s.Box(modal.Box, p.Surface, p.Text)
	modal.SetBackgroundColor(p.Surface).SetTextColor(p.Text).
		SetButtonStyle(p.ButtonStyle()).SetButtonActivatedStyle(p.ButtonFocusStyle())
}

// Table styles a simple data table on the canvas.
//
// Deprecated: Use TableOn(table, tuivory.Canvas), which preserves the same styling.
func (s Styler) Table(table *tview.Table) { s.TableOn(table, style.Canvas) }

func (s Styler) table(table *tview.Table) {
	p := s.Styles
	s.Box(table.Box, p.Background, p.Text)
	table.SetBordersColor(p.Muted).SetSelectedStyle(p.SelectionStyle())
	for row := 0; row < table.GetRowCount(); row++ {
		for col := 0; col < table.GetColumnCount(); col++ {
			cell := table.GetCell(row, col)
			st := tcell.StyleDefault.Foreground(p.Text).Background(p.Background)
			if row == 0 && cell.NotSelectable {
				st = st.Foreground(p.Accent).Underline(true)
			}
			cell.SetStyle(st).SetTransparency(false)
		}
	}
}
