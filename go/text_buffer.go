package tuivory

import (
	"encoding/json"
	"fmt"
	"github.com/rivo/uniseg"
	"strings"
	"unicode"
)

// TextEvent carries requests only. Text is populated only for non-secret copy/cut.
type TextEvent struct{ Kind, Text string }
type textSnapshot struct {
	text           string
	cursor, anchor int
}

func textBreak(s string) bool { return s == "\n" || s == "\r\n" || s == "\r" }

// TextBuffer uses extended grapheme indices, including newlines, for selection.
// Text is retrieved explicitly. Secret buffers never expose copy requests or
// plaintext through formatting/JSON. History retains at most 128 edits in memory.
type TextBuffer struct {
	text               string
	Cursor, Anchor     int
	State              ControlState
	Secret, SingleLine bool
	undo, redo         []textSnapshot
}

func NewTextBuffer(text string) *TextBuffer { b := &TextBuffer{}; b.SetText(text); return b }
func (b *TextBuffer) Text() string          { return b.text }
func (b *TextBuffer) display() string {
	if b.Secret {
		return strings.Repeat("*", len(clusters(b.text)))
	}
	return b.text
}
func (b *TextBuffer) String() string             { return b.display() }
func (b *TextBuffer) Format(s fmt.State, _ rune) { _, _ = fmt.Fprint(s, b.display()) }
func (b *TextBuffer) MarshalJSON() ([]byte, error) {
	return json.Marshal(struct {
		Text           string
		Cursor, Anchor int
	}{b.display(), b.Cursor, b.Anchor})
}
func (b *TextBuffer) SetText(text string) {
	b.text = text
	b.Cursor = len(clusters(b.text))
	b.Anchor = b.Cursor
	b.undo = nil
	b.redo = nil
}
func (b *TextBuffer) clean(text string) string {
	text = strings.ReplaceAll(strings.ReplaceAll(text, "\r\n", "\n"), "\r", "\n")
	return strings.Map(func(r rune) rune {
		if unicode.IsControl(r) && !(r == '\n' && !b.SingleLine) && r != '\t' {
			return -1
		}
		if r == '\t' {
			return ' '
		}
		return r
	}, text)
}
func (b *TextBuffer) Select(anchor, cursor int) {
	n := len(clusters(b.text))
	b.Anchor = max(0, min(n, anchor))
	b.Cursor = max(0, min(n, cursor))
}
func (b *TextBuffer) Selection() (int, int) {
	b.Select(b.Anchor, b.Cursor)
	return min(b.Anchor, b.Cursor), max(b.Anchor, b.Cursor)
}
func (b *TextBuffer) CursorByte() int {
	g := clusters(b.text)
	b.Select(b.Anchor, b.Cursor)
	return len(strings.Join(g[:b.Cursor], ""))
}
func (b *TextBuffer) snapshot() textSnapshot { return textSnapshot{b.text, b.Cursor, b.Anchor} }
func (b *TextBuffer) restore(s textSnapshot) {
	b.text = s.text
	b.Cursor = s.cursor
	b.Anchor = s.anchor
}
func (b *TextBuffer) save() {
	b.undo = append(b.undo, b.snapshot())
	if len(b.undo) > 128 {
		b.undo = b.undo[1:]
	}
	b.redo = nil
}
func (b *TextBuffer) lineBounds(g []string, at int) (int, int) {
	start, end := at, at
	for start > 0 && !textBreak(g[start-1]) {
		start--
	}
	for end < len(g) && !textBreak(g[end]) {
		end++
	}
	return start, end
}
func (b *TextBuffer) Handle(action, text string) TextEvent {
	if b.State.Disabled {
		return TextEvent{}
	}
	g := clusters(b.text)
	b.Select(b.Anchor, b.Cursor)
	lo, hi := b.Selection()
	at := b.Cursor
	selectMove := strings.HasPrefix(action, "select_")
	move := strings.TrimPrefix(action, "select_")
	target := at
	start, end := b.lineBounds(g, at)
	switch move {
	case "left":
		target = max(0, at-1)
		if !selectMove && lo != hi {
			target = lo
		}
	case "right":
		target = min(len(g), at+1)
		if !selectMove && lo != hi {
			target = hi
		}
	case "home":
		target = start
	case "end":
		target = end
	case "up":
		if start > 0 {
			previous, _ := b.lineBounds(g, start-1)
			target = min(start-1, previous+at-start)
		}
	case "down":
		if end < len(g) {
			_, nextEnd := b.lineBounds(g, end+1)
			target = min(nextEnd, end+1+at-start)
		}
	case "all":
		if selectMove {
			b.Select(0, len(g))
			return TextEvent{Kind: "select"}
		}
	default:
		target = -1
	}
	if target >= 0 {
		b.Cursor = target
		if !selectMove {
			b.Anchor = target
		}
		return TextEvent{Kind: "select"}
	}
	if action == "copy" || action == "cut" {
		if b.Secret || lo == hi || action == "cut" && !b.State.Visual().Editable {
			return TextEvent{}
		}
		value := strings.Join(g[lo:hi], "")
		if action == "copy" {
			return TextEvent{Kind: "copy", Text: value}
		}
		b.save()
		b.text = strings.Join(append(g[:lo], g[hi:]...), "")
		b.Select(lo, lo)
		b.State.Edited = true
		return TextEvent{Kind: "cut", Text: value}
	}
	if !b.State.Visual().Editable {
		return TextEvent{}
	}
	if action == "undo" || action == "redo" {
		from, to := &b.undo, &b.redo
		if action == "redo" {
			from, to = &b.redo, &b.undo
		}
		if len(*from) == 0 {
			return TextEvent{}
		}
		*to = append(*to, b.snapshot())
		s := (*from)[len(*from)-1]
		*from = (*from)[:len(*from)-1]
		b.restore(s)
		b.State.Edited = true
		return TextEvent{Kind: "change"}
	}
	switch action {
	case "backspace":
		if lo == hi && lo > 0 {
			lo--
		}
	case "delete":
		if lo == hi && hi < len(g) {
			hi++
		}
	case "newline":
		text = "\n"
	case "insert", "paste":
	default:
		return TextEvent{}
	}
	if action == "backspace" || action == "delete" {
		text = ""
	} else {
		text = b.clean(text)
	}
	if lo == hi && text == "" {
		return TextEvent{}
	}
	b.save()
	prefix := strings.Join(g[:lo], "") + text
	newText := prefix + strings.Join(g[hi:], "")
	b.text = newText
	// Insertion may merge combining marks with the neighboring grapheme.
	offset := 0
	cursor := 0
	for _, cluster := range clusters(newText) {
		if offset >= len(prefix) {
			break
		}
		offset += len(cluster)
		cursor++
	}
	b.Select(cursor, cursor)
	b.State.Edited = true
	return TextEvent{Kind: "change"}
}

