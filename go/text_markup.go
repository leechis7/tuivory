package tuivory

import (
	"fmt"
	"github.com/rivo/uniseg"
	"strings"
)

// ParseMarkup is an explicit opt-in to [role]text[/] styling. [[ escapes [.
// It returns plain logical text and grapheme spans; ordinary SetText/Layout
// never interprets markup. Unknown/unbalanced tags return an error atomically.
func ParseMarkup(markup string) (string, []SyntaxSpan, error) {
	type change struct {
		at   int
		role string
	}
	changes := []change{{0, "body"}}
	stack := []string{"body"}
	var out strings.Builder
	for at := 0; at < len(markup); {
		if markup[at] == '[' {
			if at+1 < len(markup) && markup[at+1] == '[' {
				out.WriteByte('[')
				at += 2
				continue
			}
			end := strings.IndexByte(markup[at:], ']')
			if end < 0 {
				return "", nil, fmt.Errorf("unclosed markup tag")
			}
			tag := markup[at+1 : at+end]
			if tag == "/" {
				if len(stack) == 1 {
					return "", nil, fmt.Errorf("unbalanced markup close")
				}
				stack = stack[:len(stack)-1]
			} else {
				if !textRoleSupported(tag) {
					return "", nil, fmt.Errorf("unknown markup role")
				}
				stack = append(stack, tag)
			}
			changes = append(changes, change{out.Len(), stack[len(stack)-1]})
			at += end + 1
			continue
		}
		end := strings.IndexByte(markup[at:], '[')
		if end < 0 {
			end = len(markup) - at
		}
		out.WriteString(markup[at : at+end])
		at += end
	}
	if len(stack) != 1 {
		return "", nil, fmt.Errorf("unclosed markup role")
	}
	plain := out.String()
	spans := []SyntaxSpan{}
	g := uniseg.NewGraphemes(plain)
	index, which := 0, 0
	for g.Next() {
		start, _ := g.Positions()
		for which+1 < len(changes) && changes[which+1].at <= start {
			which++
		}
		role := changes[which].role
		if role != "body" {
			if len(spans) > 0 && spans[len(spans)-1].Role == role && spans[len(spans)-1].End == index {
				spans[len(spans)-1].End++
			} else {
				spans = append(spans, SyntaxSpan{Start: index, End: index + 1, Role: role})
			}
		}
		index++
	}
	return plain, spans, nil
}
func (d *TextDocument) SetMarkup(markup string) error {
	plain, spans, e := ParseMarkup(markup)
	if e != nil {
		return e
	}
	d.SetText(plain)
	d.Syntax = spans
	return nil
}
