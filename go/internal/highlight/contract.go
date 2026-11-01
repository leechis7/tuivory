// Package highlight defines source-language-independent highlighting values.
package highlight

import (
	"fmt"
	"unicode/utf8"
)

// Token is a half-open range in original UTF-8 bytes, never display cells.
type Token struct {
	Start int    `json:"start"`
	End   int    `json:"end"`
	Role  string `json:"role"`
}
type Request struct {
	Language string `json:"language"`
	Dialect  string `json:"dialect"`
}

// Analysis retains the exact source so stale results cannot style another edit.
type Analysis struct {
	Source   string  `json:"source"`
	Language string  `json:"language"`
	Dialect  string  `json:"dialect"`
	Tokens   []Token `json:"tokens"`
}
type Analyzer interface {
	AnalyzeSyntax(string, Request) (Analysis, error)
}
type AnalyzerFunc func(string, Request) (Analysis, error)

func (f AnalyzerFunc) AnalyzeSyntax(text string, r Request) (Analysis, error) { return f(text, r) }

// RoleStyle is the explicit fallback into the existing shared palette. It does
// not create a language-specific palette. Hosts may override these role choices.
func RoleStyle(role string) string {
	switch role {
	case "keyword", "function", "type", "string", "number", "comment", "parameter":
		return "syntax." + role
	case "macro", "attribute":
		return "syntax.function"
	case "character":
		return "syntax.string"
	case "constant":
		return "syntax.number"
	case "directive":
		return "syntax.comment"
	case "lifetime":
		return "syntax.parameter"
	default:
		return "body"
	}
}
func (a Analysis) Validate(text string) error {
	if !utf8.ValidString(text) {
		return fmt.Errorf("syntax source must be UTF-8")
	}
	if a.Source != text {
		return fmt.Errorf("stale syntax source")
	}
	end := 0
	for _, t := range a.Tokens {
		if t.Start < end || t.End <= t.Start || t.End > len(text) {
			return fmt.Errorf("unordered, overlapping or invalid syntax byte range")
		}
		end = t.End
		if !utf8.RuneStart(text[t.Start]) || t.End < len(text) && !utf8.RuneStart(text[t.End]) {
			return fmt.Errorf("syntax range splits UTF-8")
		}
	}
	return nil
}