// SyntaxSpan offsets are grapheme indices in the original text, never bytes.
type SyntaxSpan struct {
	Start, End int
	Role       string
}

func textRoleSupported(role string) bool {
	switch role {
	case "body", "hint", "info", "success", "warning", "error", "header", "field", "selection", "button", "disabled", "edited":
		return true
	}
	return false
}
func (d *TextDocument) SetSyntax(spans []SyntaxSpan) error {
	n := len(clusters(d.Buffer.Text()))
	for _, s := range spans {
		if s.Start < 0 || s.End < s.Start || s.End > n || !textRoleSupported(s.Role) {
			return fmt.Errorf("invalid syntax span")
		}
	}
	d.Syntax = append([]SyntaxSpan(nil), spans...)
	return nil
}

type TextDocument struct {
	Buffer                   *TextBuffer
	Wrap, LineNumbers, ASCII bool
	ScrollX, ScrollY         int
	Syntax                   []SyntaxSpan
	hits                     [][]textHit
	reveal                   bool
	viewHeight               int
}
type textHit struct{ x, index int }

func (d *TextDocument) SetText(text string) {
	d.Buffer.SetText(text)
	d.Syntax = nil
	d.ScrollX = 0
	d.ScrollY = 0
	d.reveal = !d.Buffer.State.ReadOnly
}
func (d *TextDocument) RevealCursor() { d.reveal = true }

func NewEditor(text string) *TextDocument {
	return &TextDocument{Buffer: NewTextBuffer(text), LineNumbers: true, reveal: true}
}
func NewTextView(text string) *TextDocument {
	d := NewEditor(text)
	d.Buffer.State.ReadOnly = true
	d.LineNumbers = false
	d.reveal = false
	return d
}

// Handle adds viewport scrolling; copy/cut are host clipboard requests.
func (d *TextDocument) Handle(action, text string) TextEvent {
	if d.Buffer.State.Disabled {
		return TextEvent{}
	}
	switch action {
	case "page_up":
		d.ScrollY = max(0, d.ScrollY-max(1, d.viewHeight))
		return TextEvent{}
	case "page_down":
		d.ScrollY = popupAdd(d.ScrollY, max(1, d.viewHeight))
		return TextEvent{}
	case "scroll_up":
		d.ScrollY = max(0, d.ScrollY-1)
		return TextEvent{}
	case "scroll_down":
		d.ScrollY++
		return TextEvent{}
	case "scroll_left":
		d.ScrollX = max(0, d.ScrollX-4)
		return TextEvent{}
	case "scroll_right":
		d.ScrollX += 4
		return TextEvent{}
	}
	e := d.Buffer.Handle(action, text)
	if e.Kind == "select" || e.Kind == "change" || e.Kind == "cut" {
		d.reveal = true
	}
	return e
}

