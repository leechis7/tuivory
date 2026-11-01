package tuivory

import (
	"fmt"
	"github.com/leechis7/tuivory/go/internal/highlight"
	"unicode/utf8"
)

type SyntaxToken = highlight.Token
type SyntaxRequest = highlight.Request
type SyntaxAnalysis = highlight.Analysis
type SyntaxAnalyzer = highlight.Analyzer
type SyntaxAnalyzerFunc = highlight.AnalyzerFunc

// SyntaxRoleStyle returns the shared palette fallback for a semantic token.
// Unknown roles and identifiers use body. This never changes the source text.
func SyntaxRoleStyle(role string) string { return highlight.RoleStyle(role) }

type syntaxBinding struct {
	analyzer SyntaxAnalyzer
	request  SyntaxRequest
	source   string
	err      error
	dirty    bool
}

func (d *TextDocument) applyAnalysis(a SyntaxAnalysis) error {
	if err := a.Validate(d.Buffer.Text()); err != nil {
		return err
	}
	spans := make([]ByteSyntaxSpan, 0, len(a.Tokens))
	for _, t := range a.Tokens {
		spans = append(spans, ByteSyntaxSpan{Start: t.Start, End: t.End, Role: SyntaxRoleStyle(t.Role)})
	}
	return d.SetByteSyntax(spans)
}

// SetSyntaxAnalysis atomically applies a source-tagged result, including results
// computed by a host worker, and switches from automatic to supplied analysis.
func (d *TextDocument) SetSyntaxAnalysis(a SyntaxAnalysis) error {
	if d.Buffer.Secret {
		return fmt.Errorf("syntax analysis is unavailable for secret buffers")
	}
	if err := d.applyAnalysis(a); err != nil {
		return err
	}
	d.syntaxAnalyzer = &syntaxBinding{source: d.Buffer.Text()}
	return nil
}

// SetSyntaxAnalyzer attaches optional analysis without changing editing state.
// Nil detaches analysis. Invalid initial results preserve the prior binding.
func (d *TextDocument) SetSyntaxAnalyzer(analyzer SyntaxAnalyzer, request SyntaxRequest) error {
	if analyzer == nil {
		d.syntaxAnalyzer = nil
		d.Syntax = nil
		return nil
	}
	if d.Buffer.Secret {
		return fmt.Errorf("syntax analysis is unavailable for secret buffers")
	}
	a, err := analyzer.AnalyzeSyntax(d.Buffer.Text(), request)
	if err != nil {
		return err
	}
	if err = d.applyAnalysis(a); err != nil {
		return err
	}
	d.syntaxAnalyzer = &syntaxBinding{analyzer: analyzer, request: request, source: d.Buffer.Text()}
	return nil
}

// RefreshSyntax analyzes changed source only; scrolling/theme changes reuse it.
// Failure clears stale highlighting and remains observable through SyntaxError.
func (d *TextDocument) RefreshSyntax() error {
	if d.Buffer.Secret {
		if d.syntaxAnalyzer != nil {
			d.syntaxAnalyzer.source = ""
			d.syntaxAnalyzer.dirty = true
		}
		d.Syntax = nil
		return nil
	}
	b := d.syntaxAnalyzer
	if b == nil {
		return nil
	}
	source := d.Buffer.Text()
	if b.source == source && !b.dirty {
		return b.err
	}
	if b.analyzer == nil {
		d.Syntax = nil
		b.source = source
		b.dirty = false
		return nil
	}
	a, err := b.analyzer.AnalyzeSyntax(source, b.request)
	if err == nil {
		err = d.applyAnalysis(a)
	}
	b.source, b.err = source, err
	b.dirty = false
	if err != nil {
		d.Syntax = nil
	}
	return err
}
func (d *TextDocument) SyntaxError() error {
	if d.syntaxAnalyzer == nil {
		return nil
	}
	return d.syntaxAnalyzer.err
}

// SelectBytes uses exact original UTF-8/grapheme boundaries and preserves state
// on error. Anchor/cursor direction is retained; raw offsets are not cell widths.
func (b *TextBuffer) SelectBytes(anchor, cursor int) error {
	a, err := GraphemeIndex(b.text, anchor)
	if err != nil {
		return err
	}
	c, err := GraphemeIndex(b.text, cursor)
	if err != nil {
		return err
	}
	b.Select(a, c)
	return nil
}
func (b *TextBuffer) SelectionBytes() (start, end int) {
	lo, hi := b.Selection()
	offset := 0
	for i, g := range clusters(b.text) {
		if i == lo {
			start = offset
		}
		if i == hi {
			return start, offset
		}
		offset += len(g)
	}
	if lo == hi {
		return offset, offset
	}
	return start, offset
}

// ReplaceBytes is a literal programmatic edit with undo/redo. It does not
// normalize newlines, inject tags or clear history like SetText does.
func (b *TextBuffer) ReplaceBytes(start, end int, text string) (TextEvent, error) {
	if !utf8.ValidString(text) {
		return TextEvent{}, fmt.Errorf("replacement must be UTF-8")
	}
	if start > end {
		return TextEvent{}, fmt.Errorf("reversed byte range")
	}
	if _, err := GraphemeIndex(b.text, start); err != nil {
		return TextEvent{}, err
	}
	if _, err := GraphemeIndex(b.text, end); err != nil {
		return TextEvent{}, err
	}
	if !b.State.Visual().Editable {
		return TextEvent{}, nil
	}
	if start == end && text == "" {
		return TextEvent{}, nil
	}
	b.save()
	prefix := b.text[:start] + text
	b.text = prefix + b.text[end:]
	offset, cursor := 0, 0
	for _, g := range clusters(b.text) {
		if offset >= len(prefix) {
			break
		}
		offset += len(g)
		cursor++
	}
	b.Select(cursor, cursor)
	b.State.Edited = true
	return TextEvent{Kind: "change"}, nil
}
