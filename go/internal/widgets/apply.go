package widgets

import (
	"reflect"

	style "github.com/leechis7/tuivory/go/internal/style"
	"github.com/rivo/tview"
)

// Roles describes host-owned semantic roles. Missing entries use canvas/body.
// Reuse the same bindings when applying a new Styler; there is no global registry.
type Roles struct {
	Surfaces map[*tview.Box]style.Surface
	Text     map[*tview.TextView]style.TextRole
	Tree     map[*tview.TreeNode]style.TextRole
}

// StyleChildren lets host wrappers expose children without importing app types.
type StyleChildren interface{ StyleChildren() []tview.Primitive }

// Apply recolors existing widgets, including hidden Pages and Form children.
// It does not rebuild widgets or change values, selection, focus, or scroll.
// Rich grids, tabs and footer buttons should be reapplied with their specialized
// methods afterward, since the host owns their state.
func (s Styler) Apply(roles Roles, roots ...tview.Primitive) {
	seen := map[tview.Primitive]bool{}
	surfaces := map[*tview.Box]style.Surface{}
	for box, surface := range roles.Surfaces {
		surfaces[box] = surface
	}
	var visit func(tview.Primitive)
	visit = func(p tview.Primitive) {
		if p == nil || (reflect.ValueOf(p).Kind() == reflect.Ptr && reflect.ValueOf(p).IsNil()) || seen[p] {
			return
		}
		seen[p] = true
		box := widgetBox(p)
		surface := surfaces[box]
		switch w := p.(type) {
		case *tview.Flex:
			for i := 0; i < w.GetItemCount(); i++ {
				visit(w.GetItem(i))
			}
		case *tview.Pages:
			for _, name := range w.GetPageNames(false) {
				visit(w.GetPage(name))
			}
		case *tview.Form:
			s.Form(w)
			surface = style.Panel
			for i := 0; i < w.GetFormItemCount(); i++ {
				child := widgetBox(w.GetFormItem(i))
				if _, exists := surfaces[child]; !exists {
					surfaces[child] = style.Panel
				}
			}
			for i := 0; i < w.GetFormItemCount(); i++ {
				visit(w.GetFormItem(i))
			}
			for i := 0; i < w.GetButtonCount(); i++ {
				visit(w.GetButton(i))
			}
		case *Choice:
			s.Choice(w)
			w.SetLabelStyle(s.Styles.TextStyle(surface, style.Body))
		case *tview.DropDown:
			s.DropDown(w)
			w.SetLabelStyle(s.Styles.TextStyle(surface, style.Body))
		case *tview.InputField:
			s.Input(w)
			w.SetLabelStyle(s.Styles.TextStyle(surface, style.Body))
		case *tview.Checkbox:
			s.Checkbox(w)
			surface = style.Panel
		case *tview.TextArea:
			s.Editor(w)
			surface = style.Editor
		case *tview.TextView:
			s.Text(w, surface, roles.Text[w])
		case *tview.List:
			s.List(w)
			surface = style.Panel
		case *tview.TreeView:
			s.Tree(w, roles.Tree)
		case *tview.Table:
			s.TableOn(w, surface)
		case *tview.Button:
			s.Button(w)
		case *tview.Modal:
			s.Modal(w)
			surface = style.Panel
		}
		if box != nil {
			box.SetBackgroundColor(s.Styles.SurfaceColor(surface)).SetTitleColor(s.Styles.SurfaceText(surface))
		}
		if children, ok := p.(StyleChildren); ok {
			for _, child := range children.StyleChildren() {
				visit(child)
			}
		}
	}
	for _, root := range roots {
		visit(root)
	}
	s.RefreshBorders(roots...)
}

func widgetBox(p tview.Primitive) *tview.Box {
	switch w := p.(type) {
	case *tview.Box:
		return w
	case *tview.Flex:
		return w.Box
	case *tview.Pages:
		return w.Box
	case *tview.Form:
		return w.Box
	case *Choice:
		return w.Box
	case *tview.DropDown:
		return w.Box
	case *tview.InputField:
		return w.Box
	case *tview.Checkbox:
		return w.Box
	case *tview.TextArea:
		return w.Box
	case *tview.TextView:
		return w.Box
	case *tview.List:
		return w.Box
	case *tview.TreeView:
		return w.Box
	case *tview.Table:
		return w.Box
	case *tview.Button:
		return w.Box
	case *tview.Modal:
		return w.Box
	}
	return nil
}

// RefreshBorders uses each widget's current focus and actual background.
// Call after focus changes; it does not install or replace host event handlers.
func (s Styler) RefreshBorders(roots ...tview.Primitive) {
	seen := map[tview.Primitive]bool{}
	var visit func(tview.Primitive)
	visit = func(p tview.Primitive) {
		if p == nil || (reflect.ValueOf(p).Kind() == reflect.Ptr && reflect.ValueOf(p).IsNil()) || seen[p] {
			return
		}
		seen[p] = true
		if box := widgetBox(p); box != nil {
			bg := box.GetBackgroundColor()
			box.SetBorderStyle(s.Styles.BorderStyle(p.HasFocus(), bg))
			title := s.Styles.Text
			if bg == s.Styles.Field {
				title = s.Styles.FieldText
			}
			if bg == s.Styles.Editor {
				title = s.Styles.EditorText
			}
			box.SetTitleColor(title)
		}
		switch w := p.(type) {
		case *tview.Flex:
			for i := 0; i < w.GetItemCount(); i++ {
				visit(w.GetItem(i))
			}
		case *tview.Pages:
			for _, name := range w.GetPageNames(false) {
				visit(w.GetPage(name))
			}
		case *tview.Form:
			for i := 0; i < w.GetFormItemCount(); i++ {
				visit(w.GetFormItem(i))
			}
			for i := 0; i < w.GetButtonCount(); i++ {
				visit(w.GetButton(i))
			}
		}
		if children, ok := p.(StyleChildren); ok {
			for _, child := range children.StyleChildren() {
				visit(child)
			}
		}
	}
	for _, root := range roots {
		visit(root)
	}
}
