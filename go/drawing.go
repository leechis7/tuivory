package tuivory

import (
	"github.com/gdamore/tcell/v2"
	"github.com/leechis7/tuivory/go/internal/drawing"
)

// WideSafeScreen returns a tcell Screen that repairs overlapping wide glyphs
// before each positioned write. Pass it to the entire popup/card Draw call.
// SetContent, SetCell, Put, PutStr and PutStrStyled use the same repair. Init,
// Show, Sync, input and terminal ownership are forwarded to the host screen.
// An intersected glyph is replaced by spaces, including its cell just outside
// the drawn area, retaining its old style there. Redraw the background on close.
// Draw on the host UI goroutine; cell repairs are not a concurrent transaction.
func WideSafeScreen(screen tcell.Screen) tcell.Screen { return drawing.SafeScreen(screen) }

// DimRegion draws a shadow over a clipped rectangle while preserving complete
// glyphs and clearing wide glyphs crossing either horizontal boundary. Outside
// styles are preserved; the caller draws the card afterwards and owns redraws.
func DimRegion(screen tcell.Screen, rect CellRect) {
	drawing.Dim(screen, rect.X, rect.Y, rect.Width, rect.Height)
}
