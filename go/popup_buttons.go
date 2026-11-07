package tuivory

import "github.com/leechis7/tuivory/go/internal/widgets"

// PopupButtonRects wraps button widths with a one-cell gap and centers each row.
// Rectangles are local to the content area and use contiguous row indices.
// Use the same rectangles when drawing and routing mouse events.
func PopupButtonRects(width int, buttonWidths []int) []CellRect {
	positions := widgets.PopupButtonRects(width, buttonWidths)
	if len(positions) == 0 {
		return nil
	}
	result := make([]CellRect, len(positions))
	for i, position := range positions {
		result[i] = CellRect{X: position.X, Y: position.Y, Width: position.Width, Height: 1}
	}
	return result
}
