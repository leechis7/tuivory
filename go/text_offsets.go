package tuivory

import "fmt"

// GraphemeIndex converts an exact UTF-8 byte boundary to a grapheme index.
// Offsets inside a combining sequence or wide/emoji cluster are rejected.
func GraphemeIndex(text string, byteOffset int) (int, error) {
	if byteOffset < 0 || byteOffset > len(text) {
		return 0, fmt.Errorf("byte offset outside text")
	}
	offset := 0
	graphemes := clusters(text)
	for index, g := range graphemes {
		if offset == byteOffset {
			return index, nil
		}
		offset += len(g)
	}
	if offset == byteOffset {
		return len(graphemes), nil
	}
	return 0, fmt.Errorf("byte offset splits a grapheme")
}

// ByteSyntaxSpan is a host lexer range in original UTF-8 bytes, [Start,End).
type ByteSyntaxSpan struct {
	Start, End int
	Role       string
}

// SetByteSyntax adapts host lexer ranges without copying a backend editor fork.
// Invalid ranges/roles leave the previous syntax configuration unchanged.
func (d *TextDocument) SetByteSyntax(spans []ByteSyntaxSpan) error {
	converted := make([]SyntaxSpan, 0, len(spans))
	boundaries := map[int]int{0: 0}
	offset := 0
	for i, g := range clusters(d.Buffer.Text()) {
		offset += len(g)
		boundaries[offset] = i + 1
	}
	for _, s := range spans {
		start, ok := boundaries[s.Start]
		if !ok {
			return fmt.Errorf("invalid start byte boundary")
		}
		end, ok := boundaries[s.End]
		if !ok {
			return fmt.Errorf("invalid end byte boundary")
		}
		converted = append(converted, SyntaxSpan{Start: start, End: end, Role: s.Role})
	}
	return d.SetSyntax(converted)
}
