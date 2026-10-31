package tuivory

import "github.com/rivo/tview"

// SurfaceView is an opaque, borderless child container. The assigned rectangle
// is filled before the child is drawn. Hosts still choose placement and actions.
type SurfaceView = PanelView

func NewSurfaceView(child tview.Primitive, palette Palette) (*SurfaceView, error) {
	v, err := NewPanelView(child, palette)
	if err != nil {
		return nil, err
	}
	v.SetBorder(false).SetBorderPadding(0, 0, 0, 0)
	return v, nil
}
