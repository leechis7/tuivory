// Package drawing repairs wide-glyph overlap before updating tcell cells.
package drawing

import (
	"github.com/gdamore/tcell/v2"
	"github.com/rivo/uniseg"
)

type cellRead struct {
	x, y  int
	glyph string
	style tcell.Style
	valid bool
}
type safeScreen struct {
	tcell.Screen
	read cellRead
}

// SafeScreen wraps all positioned cell-writing entry points. Hosts must draw
// on their UI goroutine, as with tview; multiple cell updates are not atomic.
func SafeScreen(screen tcell.Screen) tcell.Screen {
	if _, ok := screen.(*safeScreen); ok {
		return screen
	}
	return &safeScreen{Screen: screen}
}

func (s *safeScreen) Get(x, y int) (string, tcell.Style, int) {
	glyph, style, width := s.Screen.Get(x, y)
	s.read = cellRead{x: x, y: y, glyph: glyph, style: style, valid: true}
	return glyph, style, width
}

func (s *safeScreen) GetContent(x, y int) (rune, []rune, tcell.Style, int) {
	main, combining, style, width := s.Screen.GetContent(x, y)
	s.read = cellRead{x: x, y: y, glyph: string(append([]rune{main}, combining...)), style: style, valid: true}
	return main, combining, style, width
}

func (s *safeScreen) Show()  { s.read.valid = false; s.Screen.Show() }
func (s *safeScreen) Sync()  { s.read.valid = false; s.Screen.Sync() }
func (s *safeScreen) Clear() { s.read.valid = false; s.Screen.Clear() }
func (s *safeScreen) Fill(primary rune, style tcell.Style) {
	s.read.valid = false
	s.Screen.Fill(primary, style)
}

func (s *safeScreen) Put(x, y int, text string, style tcell.Style) (string, int) {
	read := s.read
	s.read.valid = false
	cols, rows := s.Size()
	if x < 0 || y < 0 || x >= cols || y >= rows {
		return text, 0
	}
	remaining, glyph, width, state := text, "", 0, -1
	for width == 0 && remaining != "" {
		var part string
		part, remaining, width, state = uniseg.FirstGraphemeClusterInString(remaining, state)
		glyph += part
	}
	if width == 0 {
		return s.Screen.Put(x, y, text, style)
	}
	// Match tcell's output at the last column and leave no hidden wide start.
	if width > cols-x {
		glyph, width = " ", 1
	}
	// Table and other backend widgets read a cell and write its unchanged
	// text back to apply backgrounds/selection. A continuation is logically a
	// space, but restyling it must not erase the wide glyph on its left.
	// Require a matching, still-current read; ordinary replacement writes keep
	// the overlap repair below, including writes of spaces over wide tails.
	if read.valid && read.x == x && read.y == y && read.glyph == glyph {
		current, oldStyle, oldWidth := s.Screen.Get(x, y)
		if current == read.glyph && oldStyle == read.style {
			start, wide, span := x, current, oldWidth
			if x > 0 {
				if left, _, n := s.Screen.Get(x-1, y); n > 1 {
					start, wide, span = x-1, left, n
				}
			}
			if span > 1 {
				s.Screen.Put(start, y, wide, style)
				_, resolved, _ := s.Screen.Get(start, y)
				for n := 1; n < span && start+n < cols; n++ {
					s.Screen.Put(start+n, y, " ", resolved)
				}
				return remaining, width
			}
		}
	}
	// A write can cover the tail on its left, the start on its right, or
	// several old glyphs. Remove each intersecting old glyph in its entirety.
	for col := max(0, x-1); col < min(cols, x+width); col++ {
		_, oldStyle, oldWidth := s.Screen.Get(col, y)
		if oldWidth > 1 {
			for n := 0; n < oldWidth && col+n < cols; n++ {
				s.Screen.Put(col+n, y, " ", oldStyle)
			}
		}
	}
	// Normalize the new continuation cell too: tcell retains stale logical
	// content there, which otherwise reappears when the glyph is overwritten.
	for n := 1; n < width; n++ {
		s.Screen.Put(x+n, y, " ", style)
	}
	s.Screen.Put(x, y, glyph, style)
	return remaining, width
}
func (s *safeScreen) SetContent(x, y int, primary rune, combining []rune, style tcell.Style) {
	s.Put(x, y, string(append([]rune{primary}, combining...)), style)
}
func (s *safeScreen) SetCell(x, y int, style tcell.Style, chars ...rune) {
	if len(chars) == 0 {
		// An explicit erase, rather than read/modify/write of a continuation.
		s.read.valid = false
		s.Put(x, y, " ", style)
		return
	}
	s.Put(x, y, string(chars), style)
}
func (s *safeScreen) PutStrStyled(x, y int, text string, style tcell.Style) {
	for text != "" {
		rest, width := s.Put(x, y, text, style)
		if width == 0 {
			return
		}
		text = rest
		x += width
	}
}
func (s *safeScreen) PutStr(x, y int, text string) { s.PutStrStyled(x, y, text, tcell.StyleDefault) }

// Dim dims a clipped rectangle. Fully contained glyphs survive; glyphs crossing
// either horizontal boundary are replaced by spaces on both sides. Styles
// outside the rectangle are retained. Repaint the background to remove a shadow.
func Dim(screen tcell.Screen, x, y, w, h int) {
	cols, rows := screen.Size()
	if w <= 0 || h <= 0 || x >= cols || y >= rows {
		return
	}
	// Avoid x+w overflow, including off-screen negative origins.
	if x < 0 {
		if x <= -w {
			return
		}
		w += x
		x = 0
	}
	if y < 0 {
		if y <= -h {
			return
		}
		h += y
		y = 0
	}
	w = min(w, cols-x)
	h = min(h, rows-y)
	safe := SafeScreen(screen)
	for row := y; row < y+h; row++ {
		// A clipped left tail must be replaced, rather than preserving the
		// predecessor's wide start and letting Show skip the shadow's first cell.
		if x > 0 {
			_, st, width := screen.Get(x-1, row)
			if width > 1 {
				safe.Put(x-1, row, " ", st)
			}
		}
		for col := x; col < x+w; {
			glyph, style, width := screen.Get(col, row)
			if width > x+w-col {
				glyph = " "
				width = 1
			}
			safe.Put(col, row, glyph, style.Dim(true))
			col += max(1, width)
		}
	}
}
