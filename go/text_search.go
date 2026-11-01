package tuivory

import "fmt"

// TextRange uses original grapheme indices, not UTF-8 bytes or display cells.
type TextRange struct{ Start, End int }

// SetSearchMatches applies host search results without changing syntax/editing.
// They expire when source changes. Priority: disabled > selection > search > syntax.
func (d *TextDocument) SetSearchMatches(matches []TextRange) error {
	n := len(clusters(d.Buffer.Text()))
	for _, m := range matches {
		if m.Start < 0 || m.End < m.Start || m.End > n {
			return fmt.Errorf("invalid search grapheme range")
		}
	}
	d.searchMatches = append([]TextRange(nil), matches...)
	d.searchSource = d.Buffer.Text()
	return nil
}