// Layout renders literal text; markup is not inferred. Call SetText to replace
// data and provide syntax roles separately. No lexer, clipboard or file I/O.
func (d *TextDocument) Layout(width, height int) []ComponentLine {
	d.viewHeight = max(0, height)
	d.Buffer.Select(d.Buffer.Anchor, d.Buffer.Cursor)
	if width <= 0 || height <= 0 {
		d.hits = nil
		return nil
	}
	g := clusters(d.Buffer.display())
	if d.reveal && !d.Wrap {
		start := min(d.Buffer.Cursor, len(g))
		for start > 0 && !textBreak(g[start-1]) {
			start--
		}
		col := uniseg.StringWidth(strings.Join(g[start:min(d.Buffer.Cursor, len(g))], ""))
		available := width
		if d.LineNumbers {
			available -= len(fmt.Sprint(strings.Count(strings.Join(g[:start], ""), "\n")+1)) + 1
		}
		available = max(1, available)
		if col < d.ScrollX {
			d.ScrollX = col
		}
		if col >= d.ScrollX+available {
			d.ScrollX = col - available + 1
		}
	}
	lo, hi := d.Buffer.Selection()
	rows := []ComponentLine{}
	row := ComponentLine{Role: "body"}
	col, line := 0, 1
	prefix := 0
	allHits := [][]textHit{}
	hits := []textHit{}
	begin := func(index int) {
		row = ComponentLine{Role: "body"}
		col = 0
		prefix = 0
		if d.LineNumbers {
			label := fmt.Sprintf("%d ", line)
			row.Text = CellText(label, width)
			prefix = len(label)
			col = prefix
		}
		hits = []textHit{{prefix, index}}
	}
	flush := func(index int) {
		x := col
		if !d.Wrap {
			x -= max(0, d.ScrollX)
		}
		if x >= prefix && x < width {
			hits = append(hits, textHit{x, index})
			if index == d.Buffer.Cursor && !d.Buffer.State.ReadOnly {
				row.Spans = append(row.Spans, ComponentSpan{Start: x, Width: 1, Text: " ", Role: "body", Focused: true})
			}
		}
		rows = append(rows, row)
		// All logical positions are retained for cursor reveal and pointer routing.
		allHits = append(allHits, hits)
	}
	begin(0)
	for index, cluster := range g {
		if textBreak(cluster) {
			flush(index)
			line++
			begin(index + 1)
			continue
		}
		w := uniseg.StringWidth(cluster)
		if strings.IndexFunc(cluster, unicode.IsControl) >= 0 {
			cluster = " "
			w = 1
		}
		if d.Wrap && col+w > width && col > prefix {
			flush(index)
			begin(index)
		}
		x := col
		if !d.Wrap {
			x -= max(0, d.ScrollX)
		}
		hits = append(hits, textHit{x, index})
		if x >= prefix && x+w <= width {
			if x > uniseg.StringWidth(row.Text) {
				row.Text += strings.Repeat(" ", x-uniseg.StringWidth(row.Text))
			}
			row.Text += cluster
			role := "body"
			for _, span := range d.Syntax {
				if index >= span.Start && index < span.End && textRoleSupported(span.Role) {
					role = span.Role
				}
			}
			if index >= lo && index < hi {
				role = "selection"
			}
			if d.Buffer.State.Disabled {
				role = "disabled"
			}
			if role != "body" || index == d.Buffer.Cursor && !d.Buffer.State.ReadOnly {
				row.Spans = append(row.Spans, ComponentSpan{Start: x, Width: w, Text: cluster, Role: role, Focused: index == d.Buffer.Cursor})
			}
		}
		col += w
	}
	flush(len(g))
	if d.reveal {
		for row, hits := range allHits {
			for _, hit := range hits {
				if hit.index == d.Buffer.Cursor {
					if row < d.ScrollY {
						d.ScrollY = row
					}
					if row >= d.ScrollY+height {
						d.ScrollY = row - height + 1
					}
				}
			}
		}
		d.reveal = false
	}
	d.ScrollY = max(0, min(d.ScrollY, max(0, len(rows)-height)))
	end := min(len(rows), d.ScrollY+height)
	d.hits = allHits[d.ScrollY:end]
	return rows[d.ScrollY:end]
}

// Point hit-tests a cell coordinate relative to the content viewport. Extend
// keeps the selection anchor for a captured drag, even outside the viewport.
func (d *TextDocument) Point(x, y, width, height int, extend bool) {
	d.Layout(width, height)
	if len(d.hits) == 0 || d.Buffer.State.Disabled {
		return
	}
	y = max(0, min(y, len(d.hits)-1))
	hits := d.hits[y]
	if len(hits) == 0 {
		return
	}
	at := hits[0].index
	for _, hit := range hits {
		if hit.x <= x {
			at = hit.index
		}
	}
	anchor := at
	if extend {
		anchor = d.Buffer.Anchor
	}
	d.Buffer.Select(anchor, at)
}
